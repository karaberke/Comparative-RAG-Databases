from enum import Enum
import os
from typing import Literal
from dotenv import load_dotenv
from openai import OpenAI
import chromadb
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.responses import StreamingResponse
import asyncio
import json
import re
from llama_index.graph_stores.neo4j import Neo4jPropertyGraphStore
from llama_index.core import PropertyGraphIndex
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai_like import OpenAILike
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.indices.property_graph import VectorContextRetriever
from llama_index.llms.ollama import Ollama
from sentence_transformers import CrossEncoder
from nltk.corpus import stopwords
from collections import Counter
from qdrant_client import QdrantClient, AsyncQdrantClient
from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core.postprocessor import SentenceTransformerRerank
import time
load_dotenv()

class Database(Enum):
    Graph = 1
    ChromaDB = 2
    Qdrant = 3

class LlmModel(Enum):
    mistral = "Mistral-Small-3.2-24B-Instruct-2506"
    chatgpt = "gpt-oss-120b"

class UserSettings(BaseModel):
    selectedDatabases: list[str]
    selectedLlm:Literal["chatgpt","mistral"]

#Path Files
SETTINGS_FILE_PATH = "user_settings.json" 
# CHROMA_PATH = r"C:/Users/KARAB/OneDrive - Idaho National Laboratory/Workspace/AI/backend/chroma.db"
HISTORY_PATH = r"backend/rag/data/chat_history/"


OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
SIMILARITY_THRESHOLD = 50
QDRANT_COLLECTION_NAME = "inl-safety"
# CHROMA_COLLECTION_NAME = "inl-data"
SELECTED_DATABASE=[]

# System prompt for the RAG model
SYSTEM_PROMPT = """
You are a helpful assistant. Answer user questions using ONLY the provided context documents.
Format your responses using Markdown for readability, including bullet points, numbered lists, bold text, and code blocks where appropriate.

INSTRUCTIONS:
- Base your answers strictly on the retrieved context provided.
- If the context doesn't contain sufficient information to answer the question, respond with "I don't have enough information in the provided sources to answer this question".
Reasoning: high
"""

#Used Models
DENSE_MODEL = "bge-m3"
SPARSE_MODEL = "prithivida/Splade_PP_en_v1"
RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L12-v2"
RERANK_MODEL2 = "ms-marco-MiniLM-L12-v2"
model = CrossEncoder(RERANK_MODEL)

STOP_WORDS = stopwords.words("english")
CONTEXT_WINDOW=128000
QUESTION_COUNT=5
N_RESULTS=20
DEBUG = True
FOUND_ANSWER = [False]

reranker = SentenceTransformerRerank(top_n=2, model=RERANK_MODEL)

# Connect to OpenAI client
openai_client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=os.environ.get("OPENAI_API_URL"),
)

# Connect to Neo4j
# graph_store = Neo4jPropertyGraphStore(
#     username=os.environ.get("NEO4J_USERNAME"),
#     password=os.environ.get("NEO4J_PASSWORD"),
#     url=os.environ.get("NEO4J_URL"),
# )

# Connect to Qdrant client
client = QdrantClient(host="localhost", port=6333)
aclient = AsyncQdrantClient(host="localhost", port=6333)


# Connect to ChromaDB
# try:
#     chroma_client = chromadb.HttpClient(host='localhost', port=8000)
#     collection = chroma_client.get_or_create_collection(name=CHROMA_COLLECTION_NAME)
#     if DEBUG:
#         print(f"Successfully connected to DB. The collection has {collection.count()} items.")
# except Exception as e:
#     print(f"Failed to connect or operate on DB: {e}")
#     exit()


llm_model ="Mistral-Small-3.2-24B-Instruct-2506"
embed_model = OpenAIEmbedding(model_name=DENSE_MODEL,api_base=os.environ.get("OPENAI_API_URL"),api_key=OPENAI_API_KEY)

# llm_neo4j=OpenAILike(
#     model="gpt-oss-120b",
#     api_base=os.environ.get("OPENAI_API_URL"),
#     api_key=OPENAI_API_KEY,
#     context_window=CONTEXT_WINDOW,
# )

llm_qdrant=OpenAILike(
    model=llm_model,
    api_base=os.environ.get("OPENAI_API_URL"),
    api_key=OPENAI_API_KEY,
    context_window=128000,
    is_chat_model=True,
    is_function_calling_model=False,
)

vector_store = QdrantVectorStore(
    client=client,
    aclient=aclient,
    collection_name=QDRANT_COLLECTION_NAME,
    enable_hybrid=True,
    fastembed_sparse_model=SPARSE_MODEL,
    use_async=True,
)

loaded_index = VectorStoreIndex.from_vector_store(
    vector_store,
    embed_model=OpenAIEmbedding(model_name=DENSE_MODEL,api_base=os.environ.get("OPENAI_API_URL"),api_key=OPENAI_API_KEY),
)

# retrieve 2 sparse, 2 dense, and filter down to 3 total hybrid results
query_engine_qdrant = loaded_index.as_query_engine(
    vector_store_query_mode="hybrid",
    sparse_top_k=10,
    similarity_top_k=10,
    hybrid_top_k=3,
    llm=llm_qdrant,
    use_async=True,
    node_postprocessors=[reranker]
)
 
# index_neo4j = PropertyGraphIndex.from_existing(
#     property_graph_store=graph_store,
#     llm=llm_neo4j,
# )

# sub_retriever = VectorContextRetriever(
# index_neo4j.property_graph_store, 
# vector_store=index_neo4j.vector_store,
# embed_model=embed_model,
# )

# query_engine = RetrieverQueryEngine.from_args(
#     index_neo4j.as_retriever(sub_retrievers=[sub_retriever]), llm=Ollama(
#         model="llama3",
#         request_timeout=3600,
#         # Manually set the context window to limit memory usage
#         context_window=10000,
#         temperature=0.3,
#     )
# )

app = FastAPI()

# Add CORS middleware to allow requests from your frontend
origins = [
    "http://localhost:3000", 
    "http://localhost:5173",
    "http://10.142.12.194:5173",
    "http://172.17.208.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

# In-memory conversation history
conversation = [{"role": "system", "content": SYSTEM_PROMPT}]

def betterQuestion(user_query):
    completion = openai_client.chat.completions.create(
        model=llm_model,
        messages=[
            {
                "role": "user",
                "content": f"Can you rewrite this question to be clear and specific for an llm to understand it better. Your response only includez the generated question. Question = {user_query}"
            }
        ]
    )
    return completion.choices[0].message.content

# async def query_graphdb(user_query):
#     if not FOUND_ANSWER[0]:
#         response = query_engine.query(user_query)
#     else:
#         return
#     if not FOUND_ANSWER[0]:
#         retrieved_docs = await rerank_docs(user_query,[str(response)])
#     else:
#         return
    
#     if DEBUG:
#         print(f"GraphDB is finished: {response}")
#         print(f"Reranked Result: {retrieved_docs}")
#     return (str(response))

def _preprocess_query(query: str) -> str:
    query = query.strip().lower()
    query = re.sub(r'[^\w\s?!]', '', query)  # Strip special characters
    stopwords_dict = Counter(STOP_WORDS)
    query = ' '.join([word for word in query.split() if word not in stopwords_dict and word])
    return query 

async def rerank_docs(question,results)->set:
    retrieved_docs=set()
    scores = model.predict([(question, doc) for doc in results])
    for doc,score in zip (results, scores):
        if DEBUG:
            print(f"Score: {score*10}\nDoc: {doc}\n")
        if(score*10 > SIMILARITY_THRESHOLD):
            retrieved_docs.add(doc)
    if DEBUG:
            print("-"*250,"\nFiltered Result:")
            print(retrieved_docs)
            print("-"*250)
    return retrieved_docs

async def stream_generator(user_query,context_str,selected_model):
    # print(context_str)
    augmented_query = f"User Question: {user_query}\n\nContext Documents:\n{context_str}"

    conversation.append({"role": "user", "content": augmented_query})

    response_stream = openai_client.chat.completions.create(
        model=selected_model,
        messages=conversation,
        max_tokens=10000,
        stream=True
    )

    full_assistant_reply = ""
    for chunk in response_stream:
        content = chunk.choices[0].delta.content
        if content:
            full_assistant_reply += content
            # Yield only the content in the Server-Sent Event format
            yield f"data: {json.dumps({'reply': content})}\n\n"
            await asyncio.sleep(0.01)  # Necessary for streaming

    if full_assistant_reply:
        conversation.append({"role": "system", "content": full_assistant_reply})

async def get_context(question_pool):

    # Use a set to track unique document texts and avoid duplicates 
    processed_docs = set() 
    
    # --- 1. Vector Similarity Search --- 
    for question in question_pool: 
        if DEBUG:
            print(f"Question: {question}\n")
        query_embedding = openai_client.embeddings.create( 
            input=question, 
            model=DENSE_MODEL, 
        ).data[0].embedding 
    
        # Query for semantically similar documents based on user question
        # results = collection.query( 
        #     query_embeddings=[query_embedding], 
        #     n_results=N_RESULTS, 
        #     include=["metadatas", "documents", "distances"] 
        # )
        # processed_docs=await rerank_docs(question,results["documents"][0])

        if processed_docs:
            FOUND_ANSWER[0]=True
        if DEBUG:
            print(f"Found {len(processed_docs)} unique documents above similarity score of {SIMILARITY_THRESHOLD}\n")
            print("Returning first query")
        return processed_docs

def get_selected_databases(user_input):
    selected = []
    for num in user_input:
        try:
            db = Database(int(num))
            selected.append(db)
        except (ValueError, KeyError):
            continue  # Ignore invalid entries
    print(selected)
    return selected

""" Receives settings from the frontend and saves them to a JSON file. """ 
@app.post("/api/user-settings") 
async def save_user_settings(settings): 
    print(f"--- POST /api/user-settings ---")
    print(f"Received settings object: {settings}")
    try:
        with open(SETTINGS_FILE_PATH, "w") as f: 
            json.dump(settings.model_dump(), f, indent=2) 
        if DEBUG: 
            print(f"Saved settings: {settings.model_dump_json()}") 
        return {"message": "Settings saved successfully"}
    except IOError as e: 
        print(f"Error saving settings to file: {e}") 

""" Retrieves the saved user settings from the JSON file. If the file doesn't exist, it returns a default configuration. """ 
@app.get("/api/user-settings") 
async def get_user_settings():
    try:
        with open(SETTINGS_FILE_PATH, "r") as f:
            data = json.load(f) 
            if DEBUG:
                print(data)
            return UserSettings(**data)
    except FileNotFoundError:# If the settings file does not exist, return a default state 
        return UserSettings(selectedDatabases=[], selectedLlm="chatgpt")
    except (json.JSONDecodeError, KeyError) as e: # If the file is corrupted or has an invalid format 
        print(f"Error reading or parsing settings file: {e}") 

def load_settings():
    global SELECTED_DATABASE
    global SELECTED_LLM
    try:
        # Define the path to the user_settings.json file
        file_path = "user_settings.json"  # Change this to your actual path
        
        # Check if the file exists before trying to read it
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                settings = json.load(f)
                SELECTED_DATABASE = settings.get("selectedDatabases", [])
                SELECTED_LLM = settings.get("selectedLlm")
                if DEBUG:
                    print(f"Loaded settings: {SELECTED_DATABASE}")
                    print(f"Loaded settings: {SELECTED_LLM}")
        else:
            print("Settings file does not exist.")
    except Exception as e:
        print(f"Error loading settings: {e}")


@app.post("/api/chat")
async def chat(chat_request: ChatRequest):
    load_settings()
    selected_db= get_selected_databases(SELECTED_DATABASE)
    selected_model = LlmModel[SELECTED_LLM].value
    if DEBUG:
        print(selected_model)
    """
    API endpoint to handle the chat request and stream the response.
    """
    start_time = time.time()
    user_query=chat_request.message
    tasks=[]
    question_pool =set()
    question_pool.add(user_query)
    question_pool.add(_preprocess_query(user_query))
    for i in range(QUESTION_COUNT):
        question_pool.add(betterQuestion(user_query))
    if DEBUG:
        print(question_pool)
    for db in selected_db:
        # if db == Database.Graph:
        #     tasks.append(query_graphdb(user_query))
        #     print("Graph")
        # elif db == Database.ChromaDB:
        #     tasks.append(get_context(question_pool))
        #     print("ChromaDBGraph")
        if db == Database.Qdrant:
            tasks.append(query_engine_qdrant.aquery(user_query))
            print("Qdrant")
    processed_docs = await asyncio.gather(*tasks)
    processed_docs = [item for item in processed_docs if item]
    context_str = "\n".join( 
        [f"Source {i+1}:\n{doc}" for i, doc in enumerate(processed_docs)] 
    )
    FOUND_ANSWER[0] = False
    end_time = time.time()
    elapsed_time = end_time - start_time
    if DEBUG:
        print(f"Time taken: {elapsed_time:.3f} seconds")
        print(f"Received Query: {user_query}\nBetter Query: {question_pool}\n") 
        print(f"Given Context:\n {context_str}\n")
        for i, question in enumerate(question_pool, start=1):
            print(f"Question {i}: {question}\n")
    print(context_str)
    return StreamingResponse(stream_generator(user_query,context_str,selected_model), media_type="text/event-stream")

# Command to run the backend server, need to run this in terminal to start main instead of just running the main,py file:
# uvicorn main:app --port 3000 --reload --log-level debug
