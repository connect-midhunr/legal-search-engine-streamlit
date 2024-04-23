import chromadb
from chromadb.utils import embedding_functions
import os
from dotenv import load_dotenv

from langchain.text_splitter import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.embeddings.huggingface import HuggingFaceInstructEmbeddings
from langchain.vectorstores.faiss import FAISS
from langchain.memory import ConversationBufferMemory
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain

load_dotenv()
embedding_model = os.getenv('EMBEDDING_MODEL')
db_name = os.getenv('DATABASE_NAME')
openai_api_key = os.getenv('OPENAI_API_KEY')
huggingfacehub_api_key = os.getenv('HUGGINGFACEHUB_API_TOKEN')

# function to identify all line endings in a string.
def get_line_endings(text):
  line_endings = []
  for i, char in enumerate(text):
    if char in ("\n", "\r") and char != "\n\n":
      line_endings.append(text[i-1])
  return line_endings

# function to clean text
def clean_text(text):
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

# function to create text chunks
def create_text_chunks(text):
    text_splitter = CharacterTextSplitter(separator=".\n", chunk_size=1000, chunk_overlap=200, length_function=len)
    chunks = text_splitter.split_text(text)
    return chunks

# function to create vector store
def create_vector_store(text_chunks):
    embedding = OpenAIEmbeddings()
    # embedding = HuggingFaceInstructEmbeddings(model_name="hkunlp/instructor-xl")
    vector_store = FAISS.from_texts(texts=text_chunks, embedding=embedding)
    return vector_store

# function to create conversation of the chatbot
def create_chat_conversation(vector_store):
   memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
   conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=ChatOpenAI(model_name='gpt-3.5-turbo'),
        retriever=vector_store.as_retriever(search_type = "mmr"),
        memory=memory)
   return conversation_chain

if __name__ == '__main__':
    client = chromadb.PersistentClient(path='data')
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=embedding_model)
    doc_collection = client.get_collection(name=db_name)

    result = doc_collection.get(ids=['id_71'])
    doc_text = result['documents'][0]
    # print(doc_text)
    # print()
    # print(clean_text(doc_text))
    # print()

    text_chunks = create_text_chunks(doc_text)
    vector_store = create_vector_store(text_chunks)
    chat_conversation = create_chat_conversation(vector_store)

    response = chat_conversation({'question': 'What is Nourinmol?'})

    print("Type of response:", type(response))
    print("Response:\n", response)