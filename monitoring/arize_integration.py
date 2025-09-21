#from phoenix.session import Session
from arize_phoenix import Session
from dotenv import load_dotenv
def init_arize():
    session = Session()
    print("✅ Arize monitoring started.")
    return session
