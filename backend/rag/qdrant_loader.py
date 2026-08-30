import asyncio
import os
from dotenv import load_dotenv
from openai import OpenAI
import re
import json
import os
from llama_index.core import SimpleDirectoryReader
from llama_index.core.node_parser import (
    SentenceSplitter,
    SemanticSplitterNodeParser,
)
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core import Document
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core import Settings
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient, AsyncQdrantClient
import time
from fastembed import SparseTextEmbedding
import nest_asyncio

nest_asyncio.apply()
load_dotenv()

DATA_PATH=r"./data/"
INPUT_PATH=r"./input/"
DENSE_MODEL="bge-m3"
COLLECTION_NAME = "inl-safety"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
API_URL=os.environ.get("OPENAI_API_URL")
SPARSE_MODEL = "prithivida/Splade_PP_en_v1"

documents = []

openai_client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=API_URL,
)

EMBED_MODEL = OpenAIEmbedding(model_name="bge-m3",api_base=API_URL,api_key=OPENAI_API_KEY)


splitter = SemanticSplitterNodeParser(
    buffer_size=1, breakpoint_percentile_threshold=75, embed_model=EMBED_MODEL
)

# also baseline splitter
base_splitter = SentenceSplitter(chunk_size=512)

# Setup Qdrant in-memory, for easy prototyping
client = QdrantClient(url="http://localhost:6333")
aclient = AsyncQdrantClient(host="localhost", port=6333)

def load_text_file(data):
    try:
        content = data["text"]
        return content
    except FileNotFoundError:
        return "File not found. Please check the file path."

def replace_urls_with_placeholder(text):
    # Regular expression to match URLs
    url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
    # Replace all URLs found with the string "URL"
    replaced_text = re.sub(url_pattern, 'URL', text)
    return replaced_text

def clean(text):
    cleaned_text = text.replace('{', '').replace('}', '')
    cleaned_text = cleaned_text.replace('\n',' ').replace('\t',' ')
    cleaned_text = cleaned_text.replace('�',' ').replace('\u00a0',' ')
    cleaned_text = cleaned_text.replace('([[', ')').replace(']])', ')')
    return cleaned_text

def processtext(data):
    # Load and clean text
    text_content = load_text_file(data)
    text_content = replace_urls_with_placeholder(text_content)
    text_content = clean(text_content)

    # Create document and split into nodes
    document = Document(text=text_content, id_=data['metadata']['file_name'])
    nodes = splitter.get_nodes_from_documents([document])
    sentences = [node.get_content() for node in nodes]

    # Insert into index    
    for sentence in sentences:
        documents.append(
            Document(text=sentence, metadata={"source": data['metadata']['file_name']})
        )
    return
    
def convert_data():
    documents = SimpleDirectoryReader(INPUT_PATH).load_data()

    for i, doc in enumerate(documents):
        export_data = {"text": doc.text, "metadata": doc.metadata}
        #doc.metadata.get("file_name")) to get the file name
        file_name = f"document_{i+1}.json"
        file_path = os.path.join(DATA_PATH, file_name)
        
        with open(file_path, 'w') as json_file:
            json.dump(export_data, json_file, indent=4)
    
#Experimental: Process all files at the same time
async def process_all_files_concurrently():
    tasks = []

    for path in os.listdir(DATA_PATH): 
        file_path = os.path.join(DATA_PATH, path) 
        if os.path.isfile(file_path) and file_path.endswith(".json"): 
            with open(file_path, 'r') as file: 
                data = json.load(file)
                # Run processtext in a separate thread
                tasks.append(asyncio.to_thread(processtext, data))

    await asyncio.gather(*tasks)

async def main():
    if client.collection_exists(COLLECTION_NAME):
        client.delete_collection(COLLECTION_NAME)
    start_time = time.time()
    convert_data()
    vector_store = QdrantVectorStore(
        collection_name=COLLECTION_NAME,
        client=client,
        aclient=aclient,
        enable_hybrid=True,
        fastembed_sparse_model=SPARSE_MODEL,
        batch_size=64,
        parallel=16
    )
    for path in os.listdir(DATA_PATH): 
        # check if current path is a file 
        file_path = os.path.join(DATA_PATH, path) 
        # print(file_path) 
        if os.path.isfile(file_path) and file_path.endswith(".json"): 
            with open(file_path, 'r') as file: 
                data = json.load(file) 
                processtext(data)

    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = VectorStoreIndex.from_documents(
        documents,
        # our dense embedding model
        embed_model=EMBED_MODEL,
        storage_context=storage_context,
        use_async=True
    )
    print("Took to run: --- %s seconds ---" % (time.time() - start_time))


asyncio.run(main())
