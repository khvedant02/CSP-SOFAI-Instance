import ollama

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