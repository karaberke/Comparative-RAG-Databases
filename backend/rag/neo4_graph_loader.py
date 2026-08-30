from tokenize import Triple
import nest_asyncio
from typing import List, Literal, Tuple
from llama_index.core.indices.property_graph import SchemaLLMPathExtractor
from dotenv import load_dotenv
import os
from llama_index.llms.openai_like import OpenAILike
from llama_index.llms.ollama import Ollama
from llama_index.core import SimpleDirectoryReader
from llama_index.core.node_parser import (
    SentenceSplitter,
    SemanticSplitterNodeParser,
)
from llama_index.core import PropertyGraphIndex
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.graph_stores.neo4j import Neo4jPropertyGraphStore
import re
from openai import OpenAI

nest_asyncio.apply()
load_dotenv()

INPUT_PATH=r"./backend/rag/input/"
DENSE_MODEL="bge-m3"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
API_URL=os.environ.get("OPENAI_API_URL")


embed_model = OpenAIEmbedding(model_name=DENSE_MODEL,api_base=API_URL,api_key=OPENAI_API_KEY)
splitter = SemanticSplitterNodeParser(
    buffer_size=1, breakpoint_percentile_threshold=95, embed_model=embed_model
)
base_splitter = SentenceSplitter(chunk_size=512)

llm_instance = Ollama(
        model="llama3",
        request_timeout=3600,
        context_window=10000,
    )


llm_instance2 = OpenAILike(
    model="Mistral-Small-3.2-24B-Instruct-2506",
    api_base=API_URL,
    api_key=OPENAI_API_KEY,
    context_window=128000,
    is_chat_model=True,
    is_function_calling_model=False,
)

graph_store = Neo4jPropertyGraphStore(
    username=os.environ.get("NEO4J_USERNAME"),
    password=os.environ.get("NEO4J_PASSWORD"),
    url=os.environ.get("NEO4J_URL"),
)

def clean(text):
    cleaned_text = text.replace('{', '').replace('}', '')
    cleaned_text = cleaned_text.replace('\n',' ').replace('\t',' ')
    cleaned_text = cleaned_text.replace('�',' ').replace('\u00a0',' ')
    cleaned_text = cleaned_text.replace('([[', ')').replace(']])', ')')
    return cleaned_text

def replace_urls_with_placeholder(text):
    # Regular expression to match URLs
    url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
    # Replace all URLs found with the string "URL"
    replaced_text = re.sub(url_pattern, 'URL', text)
    return replaced_text

def add_nodes(nodes):
    # best practice to use upper-case
    entities = Literal[
    "PRODUCT",
    "MARKET",
    "TECHNOLOGY",
    "EVENT",
    "CONCEPT",
    "ORGANIZATION",
    "PERSON",
    "LOCATION",
    "TIME",
    "MISCELLANEOUS",
    "PROCEDURE",
    "REGULATION",
]
    
    relations = Literal[
        "HAS",
        "PART_OF",
        "WORKED_ON",
        "WORKED_WITH",
        "WORKED_AT",
        "USED_BY",
        "USED_FOR",
        "LOCATED_IN",
        "IS_A",
        "BORN_IN",
        "DIED_IN",
        "GOVERNED_BY",
        "APPLIES_TO"
    ]
    
    Triple = Tuple[str, str, str]
    validation_schema: List[Triple] = [ # type: ignore
        ("PRODUCT", "USED_BY", "PRODUCT"),
        ("PRODUCT", "USED_FOR", "MARKET"),
        ("PRODUCT", "HAS", "TECHNOLOGY"),
        ("MARKET", "LOCATED_IN", "LOCATION"),
        ("MARKET", "HAS", "TECHNOLOGY"),
        ("TECHNOLOGY", "USED_BY", "PRODUCT"),
        ("TECHNOLOGY", "USED_FOR", "MARKET"),
        ("TECHNOLOGY", "LOCATED_IN", "LOCATION"),
        ("TECHNOLOGY", "PART_OF", "ORGANIZATION"),
        ("TECHNOLOGY", "IS_A", "PRODUCT"),
        ("EVENT", "LOCATED_IN", "LOCATION"),
        ("EVENT", "PART_OF", "ORGANIZATION"),
        ("CONCEPT", "USED_BY", "TECHNOLOGY"),
        ("CONCEPT", "USED_FOR", "PRODUCT"),
        ("ORGANIZATION", "LOCATED_IN", "LOCATION"),
        ("ORGANIZATION", "PART_OF", "ORGANIZATION"),
        ("ORGANIZATION", "PART_OF", "MARKET"),
        ("PERSON", "BORN_IN", "LOCATION"),
        ("PERSON", "BORN_IN", "TIME"),
        ("PERSON", "DIED_IN", "LOCATION"),
        ("PERSON", "DIED_IN", "TIME"),
        ("PERSON", "WORKED_ON", "EVENT"),
        ("PERSON", "WORKED_ON", "PRODUCT"),
        ("PERSON", "WORKED_ON", "CONCEPT"),
        ("PERSON", "WORKED_ON", "TECHNOLOGY"),
        ("LOCATION", "LOCATED_IN", "LOCATION"),
        ("LOCATION", "PART_OF", "LOCATION"),
        ("PROCEDURE", "USED_FOR", "PRODUCT"),
        ("PROCEDURE", "USED_FOR", "TECHNOLOGY"),
        ("PROCEDURE", "USED_BY", "ORGANIZATION"),
        ("PROCEDURE", "PART_OF", "REGULATION"),
        ("PROCEDURE", "LOCATED_IN", "LOCATION"),
        ("REGULATION", "GOVERNED_BY", "ORGANIZATION"),
        ("REGULATION", "APPLIES_TO", "PRODUCT"),
        ("REGULATION", "APPLIES_TO", "TECHNOLOGY"),
        ("REGULATION", "LOCATED_IN", "LOCATION"),
    ]

    kg_extractor = SchemaLLMPathExtractor( 
        llm=llm_instance, 
        possible_entities=entities, 
        possible_relations=relations, 
        kg_validation_schema=validation_schema, 
        strict=False, ) 
  
    index = PropertyGraphIndex.from_existing( 
        embed_model=embed_model,
        kg_extractors=[kg_extractor] ,
        property_graph_store=graph_store, 
        show_progress=True, )
    try:
        index.insert_nodes(nodes)
    except:
        print(nodes[0])
        print("-"*100)
        print(nodes[0].get_content())

def main():
    documents = SimpleDirectoryReader(INPUT_PATH).load_data()
    nodes=splitter.get_nodes_from_documents(documents)
    for i,node in enumerate(nodes):
        print(i)
        content=node.get_content()
        if content and len(content.split()) > 2:
            content = replace_urls_with_placeholder(content)
            content = clean(content)
            node.set_content(content)
        add_nodes([node])

openai_client = OpenAI(
    api_key = os.getenv("OPENAI_API_KEY"),
    base_url = os.getenv("OPENAI_API_URL")
)

if __name__ == "__main__":
    main()