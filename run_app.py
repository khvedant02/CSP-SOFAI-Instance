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
    G = pickle.load(open(file_name, "rb"))
    
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
    chromatic_num = generator.generate_and_save_graphs(num_probs,[node_size], edg_prob)
    file_path = f"graph_coloring_problems/graph_n{node_size}_graph0.col"
    min_colors = chromatic_num[file_path]

    # Assuming graph_generate() is defined elsewhere to generate a graph
    # else:
    #     st.warning("Please upload a file or press 'Start Without Uploading' to proceed.")
    #     st.stop()

    # initializing episodic memory, example generator, and trend evaluator
    episodic_memory = EpisodicMemory()
    trend_evaluator = ImprovementTrendEvaluator()

    # Parse the graph
    graph_content,num_edges,num_vertices, edges, vertices = parse_graph(file_path)


    if episodic_memory.memory:
        print("Episodic memory loaded.")
        top_examples = episodic_memory.retrieve_similar(graph_content)
        initial_prompt = prompt_generator(graph_content, min_colors, additional_examples=top_examples)
    else:
        print("No episodic memory found.")
        initial_prompt = prompt_generator(graph_content, min_colors)

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

    while iteration < max_iterations:
        print(f"Starting iteration {iteration}...")
        iteration += 1
        s1_start_time = time.time()  
        with st.chat_message("assistant"):
            # Generate a response from the model
            response = model_res_generator(st.session_state["model"], messages)
            st.session_state["messages"].append(
                {"role": "assistant", "content": response}
            )
            st.markdown(response)

        print("message sent to model")
        # print(response)
        s1_time = time.time() - s1_start_time
        messages.append({"role": "assistant", "content": response})
        print(f"Iteration {iteration} complete. LLM responded in {s1_time:.2f} seconds.")

        color_assignments = process_plan(response)
        print(color_assignments)
        validator = GraphColoringValidator(file_path)
        coloring_correct, feedback = validator.validate_coloring(color_assignments)
        print(feedback)
        if feedback:
            feedback_list = [f"adjacent vertices {edge[0]} and {edge[1]} have the same color" for edge in feedback]
            feedback = " : ".join(feedback_list)
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
            st.markdown(f"#### Coloring generated by Degree of Saturation algorithm:\n\n```\n{dos_result}\n```")
            if not timeout_occurred:
                dos_coloring, chromatic_number = dos_result
                s2_time = time.time() - s2_start_time
                s2_solved = True
                episodic_memory.add_memory(graph_content, dos_coloring)
                visualize_coloring(file_path.replace(".col",".pickle"), color_assignments, True, "Solution by DSATUR algorithm")
                # save_run_to_file(output_filepath, "Solved by System 2.")
                print(f"S2 solved the problem in {s2_time:.2f} seconds.")
            break

        if not coloring_correct and not timeout_occurred:
            example = generate_example(graph_content)
            full_feedback = f"Feedback: {feedback}. Example: {example}"
            messages.append({"role": "user", "content": full_feedback})
            st.error(f"The above coloring is not correct. Providing feedback:\n\n{full_feedback}")
            st.error("Generating a new coloring ...")
            st.session_state["messages"].append({"role": "user", "content": full_feedback})

    sofai_time = time.time() - start_time
    # summary_line = f"{num_vertices},{example_index},{min_colors},{s1_solved},{s2_solved},{iteration},{num_edges},{s2_solved},{s1_time},{0 if timeout_occurred else s2_time if s2_solved else 0},{sofai_time}\n"
    # f_summary.write(summary_line)
    print("Summary updated for current example.")