import os
import time
import ollama
import pickle
import json
import argparse
import signal
from utils.episodic_memory import EpisodicMemory
from validator.validator_graphcoloring import GraphColoringValidator
from utils.improvement_trend_evaluator import ImprovementTrendEvaluator
from utils.example_generator import GraphColoringExampleGenerator
from solver.s2_graphcoloring import run_degree_of_saturation
from utils.prompt_generator import prompt_generator
from utils.util_functions import parse_graph, process_plan, save_run_to_file


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
    return result, False

def main():
    parser = argparse.ArgumentParser(description="CSP Solver Benchmarking")
    parser.add_argument("--model", type=str, required=True, help="Name of the model to use")
    parser.add_argument("--data_file", type=str, required=True, help="Filename to load the generated data")
    parser.add_argument("--output_file", type=str, required=True, help="Filename to save the detailed output")
    parser.add_argument("--summary_file", type=str, required=True, help="Filename to save the summary output")
    args = parser.parse_args()

    results_dir = "results"
    summary_dir = "summary"
    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(summary_dir, exist_ok=True)

    output_filepath = os.path.join(results_dir, args.output_file)
    summary_filepath = os.path.join(summary_dir, args.summary_file)

    data_list = pickle.load(open(args.data_file, "rb"))
    episodic_memory = EpisodicMemory()
    example_generator = GraphColoringExampleGenerator()
    trend_evaluator = ImprovementTrendEvaluator()

    summary_fields = 'Graph Size,Example Number,min_colors,s1_Solved,s2_solved,Iterations,Num Edges,s2_invoked,time_s1,time_s2,time_sofai\n'
    with open(summary_filepath, 'w') as f_summary:
        f_summary.write(summary_fields)

        for example_index, json_obj in enumerate(data_list):
            file_path = json_obj['file']
            min_colors = json_obj['min_color']
            file_path = file_path.replace("/work/vedant/2024/final_cpde/coling-CODE/","")
            # print(file_path)
            graph_content,num_edges,num_vertices = parse_graph(file_path)
            print(graph_content)
            print(f"Starting example {example_index}: {min_colors} colors needed for {num_edges} edges.")

            if episodic_memory.memory:
                print("Episodic memory loaded.")
                top_examples = episodic_memory.retrieve_similar(graph_content)
                initial_prompt = prompt_generator(graph_content, min_colors, additional_examples=top_examples)
            else:
                print("No episodic memory found.")
                initial_prompt = prompt_generator(graph_content, min_colors)

            messages = [{"role": "user", "content": initial_prompt}]
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
                response = model_res_generator(args.model, messages)
                print("message sent to model")
                # print(response)
                s1_time = time.time() - s1_start_time
                messages.append({"role": "assistant", "content": response})
                print(f"Iteration {iteration} complete. LLM responded in {s1_time:.2f} seconds.")

                color_assignments = process_plan(response)
                print(color_assignments)
                validator = GraphColoringValidator(file_path)
                coloring_correct, feedback = validator.validate_coloring(color_assignments)
                # print(feedback)
                # check if errors is not empty
                if feedback:
                    feedback = "Adjacent vertices are colored same : " + ", ".join(feedback)
                        
                if coloring_correct:
                    s1_solved = True
                    episodic_memory.add_memory(graph_content, response)
                    save_run_to_file(output_filepath, f"Problem solved in {iteration} iterations.")
                    print("Problem solved by S1.")
                    break

                trend_evaluator.update_feedback(feedback)
                if iteration == max_iterations or trend_evaluator.get_no_improvement_flag():
                    s2_start_time = time.time()
                    dos_result, timeout_occurred = run_s2_with_timeout(graph_content)
                    if not timeout_occurred:
                        dos_coloring, chromatic_number = dos_result
                        s2_time = time.time() - s2_start_time
                        s2_solved = True
                        episodic_memory.add_memory(graph_content, dos_coloring)
                        save_run_to_file(output_filepath, "Solved by System 2.")
                        print(f"S2 solved the problem in {s2_time:.2f} seconds.")
                    break

                if not coloring_correct and not timeout_occurred:
                    subgraph, example_coloring = example_generator.generate_example(graph_content)
                    full_feedback = f"Feedback: {feedback}. Example: {example_coloring}"
                    messages.append({"role": "user", "content": full_feedback})

            sofai_time = time.time() - start_time
            summary_line = f"{num_vertices},{example_index},{min_colors},{s1_solved},{s2_solved},{iteration},{num_edges},{s2_solved},{s1_time},{0 if timeout_occurred else s2_time if s2_solved else 0},{sofai_time}\n"
            f_summary.write(summary_line)
            print("Summary updated for current example.")

if __name__ == "__main__":
    main()