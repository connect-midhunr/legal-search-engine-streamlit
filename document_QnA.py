import chromadb
from chromadb.utils import embedding_functions
import os
from dotenv import load_dotenv
import json

from langchain.text_splitter import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.memory import ConversationBufferMemory
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
from langchain_community.llms.ollama import Ollama
from langchain_community.llms.huggingface_hub import HuggingFaceHub
from langchain_google_genai import ChatGoogleGenerativeAI
import google.generativeai as genai

load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY')
huggingfacehub_api_token = os.getenv('HUGGINGFACEHUB_API_TOKEN')
google_api_key = os.getenv('GOOGLE_API_KEY')

def load_config(filename):
    with open(filename, 'r') as f:
        config = json.load(f)
    return config

config = load_config('config.json')
db_name = config['database']['chromadb']['database_name']
huggingfacehub_embedding_model = config['embedding_models']['faiss_embedding_model']
openai_model = config['llm_models']['openai_model']
ollama_model = config['llm_models']['ollama_model']

genai.configure(api_key=google_api_key)

# print(f"OpenAI key: {openai_api_key}")

# function to identify all line endings in a string.
def get_line_endings(text):
  try:
    line_endings = []
    for i, char in enumerate(text):
      if char in ("\n", "\r") and char != "\n\n":
        line_endings.append(text[i-1])
    return line_endings

  except Exception as e:
      print(f"Exception occured in get_line_endings: {e}")
      return None

# function to clean text
def clean_text(text):
  try:
    cleaned_text = ""
    # Iterate through each line in the text
    for line in text.splitlines():
      # Check if the line ends with a space or hyphen
      if line.endswith(""):
        # If it does, concatenate with the next line without a newline
        cleaned_text += line[:-1]
      else:
        # If not, add a newline and the current line
        cleaned_text += line + "\n"
    return cleaned_text

  except Exception as e:
      print(f"Exception occured in clean_text: {e}")
      return None

# function to create text chunks
def create_text_chunks(text):
  try:
    chunks = text.split(25*'-')
    # for chunk in chunks:
    #   print(chunk)
    #   print(25*'*')
    return text.split(25*'-')

  except Exception as e:
    print(f"Exception occured in create_text_chunks: {e}")
    return None

# function to create vector store
def create_vector_store(text_chunks):
  try:
    # embedding = OpenAIEmbeddings()
    embedding = HuggingFaceBgeEmbeddings(model_name=huggingfacehub_embedding_model, model_kwargs={"device": "cpu"}, encode_kwargs={"normalize_embeddings": True})
    vector_store = FAISS.from_texts(texts=text_chunks, embedding=embedding)
    return vector_store

  except Exception as e:
    print(f"Exception occured in create_vector_store: {e}")
    return None

# function to create conversation of the chatbot
def create_chat_conversation(vector_store):
  try:
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    # llm = ChatOpenAI(model_name=openai_model)
    # llm = Ollama(model=ollama_model, temperature=0.6)
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest")
    # llm = HuggingFaceHub(repo_id="microsoft/Phi-3-small-128k-instruct", huggingfacehub_api_token=huggingfacehub_api_token)
    conversation_chain = ConversationalRetrievalChain.from_llm(
          llm=llm,
          retriever=vector_store.as_retriever(search_type = "mmr"),
          memory=memory)
    return conversation_chain

  except Exception as e:
    print(f"Exception occured in create_chat_conversation: {e}")
    return None

if __name__ == '__main__':
    client = chromadb.PersistentClient(path='data')
    # sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=chromadb_embedding_model)
    doc_collection = client.get_collection(name=db_name)

    result = doc_collection.get(ids=['id_25'])
    doc_text = result['documents'][0]
    # print(doc_text)
    # print()
    # print(clean_text(doc_text))
    # print()

    text_chunks = create_text_chunks(doc_text)
    # vector_store = create_vector_store(text_chunks)
    # chat_conversation = create_chat_conversation(vector_store)

    # response = chat_conversation({'question': 'What is Nourinmol?'})

    # print("Type of response:", type(response))
    # print("Response:\n", response)