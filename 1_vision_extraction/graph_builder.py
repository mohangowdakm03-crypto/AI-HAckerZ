"""
Graph Builder - GraphRAG Backend Engine
Constructs an in-memory knowledge graph from the data contract JSON and provides
context extraction capabilities for the local Ollama model (Person 3).
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import networkx as nx


class GraphRAGBuilder:
    """
    Backend graph engine for offline Edge-Computing GraphRAG Pipeline.
    Loads entity/relationship data and builds a directed knowledge graph using NetworkX.
    Provides local context extraction for LLM inference.
    """
    
    def __init__(self, data_contract_path: str = "data/graph_input.json"):
        """
        Initialize the GraphRAG builder.
        
        Args:
            data_contract_path: Path to the JSON data contract file from Person 1
        """
        self.data_contract_path = data_contract_path
        self.graph = nx.DiGraph()
        self.data_contract = None
        self.document_id = None
        
    def load_data_contract(self) -> bool:
        """
        Load the JSON data contract from disk.
        
        Returns:
            True if successfully loaded, False otherwise
        """
        print(f"[*] Loading data contract from: {self.data_contract_path}")
        
        if not os.path.exists(self.data_contract_path):
            print(f"[!] Error: File not found at {self.data_contract_path}")
            return False
        
        try:
            with open(self.data_contract_path, 'r', encoding='utf-8') as f:
                self.data_contract = json.load(f)
            
            # Validate schema
            required_keys = {'document_id', 'entities', 'relationships'}
            if not required_keys.issubset(self.data_contract.keys()):
                print(f"[!] Error: JSON missing required keys: {required_keys}")
                return False
            
            self.document_id = self.data_contract['document_id']
            print(f"[✓] Data contract loaded successfully")
            print(f"    Document ID: {self.document_id}")
            print(f"    Entities: {len(self.data_contract.get('entities', []))}")
            print(f"    Relationships: {len(self.data_contract.get('relationships', []))}")
            
            return True
            
        except json.JSONDecodeError as e:
            print(f"[!] Error: Invalid JSON file. Details: {e}")
            return False
        except Exception as e:
            print(f"[!] Error reading file: {e}")
            return False
    
    def build_graph(self) -> bool:
        """
        Build the directed graph from the data contract.
        
        Returns:
            True if successfully built, False otherwise
        """
        if self.data_contract is None:
            print("[!] Error: Data contract not loaded. Call load_data_contract() first.")
            return False
        
        print(f"\n[*] Building directed graph...")
        
        # Step 1: Add entities as nodes
        entities = self.data_contract.get('entities', [])
        print(f"[*] Adding {len(entities)} nodes...")
        
        for entity in entities:
            node_id = entity.get('node_id')
            if not node_id:
                print(f"[!] Warning: Entity missing 'node_id', skipping")
                continue
            
            # Add node with attributes
            self.graph.add_node(
                node_id,
                entity_type=entity.get('entity_type', 'UNKNOWN'),
                description=entity.get('description', '')
            )
        
        print(f"[✓] Added {self.graph.number_of_nodes()} nodes to graph")
        
        # Step 2: Add relationships as directed edges
        relationships = self.data_contract.get('relationships', [])
        print(f"[*] Adding {len(relationships)} edges...")
        
        added_edges = 0
        skipped_edges = 0
        
        for rel in relationships:
            source_node = rel.get('source_node')
            target_node = rel.get('target_node')
            
            if not source_node or not target_node:
                print(f"[!] Warning: Relationship missing source/target, skipping")
                skipped_edges += 1
                continue
            
            # Validate that both nodes exist
            if source_node not in self.graph.nodes() or target_node not in self.graph.nodes():
                print(f"[!] Warning: Relationship references non-existent node(s): "
                      f"{source_node} -> {target_node}")
                skipped_edges += 1
                continue
            
            # Add directed edge with attributes
            self.graph.add_edge(
                source_node,
                target_node,
                relation_type=rel.get('relation_type', 'UNKNOWN'),
                context=rel.get('context', '')
            )
            added_edges += 1
        
        print(f"[✓] Added {added_edges} directed edges to graph")
        if skipped_edges > 0:
            print(f"[!] Skipped {skipped_edges} invalid relationships")
        
        return True
    
    def extract_local_context(self, query_node_id: str) -> Optional[str]:
        """
        Extract local context around a query node.
        Retrieves immediate neighbors (incoming and outgoing edges) and formats
        as a structured text summary for downstream LLM processing.
        
        Args:
            query_node_id: The node ID to query
            
        Returns:
            Formatted context string, or None if node not found
        """
        # Validate node exists
        if query_node_id not in self.graph.nodes():
            return None
        
        node_attrs = self.graph.nodes[query_node_id]
        context_lines = []
        
        # Header
        context_lines.append(f"=== LOCAL CONTEXT: {query_node_id} ===")
        context_lines.append(f"Type: {node_attrs.get('entity_type', 'UNKNOWN')}")
        context_lines.append(f"Description: {node_attrs.get('description', 'N/A')}")
        context_lines.append("")
        
        # Outgoing edges (this node connects TO others)
        outgoing = list(self.graph.out_edges(query_node_id, data=True))
        if outgoing:
            context_lines.append("--- OUTGOING CONNECTIONS ---")
            for source, target, edge_attrs in outgoing:
                relation_type = edge_attrs.get('relation_type', 'UNKNOWN')
                context = edge_attrs.get('context', '')
                target_type = self.graph.nodes[target].get('entity_type', 'UNKNOWN')
                target_desc = self.graph.nodes[target].get('description', '')
                
                context_lines.append(f"• {query_node_id} --[{relation_type}]--> {target}")
                context_lines.append(f"  Target Type: {target_type}")
                context_lines.append(f"  Target: {target_desc[:80]}...")
                if context:
                    context_lines.append(f"  Relation Context: {context}")
                context_lines.append("")
        
        # Incoming edges (others connect TO this node)
        incoming = list(self.graph.in_edges(query_node_id, data=True))
        if incoming:
            context_lines.append("--- INCOMING CONNECTIONS ---")
            for source, target, edge_attrs in incoming:
                relation_type = edge_attrs.get('relation_type', 'UNKNOWN')
                context = edge_attrs.get('context', '')
                source_type = self.graph.nodes[source].get('entity_type', 'UNKNOWN')
                source_desc = self.graph.nodes[source].get('description', '')
                
                context_lines.append(f"• {source} --[{relation_type}]--> {query_node_id}")
                context_lines.append(f"  Source Type: {source_type}")
                context_lines.append(f"  Source: {source_desc[:80]}...")
                if context:
                    context_lines.append(f"  Relation Context: {context}")
                context_lines.append("")
        
        # Graph metrics
        context_lines.append("--- LOCAL GRAPH METRICS ---")
        in_degree = self.graph.in_degree(query_node_id)
        out_degree = self.graph.out_degree(query_node_id)
        context_lines.append(f"In-Degree (incoming): {in_degree}")
        context_lines.append(f"Out-Degree (outgoing): {out_degree}")
        
        return "\n".join(context_lines)
    
    def get_graph_stats(self) -> Dict:
        """
        Get basic statistics about the graph.
        
        Returns:
            Dictionary with graph statistics
        """
        return {
            'document_id': self.document_id,
            'total_nodes': self.graph.number_of_nodes(),
            'total_edges': self.graph.number_of_edges(),
            'is_directed': self.graph.is_directed(),
            'is_connected': nx.is_strongly_connected(self.graph) if self.graph.number_of_nodes() > 0 else False,
            'num_weakly_connected_components': nx.number_weakly_connected_components(self.graph),
            'average_in_degree': sum(dict(self.graph.in_degree()).values()) / max(self.graph.number_of_nodes(), 1),
            'average_out_degree': sum(dict(self.graph.out_degree()).values()) / max(self.graph.number_of_nodes(), 1)
        }
    
    def get_all_node_ids(self) -> List[str]:
        """
        Get list of all node IDs in the graph.
        
        Returns:
            List of node IDs
        """
        return list(self.graph.nodes())
    
    def get_node_info(self, node_id: str) -> Optional[Dict]:
        """
        Get detailed information about a specific node.
        
        Args:
            node_id: The node ID to query
            
        Returns:
            Dictionary with node attributes, or None if not found
        """
        if node_id not in self.graph.nodes():
            return None
        
        node_attrs = self.graph.nodes[node_id]
        return {
            'node_id': node_id,
            'entity_type': node_attrs.get('entity_type'),
            'description': node_attrs.get('description'),
            'in_degree': self.graph.in_degree(node_id),
            'out_degree': self.graph.out_degree(node_id)
        }


def main():
    """
    Main execution block: Initialize graph, display statistics, save to disk, and run test queries.
    """
    print("\n" + "="*70)
    print("GRAPH BUILDER - GraphRAG Backend Engine")
    print("="*70 + "\n")
    
    # Initialize builder
    builder = GraphRAGBuilder(data_contract_path="data/graph_input.json")
    
    # Load data contract
    if not builder.load_data_contract():
        print("[!] Failed to load data contract. Exiting.")
        return 1
    
    # Build the graph
    if not builder.build_graph():
        print("[!] Failed to build graph. Exiting.")
        return 1
    
    # Save graph to disk
    print("\n[*] Saving graph to disk...")
    graph_output_path = "data/graph.graphml"
    try:
        nx.write_graphml(builder.graph, graph_output_path)
        print(f"[✓] Graph saved to: {graph_output_path}")
    except Exception as e:
        print(f"[!] Warning: Failed to save graph. {e}")
    
    # Display graph statistics
    print("\n" + "-"*70)
    print("GRAPH STATISTICS")
    print("-"*70)
    stats = builder.get_graph_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Get all node IDs
    node_ids = builder.get_all_node_ids()
    print(f"\n[✓] Graph ready with {len(node_ids)} nodes")
    
    if node_ids:
        # Test extraction with first node
        print("\n" + "-"*70)
        print("TEST: LOCAL CONTEXT EXTRACTION")
        print("-"*70 + "\n")
        
        test_node_id = node_ids[0]
        print(f"[*] Running context extraction test on node: {test_node_id}\n")
        
        context = builder.extract_local_context(test_node_id)
        if context:
            print(context)
            print("\n[✓] Context extraction successful!")
        else:
            print(f"[!] Failed to extract context for node: {test_node_id}")
        
        # Display additional test information
        print("\n" + "-"*70)
        print("AVAILABLE NODES FOR TESTING")
        print("-"*70)
        print(f"Total nodes: {len(node_ids)}")
        print("Sample node IDs:")
        for node_id in node_ids[:5]:
            info = builder.get_node_info(node_id)
            print(f"  • {node_id} ({info['entity_type']}) - In: {info['in_degree']}, Out: {info['out_degree']}")
        
        if len(node_ids) > 5:
            print(f"  ... and {len(node_ids) - 5} more nodes")
    else:
        print("[!] Warning: No nodes found in graph. Check your data contract.")
    
    print("\n" + "="*70)
    print("[SUCCESS] Graph initialization, persistence, and testing complete")
    print("="*70 + "\n")
    
    return 0


if __name__ == "__main__":
    exit(main())
