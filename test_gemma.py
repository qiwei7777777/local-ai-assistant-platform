from ollama import chat


response = chat(
    model="gemma4:e4b",
    messages=[
        {
            "role": "system",
            "content": "You are a concise, helpful local AI assistant.",
        },
        {
            "role": "user",
            "content": "Explain machine learning in three sentences.",
        },
    ],
)

print(response["message"]["content"])
