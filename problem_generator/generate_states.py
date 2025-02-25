import random
import re
from s2solver import run_degree_of_saturation
import json 
import argparse

def generate_random_graph(num_nodes):
    """
    Generate a random undirected graph with the specified number of nodes, incorporating randomized complexities
    to make it challenging for an LLM to solve.

    :param num_nodes: Number of nodes in the graph.
    :return: A tuple containing a string representation of the graph and the minimum number of colors required to solve it.
    """
    if num_nodes < 2:
        raise ValueError("Number of nodes must be at least 2")

    # Generate a random set of unique characters for the nodes
    possible_chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    nodes = random.sample(possible_chars, num_nodes)
    edges = set()

    # Start by creating a basic connected structure (e.g., a chain)
    for i in range(num_nodes - 1):
        edge = (nodes[i], nodes[i + 1])
        edges.add(edge)

    # Randomly decide whether and how to add complexity
    max_possible_edges = num_nodes * (num_nodes - 1) // 2
    additional_edges = random.randint(0, max_possible_edges - len(edges))  # Randomly decide how many extra edges to add

    for _ in range(additional_edges):
        operation = random.choice(['add_edge', 'add_triangle', 'add_clique'])

        if operation == 'add_edge':
            # Add a random edge
            node1, node2 = random.sample(nodes, 2)
            edge = tuple(sorted((node1, node2)))
            if edge not in edges:
                edges.add(edge)

        elif operation == 'add_triangle':
            # Add a random triangle (three interconnected nodes)
            if len(nodes) >= 3:
                node1, node2, node3 = random.sample(nodes, 3)
                triangle_edges = {(node1, node2), (node2, node3), (node1, node3)}
                edges.update(triangle_edges)

        elif operation == 'add_clique':
            # Add a random clique (fully connected subgraph) of any size
            clique_size = random.choice([i for i in range(2, num_nodes-2)])
            clique_nodes = random.sample(nodes, clique_size)
            for i in range(clique_size):
                for j in range(i + 1, clique_size):
                    edge = tuple(sorted((clique_nodes[i], clique_nodes[j])))
                    edges.add(edge)

    # Convert edges to string format
    graph_content = "\n".join([f"{edge[0]} - {edge[1]}" for edge in sorted(edges)])

    # Solve the graph using the Degree of Saturation (S2) solver to determine the minimum number of colors required
    dos_coloring = run_degree_of_saturation(graph_content)
    
    # Parse the coloring and determine the highest color number used
    min_colors = 0
    for line in dos_coloring.splitlines():
        parts = re.findall(r'\d+', line)
        if parts:
            color = int(parts[-1])  # Extract the last number in the line, which should be the color
            if color > min_colors:
                min_colors = color
    
    return graph_content, min_colors

def main():
    parser = argparse.ArgumentParser(description="Generate graph and determine minimum number of colors required.")
    parser.add_argument('num_nodes', type=int, help='Number of nodes in the graph')
    parser.add_argument('num_examples', type=int, help='Number of examples to generate')
    args = parser.parse_args()

    results = []
    for _ in range(args.num_examples):
        graph_content, min_colors = generate_random_graph(args.num_nodes)
        results.append({
            "graph": graph_content,
            "color": min_colors
        })

    filename = f"data/graph_{args.num_nodes}_examples_{args.num_examples}.json"
    with open(filename, 'w') as f:
        json.dump(results, f, indent=4)

if __name__ == "__main__":
    main()