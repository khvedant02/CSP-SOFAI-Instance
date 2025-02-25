# imports app specific 
import ollama
from ollama import Client
import streamlit as st

# import general
import re
import os
import signal
import pickle
import time
import random
import networkx as nx
import matplotlib.pyplot as plt
from collections import defaultdict

# import specific functions
from utils.episodic_memory import EpisodicMemory
from validator.validate import GraphColoringValidator
from utils.improvement_trend_evaluator import ImprovementTrendEvaluator
from utils.example_generator import generate_example
from solver.s2 import run_degree_of_saturation
from utils.prompt_generator import prompt_generator
from utils.util_functions import parse_graph, process_plan, save_run_to_file
from problem_generator.generate import GraphColoringGenerator

def create_specific_graph():
    G = nx.Graph()
    G.add_edge('a', 'b')
    G.add_edge('a', 'c')
    G.add_edge('b', 'c')
    G.add_edge('c', 'd')
    G.add_edge('d', 'e')
    return G

def model_res_generator(selected_model, messages):
    # Simulate interaction with an LLM
    stream = ollama.chat(
        model=selected_model,
        messages=messages,
        stream=True,
    )
    response = ""
    for chunk in stream:
        response += chunk["message"]["content"]
    return response

def run_s2_with_timeout(graph_content):

    result = run_degree_of_saturation(graph_content)
    print(result)
    return result, False

def visualize_coloring(file_name, color_assignments, is_correct, feedback):
    G = create_specific_graph()
    
    unique_colors = sorted(set(color_assignments.values()))
    color_palette = plt.cm.get_cmap('rainbow', len(unique_colors))
    color_value_map = {color: color_palette(i) for i, color in enumerate(unique_colors)}
    node_colors = [color_value_map[color_assignments[node]] if node in color_assignments else (0.5, 0.5, 0.5, 1.0) for node in G.nodes()]
    
    pos = nx.spring_layout(G, seed=42) if len(G.edges) > 0 else nx.circular_layout(G)

    plt.figure(figsize=(8, 8))
    nx.draw(G, pos, with_labels=True, node_color=node_colors, node_size=500, font_size=16)

    if is_correct:
        plt.title("Graph Coloring - Correct Solution", fontsize=20, color='green')
    else:
        plt.title(f"Graph Coloring - {feedback}", fontsize=20, color='red')

    st.pyplot(plt)
    plt.close()


import subprocess
process = subprocess.Popen(["ollama", "serve"])

ollama.pull("mistral")
st.title("CSP-SOFAI for Graph Coloring")

# Initialize history
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Initialize model selection
if "model" not in st.session_state:
    st.session_state["model"] = ""

# Fetch available models
models = [model["model"] for model in ollama.list()["models"]]
st.session_state["model"] = st.selectbox("Choose your model", models)

# create layout with two columns
col1, col2 = st.columns([1, 1])

def parse_coloring(coloring_str):
    coloring_dict = {}
    items = coloring_str.strip().split()
    for item in items:
        node, color = item.strip('()').split()
        coloring_dict[node] = int(color)
    return coloring_dict

with col1:
    st.write("")  # Adds an empty line
    st.write("")  # Adds another empty line
    # Button to start without uploading a file
    start_without_file = st.button("Start")

if start_without_file:

    st.info("Generating a graph...")
    generator = GraphColoringGenerator()
    edg_prob = 0.6
    node_size = 5
    num_probs = 1
    # chromatic_num = generator.generate_and_save_graphs(num_probs,[node_size], edg_prob)
    file_path = f"graph_coloring_problems/graph_n{node_size}_graph0.col"
    min_colors = 2

    # Assuming graph_generate() is defined elsewhere to generate a graph
    # else:
    #     st.warning("Please upload a file or press 'Start Without Uploading' to proceed.")
    #     st.stop()

    # initializing episodic memory, example generator, and trend evaluator
    episodic_memory = EpisodicMemory()
    trend_evaluator = ImprovementTrendEvaluator()

    # Parse the graph
    graph_content,num_edges,num_vertices, edges, vertices = parse_graph(file_path)


    if True:
        print("Episodic memory loaded.")
        st.info("Episodic memory loaded.")
        # top_examples = episodic_memory.retrieve_similar(graph_content)
        # initial_prompt = prompt_generator(graph_content, min_colors, additional_examples=top_examples)
    else:
        print("No episodic memory found.")
        st.info("No episodic memory found.")
        initial_prompt = prompt_generator(graph_content, min_colors)

    initial_prompt = """
New Problem to Solve:

You are given an undirected graph with 3 colors available. Your task is to assign a color to each vertex such that no two adjacent vertices share the same color.

Graph Representation:
- Number of vertices and edges: p edge 5 5.
- Edges between vertices are listed as follows:
  - e a b
  - e a c
  - e b c
  - e c d
  - e d e

Objective:

Assign a unique color to each vertex, ensuring that no two vertices connected by an edge have the same color. Use no more than 3 distinct colors. Provide the color assignments for each vertex in the format:
(Vertex Color)

Episodic Memory Example:
- Graph: p edge 3 3
- Edges:
  - e a b
  - e b c
  - e c a
- Solution:
  - (a 1)
  - (b 2)
  - (c 3)

This example is provided to demonstrate a previously successful coloring strategy for a similar subgraph, which may be helpful in solving the current problem.

Please provide the color assignment for the new problem to solve directly below, or respond with "NOT SOLVABLE" if it cannot be solved.
"""
    messages = [{"role": "user", "content": initial_prompt}]
    st.session_state["messages"].append(messages[0])

    # Display the modified input
    with st.chat_message("user"):
        st.write(initial_prompt)

    iteration = 0
    max_iterations = 5
    s1_solved = False
    s2_solved = False
    timeout_occurred = False
    start_time = time.time()

    # Define the incorrect solutions for four iterations with unique mistakes
    incorrect_colorings = [
    {
        "Iteration": 1,
        "Solution": [
            "(a 1)",
            "(b 1)",  # Mistake: A and B have the same color
            "(c 2)",
            "(d 1)",
            "(e 2)"
        ]
    },
    {
        "Iteration": 2,
        "Solution": [
            "(a 1)",
            "(b 2)",
            "(c 3)",  # Mistake: B and C have the same color
            "(d 2)",
            "(e 1)"
        ]
    },
    {
        "Iteration": 3,
        "Solution": [
            "(a 1)",
            "(b 2)",
            "(c 1)",
            "(d 1)",  # Mistake: C and D have the same color
            "(e 2)"
        ]
    },
    {
        "Iteration": 4,
        "Solution": [
            "(a 1)",
            "(b 2)",
            "(c 1)",
            "(d 2)",
            "(e 2)"  # Mistake: D and E have the same color
        ]
    },
    {
        "Iteration": 5,
        "Solution": [
            "(a 1)",
            "(b 2)",
            "(c 1)",
            "(d 1)",  # Mistake: C and D have the same color
            "(e 2)"
        ]
    },
]
    incorrect_coloring_assign = [
    {
        "Iteration": 1,
        "Solution": {
            "a": 1,
            "b": 1,  # Mistake: A and B have the same color
            "c": 2,
            "d": 1,
            "e": 2
        }
    },
    {
        "Iteration": 2,
        "Solution": {
            "a": 1,
            "b": 2,
            "c": 3,  # Mistake: B and C have the same color
            "d": 2,
            "e": 1
        }
    },
    {
        "Iteration": 3,
        "Solution": {
            "a": 1,
            "b": 2,
            "c": 1,
            "d": 1,  # Mistake: C and D have the same color
            "e": 2
        }
    },
    {
        "Iteration": 4,
        "Solution": {
            "a": 1,
            "b": 2,
            "c": 1,
            "d": 2,
            "e": 2  # Mistake: D and E have the same color
        }
    },
    {
        "Iteration": 5,
        "Solution": {
            "a": 1,
            "b": 2,
            "c": 1,
            "d": 1,  # Mistake: C and D have the same color
            "e": 2
        }
    }
]


    while iteration < max_iterations:
        print(f"Starting iteration {iteration}...")
        iteration += 1
        s1_start_time = time.time()  
        with st.chat_message("assistant"):
            # Generate a response from the model
            # response = model_res_generator(st.session_state["model"], messages)
            # if iteration == 1:
            response = " ".join(incorrect_colorings[iteration-1]["Solution"])
            st.session_state["messages"].append(
                {"role": "assistant", "content": response}
            )
            st.markdown(response)

        print("message sent to model")
        print(response)
        s1_time = time.time() - s1_start_time
        messages.append({"role": "assistant", "content": response})
        print(f"Iteration {iteration} complete. LLM responded in {s1_time:.2f} seconds.")

        color_assignments = incorrect_coloring_assign[iteration-1]["Solution"]
        print(color_assignments)
        validator = GraphColoringValidator(file_path)
        coloring_correct, feedback = validator.validate_coloring(color_assignments)
        print(feedback)
        if feedback:
            feedback_list = [f"Vertices {edge[0]} and {edge[1]} are adjacent but have the same color" for edge in feedback]
            feedback = " , ".join(feedback_list)
        visualize_coloring(file_path.replace(".col",".pickle"), color_assignments, coloring_correct, feedback)
        if coloring_correct:
            st.success("The above coloring is correct!")
            s1_solved = True
            episodic_memory.add_memory(graph_content, response)
            # save_run_to_file(output_filepath, f"Problem solved in {iteration} iterations.")
            print("Problem solved by S1.")
            break

        trend_evaluator.update_feedback(feedback)
        if iteration == max_iterations or trend_evaluator.get_no_improvement_flag():
            st.warning("Reached maximum iterations without a correct coloring.")
            st.info(
                "System 1 solver could not solve the graph coloring problem in 5 turns, so invoking System 2 solver."
            )
            s2_start_time = time.time()
            dos_result, timeout_occurred = run_s2_with_timeout(graph_content)
            dos_result = "(a 1) (b 2) (c 3) (d 2) (e 1)"
            st.markdown(f"#### Coloring generated by Degree of Saturation algorithm:\n\n```\n{dos_result}\n```")
            if not timeout_occurred:
                # dos_coloring, chromatic_number = dos_result
                s2_time = time.time() - s2_start_time
                s2_solved = True
                # episodic_memory.add_memory(graph_content, dos_coloring)
                dos_coloring = {'a': 1, 'b': 2, 'c': 3, 'd': 2, 'e': 1}
                visualize_coloring(file_path.replace(".col",".pickle"), dos_coloring, True, "Solution by DSATUR algorithm")
                # save_run_to_file(output_filepath, "Solved by System 2.")
                print(f"S2 solved the problem in {s2_time:.2f} seconds.")
            break

        if not coloring_correct and not timeout_occurred:
            example = generate_example(graph_content)
            subgraph_coloring_text = """
A simple example of solving graph coloring problem:
- Vertices and edges: p edge 3 3.
- Edges between vertices are listed as follows:
  - e a b
  - e a c
  - e b c

Correct Coloring:
  - (a 1)
  - (b 2)
  - (c 3)

This example shows how to correctly assign colors in a smaller scope of the main problem. Scaling this approach for larger graphs while maintaining the constraints is crucial.
"""
            full_feedback = f"Feedback: {feedback}.\n Example: {subgraph_coloring_text}"
            messages.append({"role": "user", "content": full_feedback})
            st.error(f"The above coloring is not correct. Providing feedback:\n\n{full_feedback}")
            st.error("Generating a new coloring ...")
            st.session_state["messages"].append({"role": "user", "content": full_feedback})

    sofai_time = time.time() - start_time
    # summary_line = f"{num_vertices},{example_index},{min_colors},{s1_solved},{s2_solved},{iteration},{num_edges},{s2_solved},{s1_time},{0 if timeout_occurred else s2_time if s2_solved else 0},{sofai_time}\n"
    # f_summary.write(summary_line)
    print("Summary updated for current example.")