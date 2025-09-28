from langchain_openai import AzureChatOpenAI
import json
import pprint
import os

# Example setup (adjust with your credentials)
llm = AzureChatOpenAI(
    azure_endpoint=os.getenv("AZURE_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-08-01-preview",
    model="gpt-4"
)

# Example invoke call
response = llm.invoke("What is the capital of Nepal?")

print(response).dict()

print("=" * 50)
print("METHOD 1: Direct Print (Most Common)")
print("=" * 50)
print(response)

print("\n" + "=" * 50)
print("METHOD 2: Print Raw String Content")
print("=" * 50)
print(repr(response))  # Shows exact string representation

print("\n" + "=" * 50)
print("METHOD 3: Print Just the Content")
print("=" * 50)
print(response.content)

print("\n" + "=" * 50)
print("METHOD 4: Print All Attributes")
print("=" * 50)
for attr in dir(response):
    if not attr.startswith('_'):
        try:
            value = getattr(response, attr)
            if not callable(value):
                print(f"{attr}: {value}")
        except:
            pass

print("\n" + "=" * 50)
print("METHOD 5: Pretty Print as Dictionary")
print("=" * 50)
if hasattr(response, '__dict__'):
    pprint.pprint(response.__dict__, width=80, depth=None)

print("\n" + "=" * 50)
print("METHOD 6: JSON Format (if serializable)")
print("=" * 50)
try:
    # Try to convert to dict first
    if hasattr(response, 'dict'):
        response_dict = response.dict()
    else:
        response_dict = vars(response)
    
    print(json.dumps(response_dict, indent=2, ensure_ascii=False))
except Exception as e:
    print(f"Cannot convert to JSON: {e}")
    # Fallback to manual dict creation
    response_dict = {
        'content': getattr(response, 'content', ''),
        'additional_kwargs': getattr(response, 'additional_kwargs', {}),
        'response_metadata': getattr(response, 'response_metadata', {}),
        'type': type(response).__name__
    }
    print(json.dumps(response_dict, indent=2, ensure_ascii=False))

print("\n" + "=" * 50)
print("METHOD 7: Debug Print with Type Info")
print("=" * 50)
print(f"Type: {type(response)}")
print(f"Content: {response.content}")
print(f"Additional kwargs: {getattr(response, 'additional_kwargs', {})}")
print(f"Response metadata: {getattr(response, 'response_metadata', {})}")

print("\n" + "=" * 50)
print("METHOD 8: Raw Object Inspection")
print("=" * 50)
import inspect
print("Object attributes:")
for name, value in inspect.getmembers(response):
    if not name.startswith('_') and not inspect.ismethod(value):
        print(f"  {name}: {value}")

print("\n" + "=" * 50)
print("METHOD 9: Custom Formatting Function")
print("=" * 50)
def print_langchain_response(response):
    """Custom function to nicely format LangChain response"""
    print("🤖 LangChain Response:")
    print("-" * 30)
    print(f"📝 Content: {response.content}")
    
    if hasattr(response, 'additional_kwargs') and response.additional_kwargs:
        print(f"⚙️  Additional kwargs: {response.additional_kwargs}")
    
    if hasattr(response, 'response_metadata') and response.response_metadata:
        print(f"📊 Response metadata: {response.response_metadata}")
    
    if hasattr(response, 'usage_metadata') and response.usage_metadata:
        print(f"💰 Usage metadata: {response.usage_metadata}")
    
    print(f"🏷️  Type: {type(response).__name__}")
    print("-" * 30)

print_langchain_response(response)

print("\n" + "=" * 50)
print("METHOD 10: Save to File and Print")
print("=" * 50)
# Save the exact output to a file
with open('langchain_output.txt', 'w', encoding='utf-8') as f:
    f.write(str(response))
    f.write('\n\n--- Additional Details ---\n')
    f.write(f"Content: {response.content}\n")
    f.write(f"Type: {type(response)}\n")

# Read and print
with open('langchain_output.txt', 'r', encoding='utf-8') as f:
    print("File contents:")
    print(f.read())