from langchain.memory import ConversationBufferMemory

def get_memory():
    return ConversationBufferMemory(
        memory_key="chat_history",
        input_key="question",
        output_key="answer",    # <--- must match chain output_key
        return_messages=True
    )