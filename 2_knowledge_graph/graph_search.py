"""
Graph Search Engine - GraphRAG Query Interface
Loads a persisted knowledge graph and answers user queries using local Ollama inference
with grounded, graph-extracted context.
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
    Loads a pre-built NetworkX graph and retrieves grounded context for LLM inference.
    """

    def __init__(self, graph_path: str = "../data/graph.graphml", data_contract_path: str = "../data/graph_input.json"):
        """
        Initialize the Graph Search Engine.

        Args:
            graph_path: Path to the saved NetworkX graph (GraphML format)
            data_contract_path: Path to the original JSON data contract
        """
        self.graph_path = graph_path
        self.data_contract_path = data_contract_path
        self.graph = None
        self.data_contract = None

    def load_graph(self) -> bool:
        """
        Load the persisted graph from disk.

        Returns:
            True if successfully loaded, False otherwise
        """
        print(f"[*] Loading graph from: {self.graph_path}")

        if not os.path.exists(self.graph_path):
            print(f"[!] Error: Graph file not found at {self.graph_path}")
            print("    Run graph_builder.py first to generate the graph.")
            return False

        try:
            self.graph = nx.read_graphml(self.graph_path)
            print(f"[✓] Graph loaded successfully")
            print(f"    Nodes: {self.graph.number_of_nodes()}")
            print(f"    Edges: {self.graph.number_of_edges()}")
            return True
        except Exception as e:
            print(f"[!] Error reading graph file: {e}")
            return False

    def load_data_contract(self) -> bool:
        """
        Load the original data contract for reference.

        Returns:
            True if successfully loaded, False otherwise
        """
        if not os.path.exists(self.data_contract_path):
            print(f"[!] Warning: Data contract not found at {self.data_contract_path}")
            return False

        try:
            with open(self.data_contract_path, 'r', encoding='utf-8') as f:
                self.data_contract = json.load(f)
            print(f"[✓] Data contract loaded ({len(self.data_contract.get('entities', []))} entities)")
            return True
        except Exception as e:
            print(f"[!] Error loading data contract: {e}")
            return False

    def find_relevant_nodes(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Find nodes relevant to a query using simple keyword matching.
        This is a basic implementation; advanced versions can use embeddings or BM25.

        Args:
            query: User query string
            top_k: Number of top results to return

        Returns:
            List of (node_id, relevance_score) tuples
        """
        if self.graph is None:
            return []

        query_lower = query.lower()
        query_words = set(query_lower.split())

        node_scores = {}

        for node_id in self.graph.nodes():
            node_attrs = self.graph.nodes[node_id]
            description = node_attrs.get('description', '').lower()
            entity_type = node_attrs.get('entity_type', '').lower()

            # Calculate relevance score
            score = 0.0
            description_words = set(description.split())
            matching_words = query_words & description_words

            if matching_words:
                score += len(matching_words) * 2.0  # Weight word matches in description

            if query_lower in entity_type or entity_type in query_lower:
                score += 3.0  # Weight entity type matches

            if node_id.lower() in query_lower or query_lower in node_id.lower():
                score += 2.0  # Weight node ID matches

            if score > 0:
                node_scores[node_id] = score

        # Sort by score and return top_k
        sorted_nodes = sorted(node_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_nodes[:top_k]

    def extract_context_neighborhood(self, node_ids: List[str], depth: int = 1) -> str:
        """
        Extract a neighborhood context around a set of query nodes.
        Includes the nodes themselves plus their connections up to `depth` hops.

        Args:
            node_ids: List of seed node IDs
            depth: Number of hops to expand the neighborhood

        Returns:
            Formatted context string for LLM consumption
        """
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

                # Extract outgoing connections
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

                # Extract incoming connections
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
        """
        Execute a query against the graph and generate a grounded LLM response.

        Args:
            question: User query
            top_k: Number of relevant nodes to retrieve
            context_depth: Hops for neighborhood extraction

        Returns:
            Tuple of (context_summary, llm_answer)
        """
        if self.graph is None:
            return "", "[!] Error: Graph not loaded"

        print(f"\n[*] Searching for nodes relevant to: '{question}'")

        # Find relevant nodes
        relevant_nodes = self.find_relevant_nodes(question, top_k=top_k)

        if not relevant_nodes:
            print("[!] No relevant nodes found in graph")
            return "", "I could not find any relevant information in the knowledge graph to answer your question."

        print(f"[✓] Found {len(relevant_nodes)} relevant node(s)")
        for node_id, score in relevant_nodes:
            print(f"    • {node_id} (score: {score:.2f})")

        node_ids = [node_id for node_id, _ in relevant_nodes]

        # Extract neighborhood context
        print(f"[*] Extracting neighborhood context (depth={context_depth})...")
        context = self.extract_context_neighborhood(node_ids, depth=context_depth)

        # Debug output: Display raw context
        print("\n" + "="*70)
        print("--- RETRIEVED GRAPH CONTEXT (Passed to LLM) ---")
        print("="*70)
        print(context)
        print("="*70 + "\n")

        # Build LLM prompt with grounded context
        system_prompt = """You are a knowledge graph query assistant for an industrial system.
Your job is to answer user questions ONLY using the provided graph context.
Be concise, factual, and grounded in the extracted information.
If the context doesn't contain enough information, say so explicitly."""

        user_prompt = f"""Based on this graph context, answer the following question:

GRAPH CONTEXT:
{context}

QUESTION: {question}

Please provide a clear, concise answer grounded in the graph data."""

        print("[*] Querying Ollama (Llama 3.2) for grounded answer...")

        try:
            response = ollama.chat(
                model='llama3.2',
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ],
                options={'temperature': 0.3}  # Lower temperature for factual answers
            )

            answer = response['message']['content']
            print("[✓] Answer generated successfully")
            return context, answer

        except Exception as e:
            print(f"[!] Error querying Ollama: {e}")
            return context, f"[!] Error generating response: {e}"


def interactive_search():
    """
    Interactive search loop for querying the graph.
    """
    print("\n" + "="*70)
    print("GRAPH SEARCH ENGINE - Interactive Query Interface")
    print("="*70 + "\n")

    # Initialize search engine
    engine = GraphSearchEngine(graph_path="../data/graph.graphml", data_contract_path="../data/graph_input.json")

    # Load graph
    if not engine.load_graph():
        print("[!] Failed to load graph. Exiting.")
        return 1

    # Load data contract (optional)
    engine.load_data_contract()

    print("\n[*] Graph Search Engine ready. Enter 'quit' to exit.\n")

    while True:
        try:
            question = input("[?] Query: ").strip()

            if question.lower() in ['quit', 'exit', 'q']:
                print("[*] Exiting...")
                break

            if not question:
                print("[!] Please enter a question.")
                continue

            # Execute query
            context, answer = engine.query(question, top_k=5, context_depth=1)

            print("\n" + "-"*70)
            print("ANSWER:")
            print("-"*70)
            print(answer)
            print("-"*70 + "\n")

        except KeyboardInterrupt:
            print("\n[*] Interrupted. Exiting...")
            break
        except Exception as e:
            print(f"[!] Error during query: {e}")
            continue

    return 0


def main():
    """
    Main entry point.
    """
    return interactive_search()


if __name__ == "__main__":
    exit(main())
