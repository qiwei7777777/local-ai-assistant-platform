from ollama import chat


DEFAULT_MODEL = "gemma4:e4b"

messages = [
    {
        "role": "system",
        "content": "You are a concise, helpful local AI assistant.",
    }
]

print("Type exit or quit to stop.\n")

while True:
    user_input = input("You: ").strip()
    if user_input.lower() in {"exit", "quit"}:
        print("Goodbye.")
        break

    messages.append({"role": "user", "content": user_input})

    response = chat(model=DEFAULT_MODEL, messages=messages)
    answer = response["message"]["content"]

    print(f"Assistant: {answer}\n")
    messages.append({"role": "assistant", "content": answer})
