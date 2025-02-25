import random
import networkx as nx


def generate_example(graph_content):
    """
    Generates a subgraph coloring example from the given graph.
    
    Args:
        full_graph (nx.Graph): The full graph from which to generate a subgraph and its coloring.
    
    Returns:
        str: A formatted string representing the subgraph and its coloring.
    """
    print(graph_content)
    G = nx.Graph()
    lines = graph_content.strip().split('\n')
    for line in lines:
        parts = line.split()
        if parts[0] == 'e':
            G.add_edge(parts[1], parts[2])
    # Create a subgraph by randomly selecting a subset of nodes
    nodes = list(G.nodes())
    if len(nodes) > 2:
        subgraph_nodes = random.sample(nodes, max(3, len(nodes) // 2))  # At least 3 nodes, or half the nodes
    else:
        subgraph_nodes = nodes  # If not enough nodes, use all nodes

    subgraph = G.subgraph(subgraph_nodes).copy()
    
    # Provide a simple coloring solution using a greedy algorithm
    coloring = nx.coloring.greedy_color(subgraph, strategy='largest_first')
    
    # Format the subgraph in DIMACS format
    dimacs_format = "c A simple example of solving graph coloring problem:\n"
    dimacs_format += f"p edge {len(subgraph.nodes())} {len(subgraph.edges())}\n"
    for edge in subgraph.edges():
        dimacs_format += f"e {edge[0]} {edge[1]}\n"
    
    # Format the coloring
    coloring_format = " ".join([f"({node} {color})" for node, color in coloring.items()])
    
    return dimacs_format + coloring_format
