import streamlit as st
from components import css, user_template, bot_template
from document_QnA import create_text_chunks, create_vector_store, create_chat_conversation
import chromadb
from chromadb.utils import embedding_functions
import os
import sys
from dotenv import load_dotenv

__import__('pysqlite3')
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

load_dotenv()
embedding_model = os.getenv('EMBEDDING_MODEL')
db_name = os.getenv('DATABASE_NAME')
openai_api_key = os.getenv('OPENAI_API_KEY')
huggingfacehub_api_key = os.getenv('HUGGINGFACEHUB_API_TOKEN')

# Get the absolute path of the current working directory
current_directory = os.getcwd()

client = chromadb.PersistentClient(path=f'{current_directory}/data')
# sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=embedding_model)
doc_collection = client.get_collection(name=db_name)

all_documents = doc_collection.get()
list_of_case_titles = [dictionary['case_title'] for dictionary in all_documents['metadatas']]
list_of_doc_ids = all_documents['ids']
dict_of_options = {list_of_case_titles[num]:list_of_doc_ids[num] for num in range(len(list_of_case_titles))}

# function to generate user-to-bot chat
def generate_chat_from_user_question(user_question):
    response = st.session_state.conversation({'question': user_question})
    st.session_state.chat_history = response['chat_history']

    for i, message in enumerate(st.session_state.chat_history):
        if i % 2 == 0:
            st.write(user_template.replace(
                "{{MSG}}", message.content), unsafe_allow_html=True)
        else:
            st.write(bot_template.replace(
                "{{MSG}}", message.content), unsafe_allow_html=True)
            
# function to retrieve document text using document id
def get_doc_text(doc_id):
    result = doc_collection.get(ids=['id_71'])
    doc_text = result['documents'][0]
    return doc_text

if __name__ == '__main__':
    st.set_page_config(page_title="Chat with Court Docs",
                       page_icon=":books:")
    st.write(css, unsafe_allow_html=True)

    if "conversation" not in st.session_state:
        st.session_state.conversation = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = None

    st.header("Chat with Selected Case")
    doc_id = dict_of_options[st.selectbox("Select a case", list(dict_of_options.keys()))]
    if st.button("Process"):
        with st.spinner("Processing"):
            doc_text = get_doc_text(doc_id)
            text_chunks = create_text_chunks(doc_text)
            vector_store = create_vector_store(text_chunks)
            st.session_state.conversation = create_chat_conversation(vector_store)

    user_question = st.text_input("Ask a question about your documents:")
    if user_question:
        generate_chat_from_user_question(user_question)
        