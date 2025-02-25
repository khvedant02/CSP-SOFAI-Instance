# CSP-SOFAI-Instance

**A Neurosymbolic Fast and Slow Architecture for Graph Coloring**

## Overview

This repository contains the implementation of SOFAI-v2, a neurosymbolic architecture designed for solving Constraint Satisfaction Problems (CSPs), specifically the **graph coloring problem**. The system follows the **"Thinking, Fast and Slow"** paradigm, integrating a fast, experience-driven **System 1 (S1)** solver using a Large Language Model (LLM) and a slow, exact **System 2 (S2)** solver using the **DSATUR algorithm with backtracking**.

SOFAI-v2 iteratively refines solutions proposed by S1 using **episodic memory, feedback mechanisms, and example-driven learning**, significantly improving performance on unsolvable and mixed-complexity cases.

## Features

- **Graph Coloring Problem Solver**:
  - Uses an LLM (Mistral-7B) as **System 1 (S1)** for rapid predictions.
  - Uses **DSATUR with backtracking** as **System 2 (S2)** for correctness and completeness.
  - Implements **feedback-driven refinement** to iteratively improve S1 predictions.
  - Supports **episodic memory** for leveraging past solutions in similar problem instances.

- **Experimentation and Benchmarking**:
  - Graphs generated using the **Erdős–Rényi model**.
  - Supports multiple problem difficulty levels with **solvability mixes** (100% solvable, 100% unsolvable, or 50%-50% mix).
  - Evaluates performance based on **success rate, time taken, and iteration improvements**.

- **Validation and Experiment Automation**:
  - Includes a validator to check solution correctness.
  - Implements automated benchmarking for comparing SOFAI-v2 against baseline solvers.

## File Structure

```
CSP-SOFAI-Instance/
│── problem_generator/             # Code for generating random graph coloring problems
│    ├── generate.py               # Generates problem instances using Erdős–Rényi model
│
│── solver/                        # Solvers used in the SOFAI framework
│    ├── s2.py                     # DSATUR-based System 2 solver
│
│── utils/                         # Utility functions for episodic memory, prompt generation, etc.
│    ├── episodic_memory.py        # Manages past solutions for episodic memory retrieval
│    ├── example_generator.py      # Generates example subgraphs for learning
│    ├── improvement_trend_evaluator.py  # Evaluates solver improvement over iterations
│    ├── prompt_generator.py       # Generates prompts for LLM solver
│    ├── util_functions.py         # Miscellaneous utility functions
│
│── validator/                     # Validator for checking solution correctness
│    ├── validate.py               # Core validation logic for checking color assignment correctness
│    ├── validator.py              # High-level validation functions
│
│── requirements.txt               # Required dependencies for running the framework
│── run_app.py                     # Main script to execute the graph coloring solver
│── README.md                      # This documentation
```


## Setup Instructions

### 1️⃣ Install Ollama (Required for Running LLM-Based Solver)

SOFAI-v2 leverages **Ollama** to run local LLM-based inference. To install Ollama, follow these steps:

#### **For macOS & Linux:**
Run the following command in the terminal:
```
curl -fsSL https://ollama.com/install.sh | sh
```

#### **For Windows:**
Download and install Ollama from:  
[https://ollama.com/download](https://ollama.com/download)

Once installed, verify Ollama is running:
```
ollama list
```
If you see a list of available models or an empty list, Ollama is correctly installed.

---

### 2️⃣ Install Dependencies

Ensure you have **Python 3.10+** installed. Then, install the required Python dependencies:

```
pip install -r requirements.txt
```

The dependencies include:
- `networkx` - For handling graph structures
- `matplotlib` - For visualization
- `streamlit` - To run the interactive app
- `ollama` - For local LLM inference
- `rank_bm25` - For ranking and retrieval tasks

---

### 3️⃣ Running the Streamlit App

To launch the **interactive SOFAI-v2 app**, run:

```
streamlit run run_app.py
```

This will:
- Start the **Streamlit web interface**.
- Allow users to input and solve **graph coloring problems interactively**.
- Display **visualizations and feedback** for solutions.

Once the command runs, you can **access the app in your browser** at:
```
http://localhost:8501
```

---

This setup ensures that you can **install, run, and experiment** with SOFAI-v2 efficiently. 🚀

---

## Citation

If you use this work, please cite:
```
Khandelwal, Vedant, Vishal Pallagani, Biplav Srivastava, and Francesca Rossi. 
"A Neurosymbolic Fast and Slow Architecture for Graph Coloring." 
arXiv preprint arXiv:2412.01752 (2024).
```

```bibtex
@article{khandelwal2024neurosymbolic,
  title={A Neurosymbolic Fast and Slow Architecture for Graph Coloring},
  author={Khandelwal, Vedant and Pallagani, Vishal and Srivastava, Biplav and Rossi, Francesca},
  journal={arXiv preprint},
  year={2024},
  eprint={2412.01752},
  archivePrefix={arXiv}
}
```
