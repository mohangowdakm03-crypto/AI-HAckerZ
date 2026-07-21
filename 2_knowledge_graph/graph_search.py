"""
Graph Search Engine - GraphRAG Query Interface
Loads a persisted knowledge graph and answers user queries using local Ollama inference
with grounded, graph-extracted context via ChromaDB Vector Search.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import networkx as nx
import ollama

class GraphSearchEngine:
    """
    Query engine for the offline Edge-Computing GraphRAG Pipeline.
    Loads a pre-built NetworkX graph, embeds nodes into ChromaDB, and retrieves grounded context.
    """

    def __init__(self, graph_path: str = "../data/graph.graphml", data_contract_path: str = "../data/graph_input.json", session_id: str = "default"):
        """
        Initialize the Graph Search Engine.

        Args:
            graph_path: Path to the saved NetworkX graph (GraphML format)
            data_contract_path: Path to the original JSON data contract
            session_id: Unique session ID to isolate vector collections
        """
        self.graph_path = graph_path
        self.data_contract_path = data_contract_path
        self.session_id = session_id
        self.graph = None
        self.data_contract = None
        self.chroma_client = None
        self.collection = None

    def load_graph(self) -> bool:
        """
        Load the persisted graph from disk and sync with Vector DB.
        """
        print(f"[*] Loading graph from: {self.graph_path}")

        if not os.path.exists(self.graph_path):
            print(f"[!] Error: Graph file not found at {self.graph_path}")
            return False

        try:
            self.graph = nx.read_graphml(self.graph_path)
            print(f"[✓] Graph loaded successfully")
            print(f"    Nodes: {self.graph.number_of_nodes()}")
            print(f"    Edges: {self.graph.number_of_edges()}")
            
            # Sync to ChromaDB
            self.sync_chromadb()
            return True
        except Exception as e:
            print(f"[!] Error reading graph file: {e}")
            return False

    def sync_chromadb(self) -> bool:
        """
        Embed all graph nodes into a local ChromaDB collection for fast semantic search.
        """
        if self.graph is None:
            return False

        print("[*] Synchronizing Graph with ChromaDB Vector Store...")
        import chromadb
        from chromadb.utils.embedding_functions import OllamaEmbeddingFunction

        try:
            ef = OllamaEmbeddingFunction(
                url="http://localhost:11434/api/embeddings",
                model_name="nomic-embed-text"
            )
            
            chroma_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/chroma"))
            os.makedirs(chroma_path, exist_ok=True)
            self.chroma_client = chromadb.PersistentClient(path=chroma_path)
            
            # Use safe collection name (alphanumeric and underscores only)
            safe_session_id = "".join([c if c.isalnum() else "_" for c in self.session_id])
            collection_name = f"graph_nodes_{safe_session_id}"
            
            try:
                self.chroma_client.delete_collection(collection_name)
            except Exception:
                pass
                
            self.collection = self.chroma_client.get_or_create_collection(
                name=collection_name,
                embedding_function=ef
            )

            docs = []
            metas = []
            ids = []

            for node_id in self.graph.nodes():
                node_attrs = self.graph.nodes[node_id]
                desc = node_attrs.get('description', '')
                etype = node_attrs.get('entity_type', 'UNKNOWN')
                
                # Rich document string for vector matching
                doc_string = f"Entity Type: {etype}. ID: {node_id}. Description: {desc}."
                
                docs.append(doc_string)
                metas.append({'entity_type': etype})
                ids.append(node_id)
                
            if docs:
                print(f"[*] Embedding {len(docs)} nodes into vector database...")
                # ChromaDB requires batches for huge inserts, but our graphs are small enough to do at once.
                self.collection.add(
                    documents=docs,
                    metadatas=metas,
                    ids=ids
                )
                print("[✓] ChromaDB synchronization complete.")
            return True
        except Exception as e:
            print(f"[!] Error synchronizing with ChromaDB: {e}")
            return False

    def load_data_contract(self) -> bool:
        if not os.path.exists(self.data_contract_path):
            return False

        try:
            with open(self.data_contract_path, 'r', encoding='utf-8') as f:
                self.data_contract = json.load(f)
            return True
        except Exception:
            return False

    def find_relevant_nodes(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Find nodes relevant to a query using ChromaDB Vector Search.
        """
        if not hasattr(self, 'collection') or self.collection is None:
            print("[!] ChromaDB collection is not initialized.")
            return []
            
        print(f"[*] Querying ChromaDB for: '{query}'")
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k
            )
            
            relevant_nodes = []
            if results['ids'] and len(results['ids'][0]) > 0:
                node_ids = results['ids'][0]
                distances = results['distances'][0] if 'distances' in results and results['distances'] else []
                
                for idx, n_id in enumerate(node_ids):
                    # Chroma uses L2 distance by default (lower is closer).
                    # We invert it to a "score" purely for logging visibility.
                    distance = distances[idx] if idx < len(distances) else 1.0
                    score = max(0.0, 10.0 - distance)
                    relevant_nodes.append((n_id, score))
                    
            return relevant_nodes
        except Exception as e:
            print(f"[!] Error querying ChromaDB: {e}")
            return []

    def find_path(self, source_node: str, target_node: str) -> Optional[List[str]]:
        if self.graph is None:
            return None
        if source_node not in self.graph.nodes() or target_node not in self.graph.nodes():
            return None
        try:
            return nx.shortest_path(self.graph, source=source_node, target=target_node)
        except nx.NetworkXNoPath:
            try:
                undirected = self.graph.to_undirected()
                return nx.shortest_path(undirected, source=source_node, target=target_node)
            except nx.NetworkXNoPath:
                return None
        except nx.NodeNotFound:
            return None

    def format_path_as_context(self, path: List[str]) -> str:
        if not path or self.graph is None:
            return ""

        lines = ["=" * 60, "RELATIONSHIP PATH CONTEXT", "=" * 60, ""]
        for i, node_id in enumerate(path):
            node_attrs = self.graph.nodes.get(node_id, {})
            etype = node_attrs.get('entity_type', 'UNKNOWN')
            desc  = node_attrs.get('description', '')
            lines.append(f"[{i+1}] {node_id}  ({etype})")
            lines.append(f"     {desc}")

            if i < len(path) - 1:
                next_id = path[i + 1]
                edge_data = self.graph.get_edge_data(node_id, next_id) or \
                            self.graph.get_edge_data(next_id, node_id) or {}
                rel   = edge_data.get('relation_type', '——')
                ctx   = edge_data.get('context', '')
                lines.append(f"       ↓ [{rel}]")
                if ctx:
                    lines.append(f"         ({ctx})")
            lines.append("")

        lines.append("=" * 60)
        return "\n".join(lines)

    def extract_context_neighborhood(self, node_ids: List[str], depth: int = 1) -> str:
        if self.graph is None or not node_ids:
            return ""

        context_lines = []
        context_lines.append("="*60)
        context_lines.append("EXTRACTED GRAPH CONTEXT FOR QUERY")
        context_lines.append("="*60)
        context_lines.append("")

        visited_nodes = set()
        frontier = list(node_ids)

        for hop in range(depth):
            next_frontier = []

            for node_id in frontier:
                if node_id in visited_nodes or node_id not in self.graph.nodes():
                    continue

                visited_nodes.add(node_id)
                node_attrs = self.graph.nodes[node_id]
                context_lines.append(f"NODE: {node_id}")
                context_lines.append(f"  Type: {node_attrs.get('entity_type', 'UNKNOWN')}")
                context_lines.append(f"  Description: {node_attrs.get('description', 'N/A')}")

                outgoing = list(self.graph.out_edges(node_id, data=True))
                if outgoing:
                    context_lines.append("  OUTGOING:")
                    for source, target, edge_attrs in outgoing:
                        relation_type = edge_attrs.get('relation_type', 'UNKNOWN')
                        context = edge_attrs.get('context', '')
                        context_lines.append(f"    -> {target} [{relation_type}]")
                        if context:
                            context_lines.append(f"       ({context})")
                        if target not in visited_nodes:
                            next_frontier.append(target)

                incoming = list(self.graph.in_edges(node_id, data=True))
                if incoming:
                    context_lines.append("  INCOMING:")
                    for source, target, edge_attrs in incoming:
                        relation_type = edge_attrs.get('relation_type', 'UNKNOWN')
                        context = edge_attrs.get('context', '')
                        context_lines.append(f"    <- {source} [{relation_type}]")
                        if context:
                            context_lines.append(f"       ({context})")
                        if source not in visited_nodes:
                            next_frontier.append(source)

                context_lines.append("")

            frontier = next_frontier
            if not frontier:
                break

        context_lines.append("="*60)
        return "\n".join(context_lines)

    def query(self, question: str, top_k: int = 5, context_depth: int = 1) -> Tuple[str, str]:
        if self.graph is None:
            return "", "[!] Error: Graph not loaded"

        print(f"\n[*] Searching for nodes relevant to: '{question}'")

        relevant_nodes = self.find_relevant_nodes(question, top_k=top_k)

        if not relevant_nodes:
            print("[!] No relevant nodes found in vector database")
            return "", "I could not find any relevant information in the knowledge graph to answer your question."

        print(f"[✓] Found {len(relevant_nodes)} relevant node(s)")
        for node_id, score in relevant_nodes:
            print(f"    • {node_id} (distance score: {score:.2f})")

        node_ids = [node_id for node_id, _ in relevant_nodes]

        print(f"[*] Extracting neighborhood context (depth={context_depth})...")
        context = self.extract_context_neighborhood(node_ids, depth=context_depth)

        print("\n" + "="*70)
        print("--- RETRIEVED GRAPH CONTEXT (Passed to LLM) ---")
        print("="*70)
        print(context)
        print("="*70 + "\n")

        system_prompt = "You are a knowledge graph query assistant for an industrial system.\n" \
                        "Your job is to answer user questions ONLY using the provided graph context.\n" \
                        "Be concise, factual, and grounded in the extracted information.\n" \
                        "If the context doesn't contain enough information, say so explicitly."

        user_prompt = f"Based on this graph context, answer the following question:\n\n" \
                      f"GRAPH CONTEXT:\n{context}\n\n" \
                      f"QUESTION: {question}\n\n" \
                      f"Please provide a clear, concise answer grounded in the graph data."

        print("[*] Querying Ollama (Llama 3.1) for grounded answer...")
        try:
            response = ollama.chat(
                model='llama3.1',
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ],
                options={'temperature': 0.3}
            )

            answer = response['message']['content']
            print("[✓] Answer generated successfully")
            return context, answer
        except Exception as e:
            print(f"[!] Error querying Ollama: {e}")
            return context, f"[!] Error generating response: {e}"

def interactive_search():
    print("\n" + "="*70)
    print("GRAPH SEARCH ENGINE - Interactive Vector Query Interface")
    print("="*70 + "\n")
    
    engine = GraphSearchEngine(graph_path="../data/graph.graphml", data_contract_path="../data/graph_input.json", session_id="interactive")
    if not engine.load_graph():
        print("[!] Failed to load graph. Exiting.")
        return 1
    engine.load_data_contract()
    print("\n[*] Graph Search Engine ready. Enter 'quit' to exit.\n")

    while True:
        try:
            question = input("[?] Query: ").strip()
            if question.lower() in ['quit', 'exit', 'q']:
                break
            if not question:
                continue
            context, answer = engine.query(question, top_k=5, context_depth=1)
            print("\n" + "-"*70)
            print("ANSWER:")
            print("-"*70)
            print(answer)
            print("-"*70 + "\n")
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[!] Error: {e}")
            continue
    return 0

def main():
    return interactive_search()

if __name__ == "__main__":
    exit(main())
