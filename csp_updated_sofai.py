import re
from solver.s2 import run_degree_of_saturation
import ollama
from ollama import Client
import streamlit as st
from collections import defaultdict
from validator.validator import evaluate_response
import networkx as nx
import matplotlib.pyplot as plt
import random
from utils.example_generator import generate_example
import os

import subprocess
process = subprocess.Popen(["ollama", "serve"])

ollama.pull("mistral")
st.title("CSP-SOFAI Chatbot for Graph Coloring")

# Initialize history
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Initialize model selection
if "model" not in st.session_state:
    st.session_state["model"] = ""

# Fetch available models
# print(ollama.list()['models'][0]['model'])
# raise KeyboardInterrupt
models = [model["model"] for model in ollama.list()["models"]]
st.session_state["model"] = st.selectbox("Choose your model", models)

# problem generator
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
            # Add a random clique (fully connected subgraph) of size 3 or 4
            clique_size = random.choice([3, 4]) if len(nodes) >= 4 else 3
            clique_nodes = random.sample(nodes, clique_size)
            for i in range(clique_size):
                for j in range(i + 1, clique_size):
                    edge = tuple(sorted((clique_nodes[i], clique_nodes[j])))
                    edges.add(edge)

    # Convert edges to string format with each edge on a new line for better readability
    graph_content = "\n\n".join([f"{edge[0]} - {edge[1]}" for edge in sorted(edges)])

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


# Function to preprocess the user input for CSP
# prompt
def preprocess_input(graph_content, min_colors):
    
    user_input = f"""
    **Graph Coloring Problem**

    You are provided with an undirected graph. The graph is represented by vertices and edges connecting them.
    In the examples below, vertices are labeled with letters (e.g., A, B, C), and edges are represented by pairs of vertices (e.g., A - B means there is an edge between vertex A and vertex B).
    
    Use the actual graph provided below for solving the problem:

    
    {graph_content}
    

    You can use at most {min_colors} colors to generate a valid coloring of this graph such that no two adjacent vertices share the same color. **ONLY OUTPUT** the color assignments for each vertex in the following format: (vertex color).
   
    Example format of the output (Note: A, B, C are just examples):

    
    (A 1)
    (B 2)
    (C 1)
    
    
    Use the vertex names from the actual graph content above when generating your solution.**
"""

    return user_input

# Function to process the plan (coloring) response
def process_plan(response):
    re_code = re.compile(r"\(\s*(\w+)\s+(\d+)\s*\)")
    color_assignments = re_code.findall(response)
    formatted_assignments = [(vertex, int(color)) for vertex, color in color_assignments]
    return formatted_assignments

# Function to parse the graph content
def parse_graph(graph_content):
    vertices = set()
    edges = defaultdict(list)

    for line in graph_content.strip().splitlines():
        match = re.match(r"(\w+)\s*-\s*(\w+)", line.strip())
        if match:
            v1, v2 = match.groups()
            vertices.add(v1)
            vertices.add(v2)
            edges[v1].append(v2)
            edges[v2].append(v1)

    return vertices, edges

# Function to generate a response from the model
#  can go under system 1 solver
def model_res_generator():
    stream = ollama.chat(
        model=st.session_state["model"],
        messages=st.session_state["messages"],
        stream=True,
    )
    response = ""
    for chunk in stream:
        response += chunk["message"]["content"]
    return response

def visualize_coloring(vertices, edges, color_assignments, is_correct, feedback):
    G = nx.Graph()
    G.add_nodes_from(vertices)
    for v, neighbors in edges.items():
        for neighbor in neighbors:
            G.add_edge(v, neighbor)
    
    if len(G.nodes) == 0:
        st.error("No vertices found in the graph.")
        return
    
    if len(G.edges) == 0:
        st.warning("No edges found in the graph. Only displaying vertices.")
    
    color_map = {}
    for vertex, color in color_assignments:
        color_map[vertex] = color
    
    unique_colors = sorted(set(color_map.values()))
    color_palette = plt.cm.get_cmap('rainbow', len(unique_colors))
    color_value_map = {color: color_palette(i) for i, color in enumerate(unique_colors)}
    node_colors = [color_value_map[color_map[node]] if node in color_map else (0.5, 0.5, 0.5, 1.0) for node in G.nodes()]
    
    pos = nx.spring_layout(G, seed=42) if len(G.edges) > 0 else nx.circular_layout(G)

    plt.figure(figsize=(8, 8))
    nx.draw(G, pos, with_labels=True, node_color=node_colors, node_size=500, font_size=16)

    if is_correct:
        plt.title("Graph Coloring - Correct Solution", fontsize=20, color='green')
    else:
        plt.title(f"Graph Coloring - {feedback}", fontsize=20, color='red')

    st.pyplot(plt)
    plt.close()

# # Add buttons for feedback type and example type
# feedback_type = st.radio(
#     "Select Feedback Type",
#     ['Right/Wrong', 'Single Mistake', 'All Mistakes']
# )

# example_type = st.radio(
#     "Select Example Type",
#     ['None', 'Pair', 'Triangle', 'Pair and Triangle', 'Clique']
# )

# Create a layout with two columns for the file uploader and the start button
col1, col2 = st.columns([3, 1])

with col1:
    # File upload for the graph definition file
    graph_file = st.file_uploader("Upload Graph File [in DIMACS Format]", type=["txt"])

with col2:
    # Add some padding to center the button vertically
    st.write("")  # Adds an empty line
    st.write("")  # Adds another empty line
    # Button to start without uploading a file
    start_without_file = st.button("Start Without Uploading")

# Check if a file is uploaded or the start button is pressed
if graph_file:
    graph_content = graph_file.read().decode("utf-8")
    dos_coloring = run_degree_of_saturation(graph_content)
    
    # Parse the coloring and determine the highest color number used
    min_colors = 0
    for line in dos_coloring.splitlines():
        parts = re.findall(r'\d+', line)
        if parts:
            color = int(parts[-1])  # Extract the last number in the line, which should be the color
            if color > min_colors:
                min_colors = color

elif start_without_file:
    st.info("No graph file uploaded. Generating a graph...")

    # select the number of nodes for the random graph
    num_nodes = random.randint(4, 6)
    graph_content, min_colors = generate_random_graph(num_nodes)  # Assuming graph_generate() is defined elsewhere to generate a graph
else:
    st.warning("Please upload a file or press 'Start Without Uploading' to proceed.")
    st.stop()

# Parse the graph
vertices, edges = parse_graph(graph_content)

# Preprocess the user input
modified_input = preprocess_input(graph_content, min_colors)

# Add the modified input to the history
st.session_state["messages"].append({"role": "user", "content": modified_input})

# Display the modified input
with st.chat_message("user"):
    st.write(modified_input)

# Initialize a variable to track if the coloring is correct
coloring_correct = False
iteration = 0
max_iterations = 1

# Loop to generate responses and evaluate them
while not coloring_correct and iteration < max_iterations:
    iteration += 1
    with st.chat_message("assistant"):
        # Generate a response from the model
        response = model_res_generator()
        st.session_state["messages"].append(
            {"role": "assistant", "content": response}
        )
        st.markdown(response)

    # Evaluate the response using the validator
    color_assignments = process_plan(response)
    # validators work, to check and obtain feedback.
    coloring_correct, feedback = evaluate_response(response, graph_content, color_assignments)

    # Visualize the coloring
    visualize_coloring(vertices, edges, color_assignments, coloring_correct, feedback)

    if coloring_correct:
        st.success("The above coloring is correct!")
    else:
        # if example_type != "none":
            # example_text = get_example_text(example_type, num_nodes)
            # full_feedback = f"The coloring is not correct. Feedback: {feedback}\n\n{example_text}"
        # else:
        full_feedback = f"Feedback:\n\n{feedback}"
        st.error(f"The above coloring is not correct. Providing feedback:\n\n{full_feedback}")
        st.error("Generating a new coloring ...")
        # Use feedback as the new user prompt
        st.session_state["messages"].append({"role": "user", "content": feedback})

if not coloring_correct:
    st.warning("Reached maximum iterations without a correct coloring.")
    st.info(
        "System 1 solver could not solve the graph coloring problem in 5 turns, so invoking System 2 solver."
    )
    dos_coloring = run_degree_of_saturation(graph_content)
    st.markdown(f"#### Coloring generated by Degree of Saturation algorithm:\n\n```\n{dos_coloring}\n```")
    color_assignments = process_plan(dos_coloring)
    visualize_coloring(vertices, edges, color_assignments, True, "Solution by DSATUR algorithm")
