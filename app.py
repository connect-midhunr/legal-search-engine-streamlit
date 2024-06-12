__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
from components import css, header_template, search_result_template, user_template, bot_template, alert_bot_template, generate_interim_orders_info, generate_judgement_info
from document_QnA import create_text_chunks, create_vector_store, create_chat_conversation
import chromadb
import os
import json
import time
import numpy as np
import pandas as pd
from googletrans import Translator
from py3langid.langid import LanguageIdentifier, MODEL_FILE

from enums import Languages

translator = Translator()
identifier = LanguageIdentifier.from_pickled_model(MODEL_FILE)
identifier.set_languages([language.value for language in Languages])

def load_config(filename):
    with open(filename, 'r') as f:
        config = json.load(f)
    return config

config = load_config('config.json')
db_name = config['database']['chromadb']['database_name']

# Get the absolute path of the current working directory
current_directory = os.getcwd()

client = chromadb.PersistentClient(path=f'{current_directory}/data')
# sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=embedding_model)
doc_collection = client.get_collection(name=db_name)

all_documents = doc_collection.get()
list_of_case_titles = [dictionary['case_title'] for dictionary in all_documents['metadatas']]
list_of_doc_ids = all_documents['ids']
dict_of_options = {list_of_case_titles[num]:list_of_doc_ids[num] for num in range(len(list_of_case_titles))}
            
list_of_languages = ['Detect Language']
list_of_languages.extend([language.title() for language in Languages.__members__.keys()])

# function to stream response message from the bot
def stream_data(message):
    try:
        for word in message.split(" "):
            yield word + " "
            time.sleep(0.02)

    except Exception as e:
        print(f"Exception occured in stream_data: {e}")
        return None
    
# function to detect language of the text
def detect_language(message):
    try:
        print("Detected language:", identifier.classify(message))
        return identifier.classify(message)[0]

    except Exception as e:
        print(f"Exception occured in detect_language: {e}")
        return None

# function to generate user-to-bot chat
def generate_chat_from_user_question(user_question, language = "Detect Language"):
    try:
        lang_code = Languages[language.upper()].value if language.upper() in list(Languages.__members__.keys()) else detect_language(user_question)
        
        if st.session_state.conversation:
            st.session_state.chat_history.append(user_question)
            question = translator.translate(user_question, dest='en').text
            response = st.session_state.conversation({'question': question + "Provide the answer in at least 60 words."})
            answer = translator.translate(response['answer'], dest=lang_code).text
            st.session_state.chat_history.append(answer)
            print(st.session_state.chat_history)

            for i, message in enumerate(st.session_state.chat_history):
                if i % 2 == 0:
                    with st.chat_message("user"):
                        st.write(message)
                else:
                    with st.chat_message("assistant"):
                        if i == len(st.session_state.chat_history) - 1:
                            st.write_stream(stream_data(message))
                        else:
                            st.write(message)

        else:
            st.write(alert_bot_template.replace("{{MSG}}", "Click the 'Process' button before starting the session."), unsafe_allow_html=True)

    except Exception as e:
        print(f"Exception occured in generate_chat_from_user_question: {e}")
        return None
            
# function to retrieve document title and text using document id
def get_doc_title_and_text(doc_id):
    try:
        result = doc_collection.get(ids=[doc_id])
        doc_title = result['metadatas'][0]['case_title']
        doc_text = result['documents'][0]
        return doc_title, doc_text

    except Exception as e:
        print(f"Exception occured in get_doc_title_and_text: {e}")
        return None

if __name__ == '__main__':
    try:
        st.set_page_config(page_title="Legal Docs Search & QnA", page_icon=":robot:")
        st.write(css, unsafe_allow_html=True)

        if "conversation" not in st.session_state:
            st.session_state.conversation = None
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        col1, col2, col3 = st.columns(3)
        with col2:
            st.image(f'{current_directory}/images/collabll-logo.png')

        doc_id = st.query_params.get('docid')
        # print('doc-id:', doc_id)

        # selected_tab = option_menu(
        #     menu_title=None,
        #     options=["Search", "QnA"],
        #     icons=["search", "robot"],
        #     menu_icon="cast",
        #     default_index=0,
        #     orientation="horizontal",
        #     styles={"nav-link-selected": {"background-color": "#2986cc"}}
        # )

        if doc_id:
            st.write(header_template.replace("{{MSG}}", "Legal Docs QnA"), unsafe_allow_html=True)
            st.write("This tab demonstrates the 'Question and Answer' part of the application.")

            doc_title, doc_text = get_doc_title_and_text(doc_id)

            st.write(f'The case you have selected:  \n**{doc_title}**')

            # doc_id = dict_of_options[st.selectbox("Select a case", list(dict_of_options.keys()))]
            # if st.button("Process")
            if not st.session_state.conversation:
                with st.spinner("Processing..."):
                    text_chunks = create_text_chunks(doc_text)
                    vector_store = create_vector_store(text_chunks)
                    st.session_state.conversation = create_chat_conversation(vector_store)

            input, drop_down = st.columns([3, 1])
            with input:
                user_question = st.chat_input("Ask a question about your document")
            with drop_down:
                selected_language = st.selectbox("Select the language", list_of_languages, label_visibility="collapsed")
            if user_question:
                with st.spinner("Generating response..."):
                    generate_chat_from_user_question(user_question, selected_language)

        else:
            st.write(header_template.replace("{{MSG}}", "Legal Docs Search"), unsafe_allow_html=True)
            st.write("This tab demonstrates the 'Search and Find Documents' part of the application.")

            search_document = st.text_input("Search and find relevant documents:")
            if search_document:
                with st.spinner("Loading..."):
                    result = doc_collection.query(query_texts=search_document, n_results=10)
                    # st.write(result)

                    for num in range(len(result['ids'][0])):
                        metadata = result['metadatas'][0][num]
                        doc_id = result['ids'][0][num]
                        result_template = search_result_template.replace("{{CASE_TITLE}}", metadata['case_title'])
                        result_template = result_template.replace("{{CASE_TYPE}}", metadata['case_type'])
                        result_template = result_template.replace("{{CNR_NUMBER}}", metadata['cnr_num'])
                        result_template = result_template.replace("{{INTERIM_ORDERS_URL}}", generate_interim_orders_info(eval(metadata['list_of_interim_order_urls'])))
                        result_template = result_template.replace("{{JUDGEMENT_URL}}", generate_judgement_info(metadata['judgement_url']))
                        result_template = result_template.replace("{{START_QNA_URL}}", doc_id)
                        # print(result_template)
                        st.write(result_template, unsafe_allow_html=True)

    except Exception as e:
        print(f"Exception occured in main: {e}")
            