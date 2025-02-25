from rank_bm25 import BM25Okapi
from typing import List, Dict, Tuple
import numpy as np

class EpisodicMemory:
    def __init__(self):
        # Memory storage for past problem instances and their solutions
        self.memory = []  # Each element will be a dict with 'problem' and 'solution' keys

    def add_memory(self, problem: str, solution: str):
        """ Adds a problem and its solution to the episodic memory. """
        self.memory.append({'problem': problem, 'solution': solution})

    def retrieve_similar(self, new_problem: str, top_k: int = 1) -> List[Tuple[str, str]]:
        """ Retrieves the most similar past problems and their solutions using BM25.

        Args:
            new_problem (str): The new problem instance described in text form.
            top_k (int): Number of top similar instances to retrieve.

        Returns:
            List[Tuple[str, str]]: A list of tuples containing the problem and solution pairs.
        """
        # Tokenize and prepare data for BM25
        corpus = [doc['problem'].split() for doc in self.memory]
        bm25 = BM25Okapi(corpus)

        # Query the new problem
        tokenized_query = new_problem.split()
        scores = bm25.get_scores(tokenized_query)
        top_indexes = np.argsort(scores)[::-1][:top_k]  # Get the indexes of the top_k scores

        # Fetch the most relevant memories
        relevant_memories = [(self.memory[i]['problem'], self.memory[i]['solution']) for i in top_indexes]

        return relevant_memories
    

# Example usage:
# if __name__ == "__main__":
#     episodic_memory = EpisodicMemory()
#     # Populate memory with example data
#     episodic_memory.add_memory("Solve the equation x + 2 = 4", "x = 2")
#     episodic_memory.add_memory("Calculate the perimeter of a rectangle with sides 2 and 3", "Perimeter = 10")
    
#     # New problem instance
#     new_problem = "Find x when x + 3 = 5"
#     similar_instances = episodic_memory.retrieve_similar(new_problem, top_k=1)
    
#     print("Most similar past problem and solution:")
#     for problem, solution in similar_instances:
        # print(f"Problem: {problem}, Suggested Solution: {solution}")