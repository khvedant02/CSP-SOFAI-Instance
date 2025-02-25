import re

def parse_graph(file_path):
    """
    Parses the graph content from a file in DIMACS format to prepare it for inclusion in a prompt.
    
    Args:
        file_path (str): The file path of the graph data in DIMACS format.
    
    Returns:
        str: A string representation of the graph suitable for prompts, detailing vertices and edges.
    """
    edges = []
    num_vertices = 0
    num_edges = 0

    # Open and read the file
    with open(file_path, 'r') as file:
        lines = file.readlines()

    for line in lines:
        parts = line.strip().split()
        if len(parts) > 0:
            if parts[0] == 'p':
                _, _, num_vertices, num_edges = parts
            elif parts[0] == 'e' and len(parts) == 3:
                _, v1, v2 = parts
                edges.append(f"{v1} {v2}")

    # Preparing the string to be added to the prompt
    graph_description = f"p edge {num_vertices} {num_edges}\n" + "\n".join(f"e {edge}" for edge in edges)
    return graph_description, num_edges, num_vertices

def process_plan(response):
    """
    Parses the LLM response to extract the coloring assignments from potentially mixed content.
    
    Args:
        response (str): The string response from the LLM, potentially including irrelevant text alongside vertex-color pairs.
        
    Returns:
        dict: A dictionary with vertices as keys and their assigned colors as values.
    """
    coloring_assignment = {}
    lines = response.strip().split('\n')
    pattern = re.compile(r"\((\w+)\s+(\d+)\)")  # Regex to capture the vertex-color pair in the format (vertex color)

    for line in lines:
        line = line.strip()
        match = pattern.match(line)
        if match:
            vertex, color = match.groups()
            coloring_assignment[vertex] = int(color)  # Convert color to integer and store

    return coloring_assignment

def print_aesthetic(message, symbol='=', length=50):
    """
    Prints a message in a nicely formatted way.

    Args:
    message (str): The message to print.
    symbol (str): The symbol used for the border. Default is '='.
    length (int): The length of the border. Default is 50.
    """
    border = symbol * length
    print(f"\n{border}\n{message}\n{border}\n")

def save_run_to_file(filepath, content):
    """
    Appends a piece of content to a file.

    Args:
    filepath (str): The path to the file where the content will be saved.
    content (str): The content to save.
    """
    with open(filepath, "a") as file:
        file.write(content + "\n")

# Optional: If you plan to use this module as a script, you can include example usage here.
if __name__ == "__main__":
    # Example of how these functions might be used:
    # graph_info = "Vertices: A, B, C, D; Edges: (A-B), (B-C), (C-D), (D-A)"
    # input_prep = preprocess_input(graph_info, 3)
    print_aesthetic("Example Graph Coloring Input Preparation")
    print(input_prep)
    save_run_to_file("example_output.txt", input_prep)