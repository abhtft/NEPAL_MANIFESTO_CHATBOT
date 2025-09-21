# Manifesto Chatbot

This chatbot answers questions based on the manifesto document.

## Setup

1. Put your manifesto in `data/manifesto.pdf`
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run ingestion:
   ```bash
   python ingest/ingest.py
   ```
4. Start chatbot (Streamlit UI):
   ```bash
   streamlit run app.py
   ```
