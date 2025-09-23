#optional when not sure about langchain version
try:
    from langchain.memory import ConversationBufferMemory, ChatMessageHistory
except Exception:
    from langchain.memory import ConversationBufferMemory
    from langchain_community.chat_message_histories import ChatMessageHistory  # type: ignore

try:
    from langchain_core.messages import SystemMessage
except Exception:
    from langchain.schema import SystemMessage  # type: ignore


# Simple, general starting prompt applied once at session start
SYSTEM_PROMPT = (
    "You are a helpful RAG assistant for the Nepal Manifesto Chatbot. "
    "Be concise and structured; use short paragraphs and clear bullet lists. "
    "Bold key insights; use markdown formatting for emphasis. "
    "Base answers on the provided manifesto content; if unknown or out of scope, say 'Unknown' "
    "and optionally ask a clarifying question. Keep responses safe and professional."
)

def get_memory():
    chat_history = ChatMessageHistory()
    chat_history.add_message(SystemMessage(content=SYSTEM_PROMPT))


    return ConversationBufferMemory(
        memory_key="chat_history",
        input_key="question",
        output_key="answer",    # <--- must match chain output_key
        return_messages=True,
        chat_memory=chat_history,
    )