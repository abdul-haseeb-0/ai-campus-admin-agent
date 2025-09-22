import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import Agent, OpenAIChatCompletionsModel, Runner, function_tool, ModelSettings
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# -------------------------
# 1. Environment + Keys
# -------------------------
load_dotenv()
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not set in .env")

# -------------------------
# 2. OpenAI Client
# -------------------------
client = AsyncOpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

# -------------------------
# 3. RAG Setup
# -------------------------
DATA_PATH = "backend\data\smit.txt"
if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(f"Missing {DATA_PATH}")

loader = TextLoader(DATA_PATH)
documents = loader.load()

# Efficient splitting with adaptive logic
splitter = RecursiveCharacterTextSplitter(
    chunk_size=800, chunk_overlap=100, separators=["\n\n", "\n", ".", " "]
)
docs = splitter.split_documents(documents)

# Build embeddings + FAISS index
embeddings = GoogleGenerativeAIEmbeddings(model='gemini-embedding-001', api_key=GEMINI_API_KEY)
vectorstore = FAISS.from_documents(docs, embeddings)
retriever = vectorstore.as_retriever()

# -------------------------
# 4. Retriever Tool
# -------------------------
@function_tool
def retrieve_info(query: str) -> str:
    """Search the local knowledge base and return the most relevant context for the query.

    Args:
        query: The user question or topic to look up.
    """
    results = retriever.get_relevant_documents(query)
    context = "\n\n".join([doc.page_content for doc in results[:3]])
    return context if context else "No relevant info found."

# -------------------------
# 5. Agent
# -------------------------
rag_agent = Agent(
    name="smit_rag_agent",
    instructions=(
        "You are a retrieval-augmented assistant. "
        "Use the `retrieve_info` tool whenever the query requires external knowledge. "
        "Always cite retrieved context in your answer. "
        "If no information is available, say no clearly. don't make up answers. "
        "Be concise, accurate, and professional."
    ),
    model=OpenAIChatCompletionsModel(
        model="gemini-1.5-flash",
        openai_client=client,
    ),
    tools=[retrieve_info],
    model_settings=ModelSettings(tool_choice="required")
)

# -------------------------
# 6. CLI Loop
# -------------------------
# if __name__ == "__main__":
#     print("RAG Agent ready. Type 'exit' to quit.\n")
#     while True:
#         query = input("User: ").strip()
#         if query.lower() in {"exit", "quit"}:
#             break
#         result = Runner.run_sync(agent, query)
#         print("Assistant:", result.final_output, "\n")