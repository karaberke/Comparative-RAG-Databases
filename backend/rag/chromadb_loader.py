import os
from dotenv import load_dotenv
from openai import OpenAI
import re
import chromadb
import json
from llama_index.core import SimpleDirectoryReader
from llama_index.core.node_parser import (
    SentenceSplitter,
    SemanticSplitterNodeParser,
)
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core import Document

load_dotenv()

DATA_PATH=r"./backend/rag/data/"
INPUT_PATH=r"./backend/rag/input/"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
DENSE_MODEL="bge-m3"
API_URL=os.environ.get("OPENAI_API_URL")
COLLECTION_NAME = "inl-data"

openai_client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=API_URL,
)

embed_model = OpenAIEmbedding(model_name="bge-m3",api_base="https://api.hpc.inl.gov/llm/v1",api_key=OPENAI_API_KEY)

#semantic splitter
splitter = SemanticSplitterNodeParser(
    buffer_size=1, breakpoint_percentile_threshold=95, embed_model=embed_model
)

# also baseline splitter
base_splitter = SentenceSplitter(chunk_size=512)

chroma_client = chromadb.HttpClient(host='localhost', port=8000)


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

def create_embeddings(sentences):
    model="bge-m3"
    responses = openai_client.embeddings.create(
        input=sentences,
        model=model,
    )
    embeddings = []
    for data in responses.data:
        embeddings.append(data.embedding)
    return embeddings

def processtext(data):
    # Load text file
    text_content = load_text_file(data)

    # Remove URLs
    text_content = replace_urls_with_placeholder(text_content)

    # Do some basic cleaning
    text_content = clean(text_content)
    document = Document(text=text_content, id_=data['metadata']['file_name'])
    nodes = splitter.get_nodes_from_documents([document])
    sentences = [node.get_content() for node in nodes]

    # Create our embeddings
    embeddings = create_embeddings(sentences)

    # Create ids of sentences
    ids = [str(i) for i in range(len(sentences))]

    # Create collection
    collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)
    # Add to collection
    for sentence, embedding, doc_id in zip(sentences, embeddings, ids): 
        collection.add( 
            documents=sentence, 
            embeddings=embedding, 
            # Ensure the ID is a string 
            ids=str(doc_id), 
            metadatas=[{"source": data['metadata']['file_name']}] 
        ) 
    
def convert_data():
    documents = SimpleDirectoryReader(INPUT_PATH).load_data()

    for i, doc in enumerate(documents):
        export_data = {"text": doc.text, "metadata": doc.metadata}
        #doc.metadata.get("file_name")) to get the file name
        file_name = f"document_{i+1}.json"
        file_path = os.path.join(DATA_PATH, file_name)
        
        with open(file_path, 'w') as json_file:
            json.dump(export_data, json_file, indent=4)

def main():
    convert_data()

    # First, try to delete the collection if it exists
    try:
        chroma_client.delete_collection(name=COLLECTION_NAME)
        print(f"Deleted existing collection: {COLLECTION_NAME}")
    except:
        print(f"No existing collection named {COLLECTION_NAME} found. Proceeding to create a new one.")

    # Now, create the collection
    chroma_client.create_collection(
        name=COLLECTION_NAME,
        configuration={
            "hnsw": {
                "space": "cosine",
                "ef_search": 128,
                "ef_construction": 512,
                "max_neighbors": 32,
                "num_threads": 32
            },
            "embedding_function": None
        }
    )

    for path in os.listdir(DATA_PATH): 
        # check if current path is a file 
        file_path = os.path.join(DATA_PATH, path) 
        if os.path.isfile(file_path) and file_path.endswith(".json"): 
            with open(file_path, 'r') as file: 
                data = json.load(file) 
                processtext(data)

if __name__ == "__main__":
    main()

#docker run -v ./chroma-data:/data -p 8000:8000 chromadb/chroma
