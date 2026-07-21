import os
import json
import ollama

def extract_industrial_data():
    """
    Extracts entities and relationships from industrial text using local Llama 3.1.
    Strictly outputs the JSON data contract required for the GraphRAG pipeline.
    """
    
    # 1. Dummy Industrial Text (Cooling Pump Manual & Shift Log)
    raw_text = """
    PUMP-101A is the primary cooling water pump for the reactor system. 
    It is directly connected to VALVE-204, which regulates the intake flow. 
    During operations, TEMP-SENS-08 monitors the casing temperature. If the temperature 
    exceeds 85C, it poses a severe OVERHEATING-RISK. In such an event, operators must 
    immediately execute the EMERGENCY-SHUTDOWN-01 protocol to ensure compliance with 
    the ISO-45001-SAFETY standard.
    """

    # 2. Strict System Prompt enforcing the JSON Contract
    system_prompt = """You are an elite industrial AI data extractor. 
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

    print("[*] Initializing local extraction via Ollama (Llama 3.1)...")
    
    # 3. Execute Local Inference
    try:
        response = ollama.chat(
            model='llama3.1',
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': f"Extract the data from this text:\n\n{raw_text}"}
            ],
            format='json',
            options={
                'temperature': 0.0  # Force deterministic structural outputs
            }
        )
        
        # 4. Parse Output
        raw_json_str = response['message']['content']
        graph_data = json.loads(raw_json_str)
        
        # Ensure document_id is present
        if "document_id" not in graph_data:
            graph_data["document_id"] = "DOC-MANUAL-001"

        # 5. Save output locally for Person 2
        output_dir = "../data"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "mock_contract.json")
        
        with open(output_path, "w") as f:
            json.dump(graph_data, f, indent=2)
            
        print(f"[+] Success! Extracted JSON contract saved to: {output_path}")
        print("\n--- Preview of Extracted Data ---")
        print(json.dumps(graph_data, indent=2))
        
    except json.JSONDecodeError as e:
        print(f"[!] Error: Model failed to return valid JSON. Details: {e}")
    except Exception as e:
        print(f"[!] Pipeline Error: Ensure Ollama is running and Llama 3.1 is pulled. Details: {e}")

if __name__ == "__main__":
    extract_industrial_data()