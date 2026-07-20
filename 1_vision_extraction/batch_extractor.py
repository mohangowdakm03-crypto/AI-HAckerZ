"""
Batch LLM Extractor for GraphRAG
Processes multiple text/pdf files from inputs/ folder and combines extracted
entities and relationships into a unified master graph data contract.

Features added:
- PDF ingestion via PyMuPDF (preferred) or PyPDF2 (fallback)
- Text chunking to keep pieces within LLM context window
- Iterative chunk processing and aggregation
- Deduplication of entities and relationship filtering
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Tuple
import ollama

# PDF handling: prefer PyMuPDF (fitz) for robust extraction, fall back to PyPDF2 if available
try:
    import fitz  # PyMuPDF
    _PDF_ENGINE = "pymupdf"
except Exception:
    try:
        import PyPDF2
        _PDF_ENGINE = "pypdf2"
    except Exception:
        _PDF_ENGINE = None


class BatchExtractor:
    """
    Handles batch extraction of entities and relationships from multiple files
    (text + pdf) using Ollama + Llama 3.2 with strict JSON schema compliance.
    """

    ALLOWED_ENTITY_TYPES = {"EQUIPMENT", "SENSOR", "PROCEDURE", "HAZARD", "COMPLIANCE_STANDARD"}

    def __init__(self, inputs_dir: str = "../data/raw_documents", output_dir: str = "../data"):
        self.inputs_dir = inputs_dir
        self.output_dir = output_dir
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        return """You are an elite industrial AI data extractor. 
Your sole purpose is to convert unstructured industrial text into a precise, structured JSON graph database contract.

You MUST output strictly in valid JSON format.
You MUST adhere to this exact schema:

{
  "document_id": "DOC-001",
  "entities": [
    {
      "node_id": "Unique identifier (e.g., PUMP-101A)",
      "entity_type": "MUST BE EXACTLY ONE OF: EQUIPMENT, SENSOR, PROCEDURE, HAZARD, COMPLIANCE_STANDARD",
      "description": "Brief description of what this entity is"
    }
  ],
  "relationships": [
    {
      "source_node": "ID of the source entity",
      "target_node": "ID of the target entity",
      "relation_type": "Uppercase string (e.g., CONNECTED_TO, MONITORS, CAUSES, GOVERNED_BY)",
      "context": "Brief explanation of how they are related based on the text"
    }
  ]
}

CRITICAL RULES:
1. 'entity_type' MUST strictly be one of the 5 allowed classifications.
2. Every node mentioned in 'relationships' MUST exist in the 'entities' list.
3. Output ONLY the raw JSON object. No markdown blocks, no conversational text.
"""

    def _ensure_directories(self) -> None:
        Path(self.inputs_dir).mkdir(exist_ok=True)
        Path(self.output_dir).mkdir(exist_ok=True)
        print(f"[✓] Ensured directories exist: '{self.inputs_dir}/', '{self.output_dir}/'")

    def _extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract text from PDF using PyMuPDF or PyPDF2 fallback.

        Uses a context manager when possible to ensure documents are closed
        and file handles are released to avoid memory/locked file issues.
        """
        try:
            if _PDF_ENGINE == "pymupdf":
                # PyMuPDF supports a context manager to ensure doc is closed
                try:
                    with fitz.open(str(pdf_path)) as doc:
                        parts = [page.get_text() for page in doc]
                        return "\n".join(parts)
                except Exception as e:
                    print(f"[!] PyMuPDF failed to read {pdf_path.name}: {e}")
                    return ""

            elif _PDF_ENGINE == "pypdf2":
                text_parts = []
                with open(pdf_path, "rb") as fh:
                    reader = PyPDF2.PdfReader(fh)
                    for page in reader.pages:
                        try:
                            text_parts.append(page.extract_text() or "")
                        except Exception:
                            continue
                return "\n".join(text_parts)

            else:
                print("[!] No PDF library available. Install 'pymupdf' or 'PyPDF2'.")
                return ""

        except Exception as e:
            print(f"[!] Error extracting PDF {pdf_path.name}: {e}")
            return ""

    def _get_text_files(self) -> List[Path]:
        input_path = Path(self.inputs_dir)
        if not input_path.exists():
            print(f"[!] Warning: Input directory '{self.inputs_dir}' does not exist.")
            return []

        txt_files = list(input_path.glob("*.txt"))
        pdf_files = list(input_path.glob("*.pdf"))
        all_files = sorted(txt_files) + sorted(pdf_files)

        if not all_files:
            print(f"[!] Warning: No .txt or .pdf files found in '{self.inputs_dir}/'")
            return []

        print(f"[✓] Found {len(all_files)} file(s) to process")
        for file in all_files:
            print(f"   - {file.name}")
        return all_files

    def _chunk_text(self, text: str, max_words: int = 800, overlap: int = 100) -> List[str]:
        """Chunk text into roughly `max_words` words with overlap; prefer paragraph boundaries."""
        if not text or not text.strip():
            return []

        paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
        chunks: List[str] = []
        current_words: List[str] = []

        def flush():
            if current_words:
                chunks.append(" ".join(current_words))

        for para in paragraphs:
            words = para.split()
            if not words:
                continue

            if len(words) >= max_words:
                flush()
                current_words = []
                start = 0
                while start < len(words):
                    end = start + max_words
                    chunks.append(" ".join(words[start:end]))
                    start = end - overlap if end - overlap > start else end
                continue

            if len(current_words) + len(words) > max_words:
                flush()
                # keep small overlap from previous chunk
                if overlap > 0:
                    tail = current_words[-overlap:] if len(current_words) >= overlap else current_words[:]
                    current_words = tail.copy()
                else:
                    current_words = []

            current_words.extend(words)

        flush()
        print(f"    [#] Chunked into {len(chunks)} piece(s)")
        return chunks

    def _extract_from_text(self, text: str, document_id: str) -> Dict:
        """
        Extract entities and relationships from a text chunk, retrying when malformed JSON is returned.
        """
        max_attempts = 3
        retry_prompt = (
            "CRITICAL: Your previous output was invalid JSON. "
            "You must return ONLY valid JSON matching the schema perfectly. "
            "Fix any trailing commas or unescaped characters."
        )

        for attempt in range(1, max_attempts + 1):
            try:
                print(f"   [*] Extraction attempt {attempt}/{max_attempts} for document '{document_id}'...")
                user_prompt = f"Extract the data from this text:\n\n{text}"
                if attempt > 1:
                    user_prompt += f"\n\n{retry_prompt}"

                response = ollama.chat(
                    model='llama3.2',
                    messages=[
                        {'role': 'system', 'content': self.system_prompt},
                        {'role': 'user', 'content': user_prompt}
                    ],
                    format='json',
                    options={'temperature': 0.0}
                )

                raw_json_str = response['message']['content']
                extracted_data = json.loads(raw_json_str)
                extracted_data['document_id'] = document_id

                # Normalize entity_type and protect contract
                for ent in extracted_data.get('entities', []):
                    et = ent.get('entity_type', '')
                    if isinstance(et, str) and et.upper() in self.ALLOWED_ENTITY_TYPES:
                        ent['entity_type'] = et.upper()
                    else:
                        ent['entity_type'] = 'UNKNOWN'

                return extracted_data

            except json.JSONDecodeError as e:
                print(f"   [!] Invalid JSON on attempt {attempt}/{max_attempts}: {e}")
                if attempt == max_attempts:
                    print(f"   [!] Skipping chunk after {max_attempts} failed JSON parses.")
                    return {}
                print("   [*] Retrying with stricter JSON enforcement prompt...")
                continue
            except Exception as e:
                print(f"   [!] Error during extraction on attempt {attempt}: {e}")
                print(f"      Ensure Ollama is running and Llama 3.2 is pulled.")
                return {}

        return {}

    def _merge_data(self, all_results: List[Dict]) -> Dict:
        merged_entities: Dict[str, Dict] = {}
        merged_relationships: List[Dict] = []

        for result in all_results:
            for entity in result.get('entities', []):
                node_id = entity.get('node_id')
                if not node_id:
                    continue

                if node_id in merged_entities:
                    existing = merged_entities[node_id]
                    # Prefer known entity_type
                    if existing.get('entity_type') == 'UNKNOWN' and entity.get('entity_type') in self.ALLOWED_ENTITY_TYPES:
                        existing['entity_type'] = entity.get('entity_type')
                    # Prefer longer description
                    if len(entity.get('description', '')) > len(existing.get('description', '')):
                        existing['description'] = entity.get('description')
                else:
                    merged_entities[node_id] = entity.copy()

            for rel in result.get('relationships', []):
                merged_relationships.append(rel.copy())

        # Filter relationships to ensure nodes exist
        filtered_rels = [r for r in merged_relationships if r.get('source_node') in merged_entities and r.get('target_node') in merged_entities]

        master_contract = {
            'document_id': 'BATCH-RUN-2026',
            'entities': list(merged_entities.values()),
            'relationships': filtered_rels
        }

        return master_contract

    def validate_extracted_contract(self, contract_path: str) -> bool:
        """Validate the generated graph contract for integrity and schema correctness."""
        print("\n" + "="*50)
        print("[>] Starting contract validation")
        print("="*50)

        if not os.path.exists(contract_path):
            print(f"[!] Validation failed: contract file not found at {contract_path}")
            print("Contract Validation: 0% Failed")
            return False

        try:
            print(f"[>] Loading contract file: {contract_path}")
            with open(contract_path, 'r', encoding='utf-8') as fh:
                contract = json.load(fh)
            print("[>] Contract JSON loaded successfully.")
        except Exception as e:
            print(f"[!] Validation failed: could not load JSON contract. {e}")
            print("Contract Validation: 0% Failed")
            return False

        print("[>] Validating JSON structure...")
        if not isinstance(contract, dict):
            print("[!] Validation failed: contract root element must be a JSON object.")
            print("Contract Validation: 0% Failed")
            return False

        entities = contract.get('entities', [])
        relationships = contract.get('relationships', [])

        if not isinstance(entities, list):
            print("[!] Validation failed: 'entities' must be a list.")
            print("Contract Validation: 0% Failed")
            return False

        if not isinstance(relationships, list):
            print("[!] Validation failed: 'relationships' must be a list.")
            print("Contract Validation: 0% Failed")
            return False

        print("[>] Checking allowed entity types...")
        entity_ids = {entity.get('node_id') for entity in entities if isinstance(entity, dict) and entity.get('node_id')}
        invalid_types = []
        for entity in entities:
            if not isinstance(entity, dict):
                continue
            entity_type = entity.get('entity_type')
            if entity_type not in self.ALLOWED_ENTITY_TYPES:
                invalid_types.append((entity.get('node_id'), entity_type))

        print("[>] Checking orphan nodes in relationships...")
        orphan_relationships = []
        for rel in relationships:
            if not isinstance(rel, dict):
                continue
            source = rel.get('source_node')
            target = rel.get('target_node')
            if source not in entity_ids or target not in entity_ids:
                orphan_relationships.append((source, target))

        issue_count = 0
        if invalid_types:
            issue_count += len(invalid_types)
            print("[!] Contract Validation Warning: invalid entity types detected")
            for node_id, entity_type in invalid_types:
                print(f"    - Node '{node_id}' has invalid type '{entity_type}'")

        if orphan_relationships:
            issue_count += len(orphan_relationships)
            print("[!] Contract Validation Warning: orphan relationships detected")
            for source, target in orphan_relationships:
                print(f"    - Relationship references missing node: {source} -> {target}")

        if issue_count == 0:
            print("\n" + "="*50)
            print("[V] CONTRACT VALIDATION: 100% PASSED")
            print("="*50 + "\n")
            return True

        score = max(0, 100 - issue_count * 20)
        print(f"Contract Validation: {score}% Issues found: {issue_count}")
        return False

    def process_batch(self) -> Tuple[bool, str]:
        print("\n" + "="*70)
        print("BATCH LLM EXTRACTOR - GraphRAG Pipeline")
        print("="*70 + "\n")

        self._ensure_directories()
        files = self._get_text_files()

        if not files:
            message = "No input files found in inputs/ directory to process."
            print(f"\n[!] {message}")
            return False, message

        print(f"\n[*] Starting extraction from {len(files)} file(s)...\n")
        all_results: List[Dict] = []

        for i, file_path in enumerate(files, 1):
            print(f"[{i}/{len(files)}] Processing: {file_path.name}")
            try:
                document_id = file_path.stem

                if file_path.suffix.lower() == '.pdf':
                    text_content = self._extract_text_from_pdf(file_path)
                else:
                    with open(file_path, 'r', encoding='utf-8') as fh:
                        text_content = fh.read()

                if not text_content or not text_content.strip():
                    print(f"   [!] Warning: File is empty or unreadable, skipping")
                    continue

                chunks = self._chunk_text(text_content)
                if not chunks:
                    print(f"   [!] Warning: No chunks produced for file, skipping")
                    continue

                file_level_results: List[Dict] = []
                for j, chunk in enumerate(chunks, 1):
                    print(f"   -> Chunk {j}/{len(chunks)}")
                    extracted = self._extract_from_text(chunk, document_id)
                    if extracted:
                        file_level_results.append(extracted)

                if file_level_results:
                    # Consolidate per-file results by concatenation (dedup happens later)
                    merged = {'document_id': document_id, 'entities': [], 'relationships': []}
                    for r in file_level_results:
                        merged['entities'].extend(r.get('entities', []))
                        merged['relationships'].extend(r.get('relationships', []))
                    all_results.append(merged)
                else:
                    print(f"   [!] No extraction results for file: {file_path.name}")

            except Exception as e:
                print(f"   [!] Error processing file {file_path.name}: {e}")
                continue

        if not all_results:
            message = "No data could be extracted from any files."
            print(f"\n[!] {message}")
            return False, message

        print(f"\n[*] Merging data from {len(all_results)} source(s)...")
        master_contract = self._merge_data(all_results)

        try:
            output_path = os.path.join(self.output_dir, 'graph_input.json')
            with open(output_path, 'w', encoding='utf-8') as fh:
                json.dump(master_contract, fh, indent=2)

            entity_count = len(master_contract['entities'])
            relationship_count = len(master_contract['relationships'])
            print(f"[✓] Master graph contract saved to: {output_path}")
            print(f"    Document ID: {master_contract['document_id']}")
            print(f"    Total Entities: {entity_count}")
            print(f"    Total Relationships: {relationship_count}")

            # Run contract validation after the file is written
            self.validate_extracted_contract(output_path)
            return True, f"Successfully processed {len(files)} file(s)"

        except Exception as e:
            message = f"Failed to save output file: {e}"
            print(f"\n[!] {message}")
            return False, message


    def process_single_file_and_merge(self, file_path: str, existing_json_path: str) -> bool:
        """Extract entities/relationships from a single file and merge them into an existing graph contract."""
        p = Path(file_path)
        if not p.exists():
            print(f"[!] File not found: {file_path}")
            return False

        print(f"\n[*] Processing single file: {p.name}")
        document_id = p.stem.upper().replace(' ', '-')

        # Extract text
        if p.suffix.lower() == '.pdf':
            text_content = self._extract_text_from_pdf(p)
        else:
            text_content = self._extract_text_from_txt(p)

        if not text_content or not text_content.strip():
            print("   [!] File is empty or unreadable.")
            return False

        # Chunk and extract
        chunks = self._chunk_text(text_content)
        if not chunks:
            return False

        file_level_results: List[Dict] = []
        for j, chunk in enumerate(chunks, 1):
            print(f"   -> Chunk {j}/{len(chunks)}")
            extracted = self._extract_from_text(chunk, document_id)
            if extracted:
                file_level_results.append(extracted)

        if not file_level_results:
            print("   [!] No data extracted.")
            return False

        # Load existing graph
        existing_data = []
        if os.path.exists(existing_json_path):
            try:
                with open(existing_json_path, 'r', encoding='utf-8') as fh:
                    existing = json.load(fh)
                    # We wrap it in a list so _merge_data can treat it as one of the results
                    existing_data.append(existing)
            except Exception as e:
                print(f"   [!] Failed to load existing graph: {e}")

        # Combine old data with the new file's results
        all_results = existing_data + file_level_results
        master_contract = self._merge_data(all_results)

        try:
            with open(existing_json_path, 'w', encoding='utf-8') as fh:
                json.dump(master_contract, fh, indent=2)
            
            print(f"[✓] Graph updated with {p.name}. Saved to {existing_json_path}")
            return True
        except Exception as e:
            print(f"   [!] Failed to save updated graph: {e}")
            return False


def main():
    extractor = BatchExtractor(inputs_dir='../data/raw_documents', output_dir='../data')
    success, message = extractor.process_batch()

    if success:
        output_path = os.path.join(extractor.output_dir, 'graph_input.json')
        print("\n" + "="*70)
        print(f"[✓] Batch extraction completed. Running contract validation on: {output_path}")
        print("="*70 + "\n")
        extractor.validate_extracted_contract(output_path)
        print("\n" + "="*70)
        print(f"[SUCCESS] {message}")
        print("="*70 + "\n")
    else:
        print("\n" + "="*70)
        print(f"[FAILURE] {message}")
        print("="*70 + "\n")

    return 0 if success else 1


if __name__ == '__main__':
    exit(main())
