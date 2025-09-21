import streamlit as st
from bot.chain import get_chain
from dotenv import load_dotenv
#from monitoring.arize_integration import init_arize
# Load .env file
load_dotenv()


chain = get_chain()
#arize_session = init_arize()

st.set_page_config(page_title="Manifesto Chatbot", page_icon="🤖")
st.title("📜 Manifesto Chatbot")
st.write("Ask me anything about the manifesto.")

if "history" not in st.session_state:
    st.session_state.history = []

query = st.chat_input("Type your question here...")

if query:
    with st.spinner("Thinking..."):
        result = chain.invoke({"question": query})
        answer = result["answer"]
        st.session_state.history.append(("You", query))
        st.session_state.history.append(("Bot", answer))
        #arize_session.log_event({"inputs": query, "outputs": answer})

for speaker, text in st.session_state.history:
    if speaker == "You":
        st.chat_message("user").write(text)
    else:
        st.chat_message("assistant").write(text)
