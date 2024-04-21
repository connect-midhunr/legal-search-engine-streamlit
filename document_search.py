import csv
import os
import glob
import requests
from bs4 import BeautifulSoup
import PyPDF2
from datetime import datetime

import chromadb
from chromadb.utils import embedding_functions

import time

# function to convert a CSV file to a list of dictionaries
def csv_to_list_of_dicts(csv_file):
    try:
        data = []
        with open(csv_file, "r") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                data.append(dict(row))  # Convert each row dictionary to a dictionary
    
        return data
    except Exception as e:
        print(f"Exception occured in csv_to_list_of_dicts: {e}")
        return None
    
# function to get the url of pdf file
def get_pdf_file_url(file_url):
    try:
        # fetch the HTML content of the website
        response = requests.get(file_url)
        response.raise_for_status()  # Check for any HTTP errors
        # extract the HTML content from the response
        html_content = response.content
        # create a BeautifulSoup object
        soup = BeautifulSoup(html_content, 'html.parser')
        # Find the <object> tag
        object_tag = soup.find('object')
        # Extract the value of the data attribute
        pdf_url = object_tag.get('data')
        return pdf_url
    except Exception as e:
        print(f"Exception occured in get_pdf_file_url: {e}")
        return None
    
# function to get the content of pdf file
def get_pdf_file_content(pdf_url):
    try:
        # send a GET request to the URL
        response = requests.get(pdf_url)
        response.raise_for_status()  # Check for any HTTP errors
        return response.content
    except Exception as e:
        print(f"Exception occured in get_pdf_file_content: {e}")
        return None

# function to write pdf file
def write_pdf_file(folderpath, url):
    try:
        if len(url) > 0:
            pdf_url = get_pdf_file_url(url)
            # print("Entering function...")
            if pdf_url:
                # print("Entered function...")
                pdf_content = get_pdf_file_content(pdf_url)
                if pdf_content:
                    filename = pdf_url.split('/')[-1]
                    file_path = os.path.join(folderpath, filename)
                    
                    # write the content of the response to a PDF file
                    with open(file_path, 'wb') as f:
                        f.write(pdf_content)
                        # print(file_path, "is written.")

                    # print("Type of path:", type(file_path))
                    return file_path
    except Exception as e:
        print(f"Exception occured in write_pdf_file: {e}")
        return None
    
# function to download and save files
def save_pdf_files(cnr_num, interim_order_url_list, judgement_url):
    try:
        root_directory = 'documents'
        case_folder_name = str(cnr_num) + "_" + datetime.now().strftime("%d%m%Y%m%H%M%S%f")[:-3]
        # print('case_folder_name:', case_folder_name)
        interim_orders_folder_name = 'interim orders'

        interim_orders_folderpath = root_directory + '/' + case_folder_name + '/' + interim_orders_folder_name
        judgement_folderpath = root_directory + '/' + case_folder_name

        # create folders if does not exist
        if not os.path.exists(interim_orders_folderpath):
            os.makedirs(interim_orders_folderpath)

        interim_order_filename_list = []
        for url in interim_order_url_list:
            interim_order_filename_list.append(write_pdf_file(interim_orders_folderpath, url))
            # print('interim_order_filename_list', interim_order_filename_list)

        judgement_filename = write_pdf_file(judgement_folderpath, judgement_url)
        print("PDF files saved successfully...")

        return interim_order_filename_list, judgement_filename
    except Exception as e:
        print(f"Exception occured in save_pdf_files: {e}")
        return None

# function to extract and combine text from all pdf files in the case
def extract_and_join_text_from_pdfs(cnr_num, list_of_interim_order_urls, judgement_url):
    try:
        interim_order_filename_list, judgement_filename = save_pdf_files(cnr_num, list_of_interim_order_urls, judgement_url)
        # print("interim_order_filename_list:", interim_order_filename_list)
        # print("judgement_filename:", judgement_filename)
        list_of_filenames = []
        list_of_filenames.extend(interim_order_filename_list)
        if judgement_filename:
            list_of_filenames.append(judgement_filename)
        # print("list_of_filenames:", list_of_filenames)

        pdf_text = ''
        if list_of_filenames:
            for filename in list_of_filenames:
                pdf_reader = PyPDF2.PdfReader(filename)

                # Extract text from all pages (modify for specific page extraction)
                text = ""
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text()

                pdf_text = pdf_text + '\n\n' + text

        return pdf_text.strip()
    except Exception as e:
        print(f"Exception occured in extract_and_join_text_from_pdfs: {e}")
        return None
    
# function to write document text to a txt file
def write_document_content_to_txt_file(i, element):
    try:
        if not os.path.exists("search_results"):
            os.makedirs("search_results")
        file_path = f'search_results/document_{i}.txt'
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(str(element))
        print(f"Content has been written to '{file_path}' successfully.")
    except Exception as e:
        print(f"Exception occured in write_document_content_to_txt_file: {e}")
        return None

if __name__ == '__main__':
    list_of_court_cases = csv_to_list_of_dicts('output.csv')
    
    doc_text_list = []
    metadata_list = []
    for court_case in list_of_court_cases:
        case_type = court_case['Case Type']
        cnr_num = court_case['CNR Number']
        list_of_interim_order_urls = eval(court_case['List of Interim Order URLs'])
        judgement_url = court_case['Judgement URL']

        doc_text_list.append(extract_and_join_text_from_pdfs(cnr_num, list_of_interim_order_urls, judgement_url))
        metadata_list.append({"caseType": str(case_type), "cnr_num": str(cnr_num), "list_of_interim_order_urls": f"{list_of_interim_order_urls}", "judgement_url": str(judgement_url)})

        # print(cnr_num)
        # print(type(extract_and_join_text_from_pdfs(cnr_num, list_of_interim_order_urls, judgement_url)))
        # print()

    # print("doc_text_list:", doc_text_list)
    # print("metadata_list:", metadata_list)

    client = chromadb.PersistentClient(path="data")
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-mpnet-base-v2")
    doc_collection = client.create_collection(name="documents_db", embedding_function=sentence_transformer_ef)

    doc_collection.add(
        documents=doc_text_list,
        metadatas=metadata_list,
        ids=[f"id_{num}" for num in range(1, len(doc_text_list)+1)]
    )

    # print("Peek:", doc_collection.peek())
    print("Count:", doc_collection.count())
    print()

    # keyword = "compensation for collision"
    # print(f"Searching for '{keyword}'...")
    # print()
    # result = doc_collection.query(
    #     query_texts=keyword,
    #     n_results=10
    # )
    # print("Result:", result['documents'][0])
    # print("Result:", type(result['documents'][0]))
    # print("Result:", len(result['documents'][0]))
    # print()

    # for element in result['metadatas'][0]:
    #     print(f"Metadata: {element['caseType']} {element['cnr_num']} {eval(element['list_of_interim_order_urls'])} {element['judgement_url']}")
    #     # print("Metadata:", type(element))
    
    # for i, element in enumerate(result['documents'][0]):
    #     write_document_content_to_txt_file(i, element)

    # client.delete_collection(name="documents_db")