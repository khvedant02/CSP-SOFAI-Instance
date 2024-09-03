import re
from collections import defaultdict

def evaluate_response(response, graph_content, color_assignments, feedback_type="direct"):
    """
    Validates the coloring of the graph and provides feedback.
    
    :param response: The color assignments generated by the model or fallback solver.
    :param graph_content: The original graph definition as a string.
    :param color_assignments: List of tuples with color assignments (vertex, color).
    :param feedback_type: Type of feedback ("direct", "withone", "withall").
    :return: A tuple (is_valid, feedback_message).
    """

    # Create a dictionary to store the color assignments
    vertex_colors = {vertex: color for vertex, color in color_assignments}

    # Parse the graph to get edges
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

    # Initialize feedback variables
    is_valid = True
    feedback_messages = []
    checked_pairs = set()  # Set to track checked pairs

    # Check for missing vertices in color assignments
    missing_vertices = vertices - vertex_colors.keys()
    if missing_vertices:
        is_valid = False
        feedback_messages.append(f"Vertices {', '.join(missing_vertices)} are not colored.")
        if feedback_type == "Single Mistake" or feedback_type=="Single_Mistake":
            return False, feedback_messages[0]

    # Validate the coloring for the provided vertices
    for v1, neighbors in edges.items():
        if v1 not in vertex_colors:
            continue

        for v2 in neighbors:
            if v2 not in vertex_colors:
                feedback_messages.append(f"Vertex {v2} is not colored.")
                is_valid = False
                if feedback_type == "Single Mistake" or feedback_type == "Single_Mistake": 
                    return False, feedback_messages[0]
                continue

            # Check if this pair has already been checked
            if (v1, v2) in checked_pairs or (v2, v1) in checked_pairs:
                continue

            # Add the pair to the checked set
            checked_pairs.add((v1, v2))

            if vertex_colors[v1] == vertex_colors[v2]:
                is_valid = False
                feedback_messages.append(
                    f"Vertices {v1} and {v2} are adjacent and share the same color {vertex_colors[v1]}."
                )
                if feedback_type == "Single Mistake" or feedback_type == "Single_Mistake":
                    return False, feedback_messages[0]

    # Prepare the feedback based on the feedback_type
    if is_valid:
        return True, "The coloring is valid."

    if feedback_type == "Right/Wrong" or feedback_type == "Right_Wrong":
        return False, "The coloring is invalid."

    if feedback_type == "Single Mistake" or feedback_type == "Single_Mistake":
        return False, feedback_messages[0]

    if feedback_type == "All Mistakes" or feedback_type == "All_Mistakes":
        return False, "\n".join(feedback_messages)