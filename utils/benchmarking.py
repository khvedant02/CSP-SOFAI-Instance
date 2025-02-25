import os
import re
import argparse
import time
import pickle
from s2solver import run_degree_of_saturation
import ollama
from collections import defaultdict
from validator import evaluate_response
import json
from example_generate import get_example_text



def process_plan(response):
    re_code = re.compile(r"\(\s*(\w+)\s+(\d+)\s*\)")
    color_assignments = re_code.findall(response)
    formatted_assignments = [(vertex, int(color)) for vertex, color in color_assignments]
    return formatted_assignments

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

def model_res_generator(selected_model, messages):
    stream = ollama.chat(
        model=selected_model,
        messages=messages,
        stream=True,
    )
    response = ""
    for chunk in stream:
        response += chunk["message"]["content"]
    return response

def save_run_to_file(filepath, content):
    with open(filepath, "a") as file:
        file.write(content + "\n")

def print_aesthetic(message, symbol="=", length=50):
    border = symbol * length
    print(f"\n{border}\n{message}\n{border}\n")

def save_checkpoint(checkpoint_file, data):
    with open(checkpoint_file, 'wb') as f:
        pickle.dump(data, f)

def load_checkpoint(checkpoint_file):
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, 'rb') as f:
            return pickle.load(f)
    return None

def main():
    # Argument parser
    parser = argparse.ArgumentParser(description="CSP Solver Benchmarking")
    parser.add_argument("--model", type=str, required=True, help="Name of the model to use")
    parser.add_argument("--feedback_type", type=str, choices=["Right_Wrong", "Single_Mistake", "All_Mistakes"], default="direct", help="Type of feedback to provide")
    parser.add_argument("--example_type", type=str, choices=["none", "pair", "triangle", "pairntriangle", "clique"], default="none", help="Type of example to provide")
    parser.add_argument("--graph_size", type=int, required=True, help="Number of nodes in the graph")
    parser.add_argument("--data_file", type=str, required=True, help="Filename to load the generated data")
    parser.add_argument("--num_examples", type=int, default=1, help="Number of examples to generate and run")
    parser.add_argument("--output_file", type=str, required=True, help="Filename to save the detailed output")
    parser.add_argument("--summary_file", type=str, required=True, help="Filename to save the summary output")
    
    args = parser.parse_args()

    # Create results and summary directories if they don't exist
    results_dir = "results"
    summary_dir = "summary"
    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(summary_dir, exist_ok=True)

    # Update paths with directories
    output_filepath = os.path.join(results_dir, args.output_file)
    summary_filepath = os.path.join(summary_dir, args.summary_file)
    checkpoint_file = "args.pkl"

    # Load data from checkpoint if available, otherwise create a new one
    checkpoint = load_checkpoint(checkpoint_file)
    if checkpoint:
        if (checkpoint['feedback_type'] == args.feedback_type and
            checkpoint['example_type'] == args.example_type and
            checkpoint['graph_size'] == args.graph_size):
            start_example = checkpoint['current_example']
            print(f"Resuming from Example {start_example} for feedback '{args.feedback_type}', example '{args.example_type}', and graph size '{args.graph_size}'.")
        else:
            start_example = 0
    else:
        start_example = 0
        # Create a new checkpoint
        checkpoint_data = {
            'feedback_type': args.feedback_type,
            'example_type': args.example_type,
            'graph_size': args.graph_size,
            'current_example': start_example,
        }
        save_checkpoint(checkpoint_file, checkpoint_data)

    with open(args.data_file, 'r') as f:
        data = json.load(f)

    for example_index, json_obj in enumerate(data[start_example:], start=start_example):
        start_time = time.time()
        graph_content = json_obj['graph']
        min_colors = json_obj['color']
        vertices, edges = parse_graph(graph_content)
        num_edges = sum(len(adj_list) for adj_list in edges.values()) // 2

        # Save checkpoint data
        checkpoint_data = {
            'feedback_type': args.feedback_type,
            'example_type': args.example_type,
            'graph_size': args.graph_size,
            'current_example': example_index,
        }
        save_checkpoint(checkpoint_file, checkpoint_data)

        # Save initial content
        save_run_to_file(output_filepath, f"Example {example_index:03}:")
        save_run_to_file(output_filepath, f"Graph Content:\n{graph_content}")

        # Preprocess the user input
        modified_input = preprocess_input(graph_content, min_colors)
        save_run_to_file(output_filepath, f"User Prompt:\n{modified_input}")
        messages = [{"role": "user", "content": modified_input}]

        # Initialize a variable to track if the coloring is correct
        coloring_correct = False
        iteration = 0
        max_iterations = 5

        # Loop to generate responses and evaluate them
        while not coloring_correct and iteration < max_iterations:
            iteration += 1
            print_aesthetic(f"Iteration {iteration}", symbol="*")

            # Generate a response from the model
            response = model_res_generator(args.model, messages)
            messages.append({"role": "assistant", "content": response})

            save_run_to_file(output_filepath, f"Iteration {iteration} Response:\n{response}")
            
            # Evaluate the response using the validator
            color_assignments = process_plan(response)
            coloring_correct, feedback = evaluate_response(response, graph_content, color_assignments, feedback_type=args.feedback_type)

            if not coloring_correct:
                # If the model fails, add an example and the feedback to the prompt
                if args.example_type != "none":
                    example_text = get_example_text(args.example_type, args.graph_size)
                    full_feedback = f"The coloring is not correct. Feedback: {feedback}\n{example_text}"
                    save_run_to_file(output_filepath, f"User Prompt:\n{full_feedback}")
                else:
                    full_feedback = f"Feedback:\n{feedback}"

                # Use the example (if any) and feedback as the new prompt
                messages.append({"role": "user", "content": full_feedback})
                save_run_to_file(output_filepath, f"User Prompt:\n{full_feedback}")
            else:
                save_run_to_file(output_filepath, f"Example {example_index:03} - The coloring is correct!")

        if not coloring_correct:
            save_run_to_file(output_filepath, "Not Solved by S1. Going to S2.")
            print_aesthetic("Invoking System 2 solver (Degree of Saturation algorithm).", symbol="^")
            s1_time = time.time() - start_time
            s2_start_time = time.time()
            dos_coloring = run_degree_of_saturation(graph_content)
            s2_time = time.time() - s2_start_time
            
            print(dos_coloring)
            save_run_to_file(output_filepath, f"Solved Output:\n{dos_coloring}")
            save_run_to_file(summary_filepath, f"Example {example_index:03}: Solved: False, Iterations: {iteration}, Feedback: {args.feedback_type}, Example: {args.example_type}, Num Edges: {num_edges}, S1 Time: {s1_time:.2f}s, S2 Invoked: Yes, S2 Time: {s2_time:.4f}s")
        else:
            s1_time = time.time() - start_time
            s2_time = 0
            save_run_to_file(summary_filepath, f"Example {example_index:03}: Solved: True, Iterations: {iteration}, Feedback: {args.feedback_type}, Example: {args.example_type}, Num Edges: {num_edges}, S1 Time: {s1_time:.2f}s, S2 Invoked: No, S2 Time: {s2_time:.4f}s")

        # Add a visual marker to indicate the end of the example
        save_run_to_file(output_filepath, "-" * 50)

        # Remove checkpoint if example is fully processed
        if os.path.exists(checkpoint_file):
            os.remove(checkpoint_file)

if __name__ == "__main__":
    main()
