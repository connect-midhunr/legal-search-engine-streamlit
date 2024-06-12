import csv
import os
import shutil
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import PyPDF2
import pdf2image
import easyocr
from datetime import datetime
from io import BytesIO
import time
import json
import spacy

import chromadb
from chromadb.utils import embedding_functions
from langchain.text_splitter import CharacterTextSplitter
from langchain_openai import OpenAI
from langchain_community.llms.ollama import Ollama

from enums import DocumentType

load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY')

def load_config(filename):
    with open(filename, 'r') as f:
        config = json.load(f)
    return config

config = load_config('config.json')
db_name = config['database']['chromadb']['database_name']
openai_model = config['llm_models']['openai_model']
ollama_model = config['llm_models']['ollama_model']
pdf_downloads_foldername = config['folders']['pdf_downloads']

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
def save_pdf_files(case_type, cnr_num, interim_order_url_list, judgement_url):
    try:
        root_directory = os.path.join(os.getcwd(), pdf_downloads_foldername)
        case_folder_name = str(case_type) + '_' + str(cnr_num)
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
    
# function to delete downloads folder
def delete_downloads_folder():
    try:
        directory_path = os.path.join(os.getcwd(), pdf_downloads_foldername)
        if os.path.exists(directory_path):
            shutil.rmtree(directory_path)
            print(f"Directory '{directory_path}' has been deleted.")
        else:
            print(f"Directory '{directory_path}' does not exist.")

    except Exception as e:
        print(f"Exception occured in delete_downloads_folder: {e}")
        return None
    
# function to create document intro from case details
def create_case_intro_from_case_details(case_details):
    try:
        formatted_text = ""
        for key, value in case_details.items():
            if key == 'Judgement URL':
                key = "URL of Judgement in PDF file format"
            if key == 'List of Interim Order URLs':
                key = "List of URLs of Interim Order in PDF file format"
            if isinstance(value, str):
                try:
                    parsed_value = eval(value)
                    if isinstance(parsed_value, list):
                        formatted_text += f"{key}"
                        if parsed_value:
                            for i, value_inside_list in enumerate(parsed_value):
                                formatted_text += f"\n{i+1}.\t"
                                if isinstance(value_inside_list, dict):
                                    value_inside_list.pop('#')
                                    formatted_text += "\n\t".join([f"{key}: {value}" for key, value in value_inside_list.items()])
                                else:
                                    formatted_text += value_inside_list
                            formatted_text += "\n"
                        else:
                            formatted_text += f": Records not available\n"
                    else:
                        formatted_text += f"{key}: {parsed_value}\n"
                except (SyntaxError, NameError, KeyError, TypeError, KeyError) as e:
                    if not value:
                        value = "Information not available"
                    formatted_text += f"{key}: {value}\n"
            else:
                formatted_text += f"{key}: {value}\n"
            if key in ('Case Status', 'Bench', 'History of Case Hearings', 'URL of Judgement in PDF file format'):
                formatted_text += f"{25*'-'}\n"
        
        return formatted_text

    except Exception as e:
        print(f"Exception occured in create_case_intro_from_case_details: {e}")
        return None
    
# function to count number of images in a pdf file
def get_num_of_images_in_pdf_file(filename):
    try:
        image_count = 0

        with open(filename, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(filename)

            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                x_objects = page['/Resources']['/XObject']

                for obj_key in x_objects.keys():
                    obj = x_objects[obj_key]
                    
                    # Check if the object is an image
                    if obj.get('/Subtype') == '/Image':
                        width = obj.get('/Width')
                        height = obj.get('/Height')
                        
                        # Check if image dimensions meet the criteria
                        if width and height and width > 1240 and height > 1754:
                            image_count += 1

        return image_count

    except Exception as e:
        print(f"Exception occured in get_num_of_images_in_pdf_file: {e}")
        return None

# function to extract text from images in a pdf file
def extract_text_from_images_in_pdf_file(filename):
    try:
        text = ""
        images = pdf2image.convert_from_path(filename)
        for image in images:
            # print(f"Type of image: {type(image)}")
            image_data = b''
            with BytesIO() as output:
                image.save(output, format='JPEG')
                image_data = output.getvalue()
                # print(f"Type of image_data: {type(image_data)}")
            reader = easyocr.Reader(['en'])
            result = reader.readtext(image_data)

            for line in result:
                text += line[1] + '\n'
        return text

    except Exception as e:
        print(f"Exception occured in extract_text_from_images_in_pdf_file: {e}")
        return None

# function to extract from a pdf file
def extract_text_from_pdf_file(filename):
    try:
        pdf_reader = PyPDF2.PdfReader(filename)

        num_of_images = get_num_of_images_in_pdf_file(filename)
        print(f"Image Count: {num_of_images}")
        if num_of_images > 0:
            text = extract_text_from_images_in_pdf_file(filename)
        else:
            text = ""
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text()
        
        return text

    except Exception as e:
        print(f"Exception occured in extract_text_from_pdf_file: {e}")
        return None

# function to format, summarize and chunk the text content of documents
def format_document_text_content(doc_content, doc_type):
    try:
        # if doc_type == DocumentType.INTERIM_ORDER:
        #     prompt = f"""
        #             Provide the full details from this legal text including the full details of court, judge, date, case type, suit number, 
        #             Interlocutory Application, all plaintiff and defendant involved and their advocates (deleted parties must also be included), 
        #             order (need the full content of order), etc. The legal text is given below:

        #             {doc_content}

        #             Exclude intro and outro generated by you.
        #         """
        # elif doc_type == DocumentType.JUDGEMENT:
        #     prompt = f"""
        #             Provide the full details from this legal text including the full details of court, judge, date, case type, suit number, 
        #             all plaintiff and defendant involved and their advocates (deleted parties must also be included), judgement, etc. 
        #             The legal text is given below:

        #             {doc_content}

        #             Exclude intro and outro generated by you.
        #         """
        # else:
        #     return ''
        
        # # llm = OpenAI(model=openai_model)
        # llm = Ollama(model=ollama_model, temperature=0.75)
        # formatted_text = llm(prompt)
        # print("Summarized text", doc_type.value, "printed successfully")
        # # print(25*'-')
        # # print(summarized_text)
        
        # # summarized_text = """Court: High Court of Kerala at Ernakulam
        # #     Judge: The Honourable Mr. Justice Devan Ramachandran
        # #     Date: Wednesday, the 5th day of April 2023 / 15th Chaitra, 1945 (March-April in Hindu calendar)
        # #     Case Type: Admiralty Suit
        # #     Suit Number: ADML.S. NO. 4 OF 2023
        # #     Plaintiff: Adani Global Pte Ltd
        # #     Address of Plaintiff's Office: 3 Anson Road, 22-01, Spring Leaf Tower, Singapore
        # #     Representative(s):
        # #     Rishi Srivastava (Authorized Representative)
        # #     - Video Board Resolution dated 14/06/2022
        # #         - Mr. Banke Bihari Lal (Residing at 03/19/221, Shakti Vihar Colony, Behind ICICI Bank, Naya Banda, Uttar
        # #     Pradesh, India, PIN - 79909)
        # #     VIPIN P.VARGHESE (Advocate)
        # #     - Associates:
        # #         - V.J.MATHEW (SR.)
        # #         - Celine John
        # #         - Mehnaaz P. Mohammed
        # #         - Aniruddha G. Kamath
        # #         - Adarsh Mathéw

        # #     Defendant(s):
        # #     1. M.V. Maranara IMO 9733117 (Formerly World Dream T/A Marshall Islands Flagship)
        # #     Address: Cochin Port Authority, Willingdon Island, Kochi, PIN - 682003

        # #     Date of Judgment: 2023:KER:22439

        # #     Judgement Details:
        # #     The Suit was not pressed as the defendant vessel did not arrive at the Port of Cochin.
        # #     The suit is dismissed and permission to reopen it in the future granted, with court fees refunded to the
        # #     plaintiff according to rules on limitation periods."""

        nlp = spacy.load("en_core_web_sm")
        doc = nlp(doc_content)
        sentences = [sent.text.strip() for sent in doc.sents]
        formatted_text = '\n'.join([' '.join(sentence.split('\n')) for sentence in sentences])
        
        text_splitter = CharacterTextSplitter(separator="\n", chunk_size=1000, chunk_overlap=200, length_function=len)
        chunks = text_splitter.split_text(formatted_text)
        return f"\n{25*'-'}\n".join(chunks)

    except Exception as e:
        print(f"Exception occured in format_document_text_content: {e}")
        return None

# function to extract and combine text from all pdf files in the case
def create_document_text_content(case_details):
    try:
        case_intro = create_case_intro_from_case_details(case_details)
        pdf_text = case_intro

        case_type = case_details['Case Type']
        cnr_num = case_details['CNR Number']
        list_of_interim_order_urls = eval(case_details['List of Interim Order URLs'])
        judgement_url = case_details['Judgement URL']

        interim_order_filename_list, judgement_filename = save_pdf_files(case_type, cnr_num, list_of_interim_order_urls, judgement_url)
        # print("interim_order_filename_list:", interim_order_filename_list)
        # print("judgement_filename:", judgement_filename)

        if interim_order_filename_list:
            for i, filename in enumerate(interim_order_filename_list):
                text = extract_text_from_pdf_file(filename)
                pdf_text = pdf_text + '\n' + f'Interim Order No. {i+1} is given below.\n\n' + format_document_text_content(text, DocumentType.INTERIM_ORDER) + '\n' + 25*'-' + '\n'

        if judgement_filename:
            text = extract_text_from_pdf_file(judgement_filename)
            pdf_text = pdf_text + f'Judgement is given below.\n\n' + format_document_text_content(text, DocumentType.JUDGEMENT) + '\n' + 25*'-' + '\n'

        delete_downloads_folder()

        return pdf_text.strip()

    except Exception as e:
        print(f"Exception occured in create_document_text_content: {e}")
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
    client = chromadb.PersistentClient(path="data")
    # sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=embedding_model)
    doc_collection = client.get_or_create_collection(name=db_name)

    list_of_court_cases = csv_to_list_of_dicts('output.csv')
    # demo_data = {'CI Number': 'KLHC010000012011', 'CNR Number': '200100000012011', 'Case Number': 'Adml.S. 1/2011', 'Case Title': 'UNICORN MARINE SERVICES PVT.LTD.v/sOWNERS AND PARTIES INTERESTED IN THE VES', 'Case Type': 'Adml.S.', 'Case Status': 'DISPOSED', 'Filing Date': '06-05-2011', 'Registration Date': '06-05-2011', 'Under Act(s)': 'act1', 'Under Section(s)': 'sec1', 'Petitioner': 'UNICORN MARINE SERVICES PVT.LTD.', 'Respondent': 'OWNERS AND PARTIES INTERESTED IN THE VES', 'Judge': 'HONOURABLE MR.JUSTICE HARUN-UL-RASHID', 'Bench': 'bench1', 'History of Case Hearings': "[{'#': '1', 'Cause List Type': 'Daily List', 'Hon: Judge Name': 'HONOURABLE MR.JUSTICE P.BHAVADASAN', 'BusinessDate': '25-11-2011', 'NextDate(Tentative Date)': '04-05-2012', 'Purpose of Hearing': 'PETITIONS', 'Order': 'o1'}, {'#': '2', 'Cause List Type': 'Part Two', 'Hon: Judge Name': 'HONOURABLE MR.JUSTICE N.K.BALAKRISHNAN', 'BusinessDate': '04-05-2012', 'NextDate(Tentative Date)': '21-06-2012', 'Purpose of Hearing': 'PETITIONS', 'Order': 'o2'}, {'#': '3', 'Cause List Type': 'Part Two', 'Hon: Judge Name': 'HONOURABLE MR.JUSTICE HARUN-UL-RASHID', 'BusinessDate': '21-06-2012', 'NextDate(Tentative Date)': '22-06-2012', 'Purpose of Hearing': 'PETITIONS', 'Order': 'o3'}, {'#': '4', 'Cause List Type': 'Daily List', 'Hon: Judge Name': '2963-HONOURABLE THE AG.CHIEF JUSTICE MR.M.M.PAREED PILLAY', 'BusinessDate': '22-06-2012', 'NextDate(Tentative Date)': '26-06-2012', 'Purpose of Hearing': 'FOR SETTLEMENT', 'Order': 'o4'}, {'#': '5', 'Cause List Type': 'Part Two', 'Hon: Judge Name': 'HONOURABLE MR.JUSTICE HARUN-UL-RASHID', 'BusinessDate': '26-06-2012', 'NextDate(Tentative Date)': '26-06-2012', 'Purpose of Hearing': 'FOR ORDERS', 'Order': 'o5'}, {'#': '6', 'Cause List Type': 'type1', 'Hon: Judge Name': 'HONOURABLE MR.JUSTICE HARUN-UL-RASHID', 'BusinessDate': '26-06-2012', 'NextDate(Tentative Date)': 'date1', 'Purpose of Hearing': 'pup1', 'Order': 'o6'}]", 'Judgement Date': '26-06-2012', 'List of Interim Order URLs': "['https://hckinfo.kerala.gov.in/digicourt/Casedetailssearch/fileviewcitation?token=MjAwMTAwMDAwMDEyMDExXzEucGRm+&lookups=b3JkZXJzLzIwMTE=+&citationno=MjAxMjpLRVI6MjQ4OTU=', 'https://hckinfo.kerala.gov.in/digicourt/Casedetailssearch/fileviewcitation?token=MjAwMTAwMDAwMDEyMDExXzEucGRm+&lookups=b3JkZXJzLzIwMTE=+&citationno=MjAxMjpLRVI6MjQ4OTU=', 'https://hckinfo.kerala.gov.in/digicourt/Casedetailssearch/fileviewcitation?token=MjAwMTAwMDAwMDEyMDExXzEucGRm+&lookups=b3JkZXJzLzIwMTE=+&citationno=MjAxMjpLRVI6MjQ4OTU=']", 'Judgement URL': 'https://hckinfo.kerala.gov.in/digicourt/Casedetailssearch/fileviewcitation?token=MjAwMTAwMDAwMDEyMDExXzEucGRm+&lookups=b3JkZXJzLzIwMTE=+&citationno=MjAxMjpLRVI6MjQ4OTU='}
    # print(demo_data)
    # print()
    # print(create_document_text_content(list_of_court_cases[70]))
    
    for i, case_details in enumerate(list_of_court_cases):
        print(create_document_text_content(case_details))
        # case_type = case_details['Case Type']
        # cnr_num = case_details['CNR Number']
        # case_title = case_details['Case Title']
        # list_of_interim_order_urls = eval(case_details['List of Interim Order URLs'])
        # judgement_url = case_details['Judgement URL']

        # print("Case no. ", i+1, ":", cnr_num)

        # doc_collection.add(
        #     documents=[create_document_text_content(case_details)],
        #     metadatas=[{"case_type": str(case_type), "cnr_num": str(cnr_num), "case_title": str(case_title), "list_of_interim_order_urls": f"{list_of_interim_order_urls}", "judgement_url": str(judgement_url)}],
        #     ids=[f"id_{i+1}"]
        # )
        # print(type(extract_and_join_text_from_pdfs(cnr_num, list_of_interim_order_urls, judgement_url)))
        print()

    # keyword = "nourinmol"
    # print(f"Searching for '{keyword}'...")
    # print()
    # result = doc_collection.query(
    #     query_texts=keyword,
    #     n_results=10
    # )
    # # print("Result:", result['documents'][0])
    # print("Type of Result:", type(result['documents'][0]))
    # print("Length of Result:", len(result['documents'][0]))
    # print()

    # # # print("Peek:", doc_collection.peek())
    # print("Count:", doc_collection.count())
    # print()

    # for element in result['metadatas'][0]:
    #     print(f"Metadata: {element['case_type']} {element['cnr_num']} {element['case_title']} {eval(element['list_of_interim_order_urls'])} {element['judgement_url']}")
    #     print()

    # for element in result['ids'][0]:
    #     print(element)
    
    # for i, element in enumerate(result['documents'][0]):
    #     write_document_content_to_txt_file(i, element)

    # all_documents = doc_collection.get()
    # list_of_case_titles = [dictionary["case_title"] for dictionary in all_documents['metadatas']]
    # list_of_doc_ids = all_documents['ids']
    # dict_of_options = {list_of_case_titles[num]:list_of_doc_ids[num] for num in range(len(list_of_case_titles))}
    # print(dict_of_options)

    # client.delete_collection(name=db_name)