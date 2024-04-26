import requests
import webbrowser
from bs4 import BeautifulSoup
import os
import csv
import re
import PyPDF2

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
    
# function to extract CI number, CNR number, case number and case title from a row in a table
def extract_cinum_cnrnum_casenum_casetitle_row(row):
    # find all <td> elements within the row
    td_elements = row.find_all('td')
    
    case_num = td_elements[1].get_text()
    case_title = td_elements[2].get_text(strip=True)
    result_button = td_elements[3].button
    # print(result_button)
    parameters = result_button.get('onclick').replace("'", "").replace(");", "")[result_button.get('onclick').find("(")+1:result_button.get('onclick').find(")")].split(',')
    ci_num, cnr_num = parameters[0], parameters[1]
    
    return {"CI Number": ci_num, "CNR Number": cnr_num, "Case Number": case_num, "Case Title": case_title}
    
# function to extract CI numbers, CNR numbers, case numbers and case titles from a search result
def extract_cinum_cnrnum_casenum_casetitle_list(result_soup):
    try:
        # find the table with class="table table-striped table-bordered table-hover"
        table = result_soup.find('table', class_='table table-striped table-bordered table-hover')
        # find all rows (tr) within the table's tbody
        rows = table.find('tbody').find_all('tr')
        # print("No. of rows:", len(rows))
        # extract the values of the onclick attribute
        cinum_casenum_list = [extract_cinum_cnrnum_casenum_casetitle_row(row) for row in rows[:-1]]

        return cinum_casenum_list
    except Exception as e:
        print("Error fetching content(extract_cinum_cnrnum_casenum_casetitle_list):", e)
        return None
    
# function to get case details from parameters
def get_case_details_from_parameters(parameters):
    try:
        # make a POST request to the API with the provided data
        api_url = 'https://hckinfo.kerala.gov.in/digicourt/Casedetailssearch/Viewcasestatus'
        response = requests.post(api_url, data={'cino': parameters["CI Number"], 'case_no': parameters["CNR Number"]})
        response.raise_for_status()  # Check for any HTTP errors
        
        # extract the HTML content from the response
        html_content = response.content
        # create a BeautifulSoup object
        soup = BeautifulSoup(html_content, 'html.parser')
        return soup
    except requests.RequestException as e:
        print("Error fetching content(get_case_details_from_parameters):", e)
        return None
    
# function to extract token, lookup and root user of interim orders
def extract_token_lookup_rootuser_interim_orders(case_details_soup):
    try:
        # find all buttons with class 'btn btn-primary'
        interim_order_buttons = [button.a for button in case_details_soup.find_all('button', class_='btn btn-primary') if button.get_text(strip=True) != 'VIEW JUDGMENT']
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
        judgement_button = [button.a for button in case_details_soup.find_all('button', class_='btn btn-primary') if button.get_text(strip=True) == 'VIEW JUDGMENT']

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

# write pdf file
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

            # print("Type of path:", type(file_path))
            return file_path
    except Exception as e:
        print("Error fetching content(write_pdf_file):", e)
        return None
    
# function to download and save files
def save_pdf_files(case_num, interim_order_url_list, judgement_url):
    try:
        root_directory = 'new_documents'
        case_folder_name = str(case_num)
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
        print("Error fetching content(save_pdf_files):", e)
        return None
    
# function to extract judgement text from the PDF file
def extract_judgement_text_from_judgement_file(judgement_filename):
    try:
        if judgement_filename:
            # Open the PDF file in binary mode
            with open(judgement_filename, 'rb') as file:
                # Create a PDF file reader object
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Initialize an empty string to store the extracted text
                text = ''
                # Loop through each page in the PDF
                for page_num in range(len(pdf_reader.pages)):
                    # Get the page object
                    page = pdf_reader.pages[page_num]
                    
                    # Extract text from the page
                    text += page.extract_text()

                if "JUDGMENT" in text:
                    # Use regular expression to extract the desired text
                    match = re.search(r'JUDGMENT.*?JUDGMENT(.*?)Sd/-', text, re.DOTALL)

                    if match:
                        extracted_text = match.group(1).strip()
                        # Remove extra spaces and line breaks
                        extracted_text = re.sub(r'\s+', ' ', extracted_text)
                        # print(extracted_text)
                    else:
                        extracted_text = "Text not found"  

                    write_string_to_txt_file(extracted_text)
                    return extracted_text
        
        return ''

    except Exception as e:
        print("Error fetching content(extract_judgement_text_from_judgement_file):", e)
        return None
    
# function to extract relevant details from case details table
def extract_details_from_case_details_table(table):
    try:
        td_elements = [td.get_text(strip=True) for td in table.find_all('td')]
        # print(td_elements)
        # print(td_elements.index('Case Type'))
        details = {
            "Case Type": td_elements[td_elements.index('Case Type')+1],
            "Case Status": td_elements[td_elements.index('Case Status')+1],
            "Filing Date": td_elements[td_elements.index('Filing Date')+1],
            "Registration Date": td_elements[td_elements.index('Registration Date')+1]
        }
        # print(details)

        return details
    except Exception as e:
        print("Error fetching content(extract_details_from_case_details_table):", e)
        return None
    
# function to extract relevant details from acts table
def extract_details_from_acts_table(table):
    try:
        td_elements = table.find_all('td')
        # print(td_elements)
        details = {td_elements[1].get_text(strip=True): td_elements[3].get_text(strip=True), td_elements[2].get_text(strip=True): td_elements[4].get_text(strip=True)}
        # print(details)

        return details
    except Exception as e:
        print("Error fetching content(extract_details_from_acts_table):", e)
        return None
    
# function to extract relevant details from petitioner table
def extract_details_from_petitioner_table(table):
    try:
        td_elements = table.find_all('td')
        # print(td_elements)
        # Define a regular expression pattern to match text starting with an integer followed by ")"
        pattern = re.compile(r'^\d+\)')
        # Filter td elements based on their text content using the regular expression
        details = [td.get_text(strip=True)[td.get_text(strip=True).index(')')+1:].strip() for td in td_elements if pattern.match(td.get_text(strip=True))]
        # print(details)

        return {"Petitioner": ', '.join(details)}
    except Exception as e:
        print("Error fetching content(extract_details_from_petitioner_table):", e)
        return None
    
# function to extract relevant details from respondent table
def extract_details_from_respondent_table(table):
    try:
        td_elements = table.find_all('td')
        # print(td_elements)
        # Define a regular expression pattern to match text starting with an integer followed by ")"
        pattern = re.compile(r'^\d+\)')
        # Filter td elements based on their text content using the regular expression
        # print([td.get_text(strip=True) for td in td_elements])
        details = [td.get_text(strip=True)[td.get_text(strip=True).index(')')+1:].strip() for td in td_elements if pattern.match(td.get_text(strip=True))]
        # print(details)

        return {"Respondent": ', '.join(details)}
    except Exception as e:
        print("Error fetching content(extract_details_from_respondent_table):", e)
        return None
    
# function to extract relevant details from case status table
def extract_details_from_case_status_table(table):
    try:
        td_elements = [td.get_text(strip=True) for td in table.find_all('td')]
        # print(td_elements)
        details = {
            "Judge": td_elements[td_elements.index('Coram')+1], 
            "Bench": td_elements[td_elements.index('Bench')+1]}
        # print(details)

        return details
    except Exception as e:
        print("Error fetching content(extract_details_from_case_status_table):", e)
        return None
    
# function to extract relevant details from case hearings table
def extract_details_from_case_hearings_table(table):
    try:
        rows = table.find_all('tr')[1:]
        # print(rows)
        table_headers = [td.get_text(strip=True) for td in rows[0].find_all('td')]
        # print(table_headers)
        details = [
            {table_headers[num]: row.find_all('td')[num].get_text(strip=True) for num in range(len(row.find_all('td')))}
            for row in rows[1:]
        ]
        # print(details)

        return {'History of Case Hearings': details}
    except Exception as e:
        print("Error fetching content(extract_details_from_case_hearings_table):", e)
        return None
    
# function to extract relevant details from judgement table
def extract_details_from_judgement_table(table):
    try:
        td_elements = table.find_all('td')
        # print(td_elements)
        details = {'Judgement Date': td_elements[-2].get_text(strip=True)}
        # print(details)

        return details
    except Exception as e:
        print("Error fetching content(extract_details_from_acts_table):", e)
        return None

# function combine all the dictionaries
def combine_all_dicts(dicts):
    try:
        combined_dict = {}
        for dict in dicts:
            combined_dict.update(dict)
        
        return combined_dict
    except Exception as e:
        print("Error fetching content(combine_all_dicts):", e)
        return None

# function to extract relevant details from case details
def extract_case_details(parameters, case_details_soup, list_of_interim_order_urls, judgement_url):
    try:
        # Find all tables with the specified class
        tables = case_details_soup.find_all('table', class_='table table-striped table-bordered table-hover table-shadow')

        case_details_table = [table for table in tables if table.find('td', class_='table-header').get_text(strip=True) == 'CASE DETAILS'][0]
        case_details = extract_details_from_case_details_table(case_details_table)

        acts_table = [table for table in tables if table.find('td', class_='table-header').get_text(strip=True) == 'ACTS'][0]
        acts = extract_details_from_acts_table(acts_table)

        petitioner_table = [table for table in tables if table.find('td', class_='table-header').get_text(strip=True) == 'PETITIONER AND ADVOCATE'][0]
        petitioner = extract_details_from_petitioner_table(petitioner_table)

        respondent_table = [table for table in tables if table.find('td', class_='table-header').get_text(strip=True) == 'RESPONDENT AND ADVOCATES'][0]
        respondent = extract_details_from_respondent_table(respondent_table)

        case_status_table = [table for table in tables if table.find('td', class_='table-header').get_text(strip=True) == 'CASE STATUS'][0]
        case_status = extract_details_from_case_status_table(case_status_table)

        case_hearings_table = [table for table in tables if table.find('td', class_='table-header').get_text(strip=True) == 'HISTORY OF CASE HEARING'][0]
        case_hearings = extract_details_from_case_hearings_table(case_hearings_table)

        judgement_table = [table for table in tables if table.find('td', class_='table-header').get_text(strip=True) == 'JUDGMENT']
        judgement_date = extract_details_from_judgement_table(judgement_table[0]) if len(judgement_table) > 0 else {'Judgement Date': ''}

        document_urls = {'List of Interim Order URLs': list_of_interim_order_urls, 'Judgement URL': judgement_url}

        combined_details = combine_all_dicts([parameters, case_details, acts, petitioner, respondent, case_status, case_hearings, judgement_date, document_urls])
        # print(combined_details)

        print("Case details extracted successfully...")
        return combined_details
    except Exception as e:
        print("Error fetching content(extract_case_details):", e)
        return None
    
# function to create a csv dataset out of case details
def create_csv_dataset(list_of_case_details):
    try:
        # Extracting header from the first dictionary
        headers = list_of_case_details[0].keys()

        # Writing data to CSV file
        with open('output.csv', 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            
            # Writing headers to CSV file
            writer.writeheader()
            
            # Writing data rows to CSV file
            for row in list_of_case_details:
                writer.writerow(row)
        
        print("CSV file generated successfully...")
    except Exception as e:
        print("Error fetching content(create_csv_dataset):", e)
        return None

if __name__ == '__main__':

    if check_website_exists(url):
        soup = create_soup_object(url)
        select_tag = soup.find('select', id='case_type')
        options = select_tag.find_all('option')
        case_types = []
        for option in options[1:]:
            case_types.append((option['value'], option.get_text(strip=True)))

        list_of_case_details = []

        for case_type in range(1, 2):

            print(f"Process for case type {case_type} started...")

            for year in range(2011, 2012):

                print(f"Process for year {year} started...")
            
                search_result_soup = get_case_results_casetype_year(case_type, year)
                list_of_cinum_casenum = extract_cinum_cnrnum_casenum_casetitle_list(search_result_soup)
                # print('list_of_cinum_casenum:', list_of_cinum_casenum)
                print()
                for parameters in list_of_cinum_casenum:
                    # print("parameters:", parameters)
                    case_details_soup = get_case_details_from_parameters(parameters)
                    # write_string_to_txt_file(case_details_soup.prettify())
                
                    list_of_interim_order_parameters = extract_token_lookup_rootuser_interim_orders(case_details_soup)
                    judgement_parameters = extract_token_lookup_citationnum_judgement(case_details_soup)
                    list_of_interim_order_urls = generate_interim_order_urls_list(list_of_interim_order_parameters) if list_of_interim_order_parameters is not None else []
                    judgement_url = generate_judgement_url(judgement_parameters) if judgement_parameters is not None else ''

                    interim_order_filename_list, judgement_filename = save_pdf_files(parameters['CNR Number'], list_of_interim_order_urls, judgement_url)
                    # judgement_text = extract_judgement_text_from_judgement_file(judgement_filename)

                    list_of_case_details.append(extract_case_details(parameters, case_details_soup, list_of_interim_order_urls, judgement_url))

                    print()

                print(f"Process for year {year} completed...")
                print()

            print(f"Process for case type {case_type} completed...")
            print()

        # create_csv_dataset(list_of_case_details)

        