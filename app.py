import streamlit as st
from bot.chain import get_chain
from dotenv import load_dotenv
import os
import json
import uuid
from datetime import datetime
#from monitoring.arize_integration import init_arize
# Load .env file
load_dotenv()


chain = get_chain()
#arize_session = init_arize()

st.set_page_config(page_title="Manifesto Chatbot", page_icon="🤖")
st.title("📜 Manifesto Chatbot")
st.write("Ask me anything about the manifesto.")

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.session_start = datetime.utcnow().isoformat() + "Z"

if "history" not in st.session_state:
    st.session_state.history = []

query = st.chat_input("Type your question here...")

if query:
    with st.spinner("Thinking..."):
        result = chain.invoke({"question": query})
        answer = result["answer"]
        st.session_state.history.append({
            "speaker": "You",
            "text": query,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
        st.session_state.history.append({
            "speaker": "Bot",
            "text": answer,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
        #arize_session.log_event({"inputs": query, "outputs": answer})

for message in st.session_state.history:
    # Backwards compatibility if earlier tuples exist
    if isinstance(message, tuple) and len(message) == 2:
        speaker, text = message
    else:
        speaker = message.get("speaker")
        text = message.get("text")

    if speaker == "You":
        st.chat_message("user").write(text)
    else:
        st.chat_message("assistant").write(text)

# End session and persist timestamped log
if st.button("End session and save log"):
    session_log = {
        "session_id": st.session_state.get("session_id"),
        "session_start": st.session_state.get("session_start"),
        "session_end": datetime.utcnow().isoformat() + "Z",
        "total_messages": len(st.session_state.get("history", [])),
        "messages": st.session_state.get("history", []),
    }

    os.makedirs("logs", exist_ok=True)
    log_path = os.path.join("logs", f"session_{st.session_state.get('session_id')}.json")
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(session_log, f, ensure_ascii=False, indent=2)

    st.success(f"Session log saved: {log_path}")
    st.download_button(
        label="Download session log",
        data=json.dumps(session_log, ensure_ascii=False, indent=2),
        file_name=f"session_{st.session_state.get('session_id')}.json",
        mime="application/json",
    )
