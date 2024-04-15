import requests
import webbrowser
from bs4 import BeautifulSoup
import os
import time

# function to write a string to a TXT file
def write_string_to_txt_file(string_content):
    try:
        file_path = 'temp.txt'
        with open(file_path, 'w') as file:
            file.write(string_content)
        print(f"Content has been written to '{file_path}' successfully.")
    except IOError as e:
        print(f"Error writing to file: {e}")

# url of Kerala High Court website page with case details searched using case type
url = 'https://hckinfo.kerala.gov.in/digicourt/Casedetailssearch/Statuscasetype'

# function to check if a website exists at the url
def check_website_exists(url):
    try:
        response = requests.head(url)
        return response.status_code == 200
    except requests.ConnectionError:
        return False

# function to open the website at the url in web browser
def open_website(url):
    webbrowser.open(url)

# function to create a BeautifulSoup object of the website in the url
# to enable web scraping
def create_soup_object(url):
    try:
        # fetch the HTML content of the website
        response = requests.get(url)
        # raise an exception if the request was not successful
        response.raise_for_status()
        # create a BeautifulSoup object
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup
    except requests.RequestException as e:
        print("Error fetching content(create_soup_object):", e)
        return None
    
# function to get search results of cases using case type and year
def get_case_results_casetype_year(casetype, year):
    try:
        # make a POST request to the API with the provided data
        api_url = 'https://hckinfo.kerala.gov.in/digicourt/Casedetailssearch/Stausbycasetype'
        response = requests.post(api_url, data={'case_type': casetype, 'case_year': year})
        response.raise_for_status()  # Check for any HTTP errors
        
        # extract the HTML content from the response
        html_content = response.content
        # create a BeautifulSoup object
        soup = BeautifulSoup(html_content, 'html.parser')
        return soup
    except requests.RequestException as e:
        print("Error fetching content(get_case_results_casetype_year):", e)
        return None
    
# function to extract CI numbers and case numbers from a search result
def extract_cinum_casenum(result_soup):
    try:
        # find all buttons with class 'btn btn-primary'
        result_buttons = result_soup.find_all('button', class_='btn btn-primary')
        # extract the values of the onclick attribute
        cinum_casenum_list = [button.get('onclick').replace("'", "").replace(");", "")[button.get('onclick').find("(")+1:button.get('onclick').find(")")].split(',') for button in result_buttons]

        return cinum_casenum_list
    except Exception as e:
        print("Error fetching content(extract_cinum_casenum):", e)
        return None
    
# function to get case details from CI number and case number
def get_case_details_cinum_casenum(cinum, casenum):
    try:
        # make a POST request to the API with the provided data
        api_url = 'https://hckinfo.kerala.gov.in/digicourt/Casedetailssearch/Viewcasestatus'
        response = requests.post(api_url, data={'cino': cinum, 'case_no': casenum})
        response.raise_for_status()  # Check for any HTTP errors
        
        # extract the HTML content from the response
        html_content = response.content
        # create a BeautifulSoup object
        soup = BeautifulSoup(html_content, 'html.parser')
        return soup
    except requests.RequestException as e:
        print("Error fetching content(get_case_details_cinum_casenum):", e)
        return None
    
# function to extract token, lookup and root user of interim orders
def extract_token_lookup_rootuser_interim_orders(case_details_soup):
    try:
        # find all buttons with class 'btn btn-primary'
        interim_order_buttons = [button.a for button in case_details_soup.find_all('button', class_='btn btn-primary') if button.get_text().strip() != 'VIEW JUDGMENT']
        if len(interim_order_buttons) > 0:
            # extract the values of the onclick attribute
            token_lookup_rootuser_list = [button.get('onclick').replace("'", "").replace(");", "")[button.get('onclick').find("(")+1:button.get('onclick').find(")")].split(',') for button in interim_order_buttons]
            return token_lookup_rootuser_list
        return None
    except Exception as e:
        print("Error fetching content(extract_token_lookup_rootuser_interim_orders):", e)
        return None
    
# function to generate the URL of interim order file
def generate_interim_order_urls_list(list_of_interim_order_parameters):
    try:
        # generate the URL of interim order file
        file_urls = [f'https://hckinfo.kerala.gov.in/digicourt/Casedetailssearch/fileview?token={token}+&lookups={lookup}' for token, lookup, rootuser in tuple(list_of_interim_order_parameters)]
        return file_urls
    except requests.RequestException as e:
        print("Error fetching content(generate_interim_order_urls_list):", e)
        return None

# function to extract token, lookup and citation number of judgement
def extract_token_lookup_citationnum_judgement(case_details_soup):
    try:
        # find all buttons with class 'btn btn-primary'
        judgement_button = [button.a for button in case_details_soup.find_all('button', class_='btn btn-primary') if button.get_text().strip() == 'VIEW JUDGMENT']

        if len(judgement_button) == 1:
            # extract the values of the onclick attribute
            onclick = judgement_button[0].get('onclick')
            token_lookup_citationnum = onclick.replace("'", "").replace(");", "")[onclick.find("(")+1:onclick.find(")")].split(',')
            return token_lookup_citationnum
        else:
            return None
    except Exception as e:
        print("Error fetching content(extract_token_lookup_citationnum_judgement):", e)
        return None

# function to generate the URL of judgement file
def generate_judgement_url(judgement_parameters):
    try:
        # generate the URL of judgement file
        token, lookup, citationnum = tuple(judgement_parameters)
        file_url = f'https://hckinfo.kerala.gov.in/digicourt/Casedetailssearch/fileviewcitation?token={token}+&lookups={lookup}+&citationno={citationnum}'
        return file_url
    except requests.RequestException as e:
        print("Error fetching content(generate_judgement_url):", e)
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
        print("Error fetching content(get_pdf_file_url):", e)
        return None
    
# function to get the content of pdf file
def get_pdf_file_content(pdf_url):
    try:
        # send a GET request to the URL
        response = requests.get(pdf_url)
        response.raise_for_status()  # Check for any HTTP errors
        return response.content
    except Exception as e:
        print("Error fetching content(get_pdf_file_content):", e)
        return None

# save pdf file
def write_pdf_file(folderpath, url):
    try:
        if len(url) > 0:
            pdf_url = get_pdf_file_url(url)
            pdf_content = get_pdf_file_content(pdf_url)
            filename = pdf_url.split('/')[-1]
            file_path = os.path.join(folderpath, filename)
                # write the content of the response to a PDF file
            with open(file_path, 'wb') as f:
                f.write(pdf_content)
                print(file_path, "is written.")
    except Exception as e:
        print("Error fetching content(write_pdf_file):", e)
        return None
    
# function to download and save files
def save_pdf_files(case_num, interim_order_url_list, judgement_url):
    try:
        root_directory = 'documents'
        case_folder_name = str(case_num)
        interim_orders_folder_name = 'interim orders'

        interim_orders_folderpath = root_directory + '/' + case_folder_name + '/' + interim_orders_folder_name
        judgement_folderpath = root_directory + '/' + case_folder_name

        # create folders if does not exist
        if not os.path.exists(interim_orders_folderpath):
            os.makedirs(interim_orders_folderpath)

        for url in interim_order_url_list:
            write_pdf_file(interim_orders_folderpath, url)

        write_pdf_file(judgement_folderpath, judgement_url)
    except Exception as e:
        print("Error fetching content(save_pdf_files):", e)
        return None

if __name__ == '__main__':

    if check_website_exists(url):
        soup = create_soup_object(url)
        select_tag = soup.find('select', id='case_type')
        options = select_tag.find_all('option')
        case_types = []
        for option in options[1:]:
            case_types.append((option['value'], option.get_text().strip()))
        
        search_result_soup = get_case_results_casetype_year(1, 2024)
        list_of_cinum_casenum = extract_cinum_casenum(search_result_soup)
        print('list_of_cinum_casenum:', list_of_cinum_casenum)
        print()

        for parameters in list_of_cinum_casenum:
            print("parameters:", parameters)
            case_details_soup = get_case_details_cinum_casenum(parameters[0], parameters[1])
            write_string_to_txt_file(case_details_soup.prettify())
        
            list_of_interim_order_parameters = extract_token_lookup_rootuser_interim_orders(case_details_soup)
            print('list_of_interim_order_parameters:', list_of_interim_order_parameters)
            judgement_parameters = extract_token_lookup_citationnum_judgement(case_details_soup)
            print('judgement_parameters:', judgement_parameters)
            list_of_interim_order_urls = generate_interim_order_urls_list(list_of_interim_order_parameters) if list_of_interim_order_parameters is not None else []
            print('list_of_interim_order_urls:', list_of_interim_order_urls)
            judgement_url = generate_judgement_url(judgement_parameters) if judgement_parameters is not None else ''
            print('judgement_url:', judgement_url)

            save_pdf_files(parameters[1], list_of_interim_order_urls, judgement_url)

            print()