def get_example_text(example_type, graph_size):
    """
    Generates example text based on the specified example type and graph size.

    :param example_type: Type of example to provide ('none', 'pair', 'triangle', 'pair+triangle', 'clique').
    :param graph_size: Size of the graph.
    :return: A string containing the example text.
    """
    if example_type == "none" or example_type == "None":
        return ""

    elif example_type == "pair" or example_type == "Pair":
        return """
        For example, consider a graph coloring problem for two connected nodes, A and B. To color these nodes, 
        assign a different color to each one. For instance, A can be colored with color 1, and B with color 2. 
        This ensures that no two adjacent nodes share the same color.

        Example:
        (A 1)
        (B 2)
        """

    elif example_type == "triangle" or example_type == "Triangle":
        if graph_size > 7:
            return """
            For example, consider a graph coloring problem for four nodes, A, B, C, and D, all connected to each 
            other (forming a fully connected quadrilateral). To color these nodes, assign different colors to each one. 
            For instance, A can be colored with color 1, B with color 2, C with color 3, and D with color 4. 
            This ensures that no two adjacent nodes share the same color.

            Example:
            (A 1)
            (B 2)
            (C 3)
            (D 4)
            """
        else:
            return """
            For example, consider a graph coloring problem for three nodes, A, B, and C, all connected to each 
            other (forming a triangle). To color these nodes, assign different colors to each one. For instance, 
            A can be colored with color 1, B with color 2, and C with color 3. This ensures that no two adjacent 
            nodes share the same color.

            Example:
            (A 1)
            (B 2)
            (C 3)
            """

    elif example_type == "pairntriangle" or example_type == "Pair and Triangle":
        return """
        For example, consider a graph coloring problem that involves both pairs and triangles. First, let's 
        consider two connected nodes, A and B. To color these nodes, assign a different color to each one. 
        For instance, A can be colored with color 1, and B with color 2.

        Now consider a triangle formed by nodes X, Y, and Z, where each node is connected to the other two. 
        Assign different colors to each of these nodes. For instance, X can be colored with color 1, Y with 
        color 2, and Z with color 3.

        Examples:
        (A 1)
        (B 2)
        (X 1)
        (Y 2)
        (Z 3)
        """

    elif example_type == "clique" or example_type == "Clique":
        if graph_size > 7:
            return """
            For example, consider a graph coloring problem for four nodes, A, B, C, and D, all connected to 
            each other (forming a fully connected subgraph, or clique). To color these nodes, assign different 
            colors to each one. For instance, A can be colored with color 1, B with color 2, C with color 3, 
            and D with color 4. This ensures that no two adjacent nodes share the same color.

            Example:
            (A 1)
            (B 2)
            (C 3)
            (D 4)
            """
        else:
            return """
            For example, consider a graph coloring problem for three nodes, A, B, and C, all connected to 
            each other (forming a fully connected subgraph, or clique). To color these nodes, assign different 
            colors to each one. For instance, A can be colored with color 1, B with color 2, and C with color 3. 
            This ensures that no two adjacent nodes share the same color.

            Example:
            (A 1)
            (B 2)
            (C 3)
            """

    else:
        raise ValueError("Invalid example type. Must be one of 'none', 'pair', 'triangle', 'pair+triangle', or 'clique'.")
