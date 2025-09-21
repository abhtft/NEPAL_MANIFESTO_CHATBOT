Absolutely! Let me explain the **full workflow of your Azure-based manifesto chatbot** in a clear, structured way. I’ll break it down step by step.

---

## **1️⃣ Data Ingestion**

**Purpose:** Convert your manifesto PDF into chunks that the chatbot can understand and embed.

**Steps:**

1. **Load the PDF**

   * `PyPDFLoader` reads the entire manifesto (60 pages) into a text document object.

2. **Split into chunks**

   * Use `RecursiveCharacterTextSplitter` to break the text into smaller pieces (e.g., 1000 characters each with 200 overlap).
   * This makes embeddings more precise and helps retrieval.

3. **Create embeddings**

   * Use `AzureOpenAIEmbeddings` to generate vector embeddings for each chunk.
   * Embeddings are numerical representations of text that the model can search efficiently.

4. **Store in Chroma vector database**

   * `Chroma.from_documents()` persists all the embeddings in `chroma_store`.
   * This allows fast retrieval when a user asks a question.

**Outcome:** A vector database where every chunk of your manifesto is searchable.

---

## **2️⃣ Retriever**

**Purpose:** Retrieve the most relevant chunks of text based on the user’s question.

**How it works:**

1. `get_retriever()` connects to the **Chroma vector store**.
2. It uses the **Azure embeddings** to match the user query with the closest chunks.
3. Returns top `k` chunks (e.g., 4) to the LLM for answering.

**Outcome:** The chatbot always works with the most relevant sections of the manifesto.

---

## **3️⃣ Conversational Chain**

**Purpose:** Make the LLM answer user questions **in a conversational manner** and remember context.

**Components:**

1. **LLM** → `AzureChatOpenAI`

   * This is the language model (e.g., GPT-4) hosted on Azure.
   * It generates answers based on the retrieved text.

2. **Retriever** → feeds relevant chunks to the LLM.

3. **Memory** → `ConversationBufferMemory`

   * Keeps track of chat history so the conversation feels natural.
   * Only stores the output key `answer` to avoid conflicts with `source_documents`.

4. **Chain** → `ConversationalRetrievalChain`

   * Connects LLM + Retriever + Memory.
   * Returns:

     * `answer` → bot’s response
     * `source_documents` → original chunks used to generate the answer (optional for UI)

**Outcome:** You get a context-aware, document-specific conversational AI.

---

## **4️⃣ Streamlit UI**

**Purpose:** Provide a simple interface for users to chat with the bot.

**How it works:**

1. User types a question in the text box.
2. `chain.invoke({"question": query})` retrieves the answer.
3. The chat history is updated automatically.
4. Optionally, you can display **source documents** used to generate the answer.

**Outcome:** An interactive web app running locally, where users can query your manifesto document.

---

## **5️⃣ Optional Monitoring (Arize / Phoenix)**

**Purpose:** Track chatbot performance, like which questions are asked, embeddings, and answers.

* Currently optional — can be added later.
* Helps measure correctness, bias, and user engagement.

---

### **Workflow Diagram (Simplified)**

```
User Question
      ↓
   Streamlit UI
      ↓
ConversationalRetrievalChain
 ┌────────────┬────────────┐
LLM (Azure)  Retriever   Memory
      ↓          ↑         ↑
  Answer       Relevant Chunks
      ↓
Return answer + sources
```

---

✅ **Key Points:**

* Azure embeddings are used consistently in ingestion and retrieval.
* Chain memory only stores the `answer` key to avoid errors.
* Retrieval ensures answers are **document-specific**, not general knowledge.
* UI is lightweight and easy to test.

---

If you want, I can now **give a fully fixed folder structure** ready to run end-to-end with Azure embeddings + chat + Streamlit UI. This will eliminate all your current errors.

Do you want me to do that?
