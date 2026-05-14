import streamlit as st
from ollama import chat


DEFAULT_MODEL = "gemma4:e4b"

st.set_page_config(page_title="Gemma 4 Local Assistant", page_icon="AI")
st.title("Gemma 4 Local Assistant")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": "You are a concise, helpful local AI assistant.",
        }
    ]

for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

prompt = st.chat_input("Ask a question...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    response = chat(model=DEFAULT_MODEL, messages=st.session_state.messages)
    answer = response["message"]["content"]
    st.session_state.messages.append({"role": "assistant", "content": answer})

    with st.chat_message("assistant"):
        st.markdown(answer)
