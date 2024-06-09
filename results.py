import subprocess
import time
import xml.etree.ElementTree as ET
import requests
import os

section_mappings = {
    'Abstract': ['Abstract', 'Summary'],
    'Introduction': ['Introduction'],
    'Methods': [
        'Methods', 'Methodology', 'Materials and Methods', 'Experimental Setup',
        'Experimental Design', 'Experimental Procedures', 'Experimental Protocol',
        'Experimental Methods', 'Experimental Section', 'Experimental',
        'Study Design', 'Study Population', 'Study Sample', 'Study Participants',
        'Study Protocol', 'study selection'
    ],
    'Results': ['Results', 'Findings', 'Outcomes', 'Observations', 'Data', 'Analysis', 'Statistics'],
    'Discussion': ['Discussion', 'Interpretation', 'Implications', 'Limitations'],
    'Conclusion': ['Conclusion'],
    'Figures_Tables': ['Figures', 'Tables', 'Illustrations', 'Appendix', 'Supplementary Material'],
    'References': ['References', 'Bibliography', 'Citations', 'Sources', 'Literature Cited'],
    'Statistical Analysis': ['Statistical Analysis']  # Added this new section
}

# Path to the GROBID service
GROBID_PATH = '/Users/franciscoteixeirabarbosa/projects/test/sections_pdf/grobid'
GROBID_URL = 'http://localhost:8070'

def start_grobid_service():
    try:
        response = requests.get(f'{GROBID_URL}/api/isalive', timeout=10)
        if response.status_code == 200:
            print("GROBID service is already running.")
        else:
            # Start the GROBID service
            p = subprocess.Popen(['./gradlew', 'run', '--stacktrace'], cwd=GROBID_PATH)
            # Wait for the GROBID service to start
            time.sleep(10)
    except requests.exceptions.RequestException as e:
        # If the request fails, it means the service is not running
        print("GROBID service is not running. Starting it now...")
        p = subprocess.Popen(['./gradlew', 'run', '--stacktrace'], cwd=GROBID_PATH)
        # Wait for the GROBID service to start
        time.sleep(10)

def extract_results(xml_root: ET.Element, namespace: dict) -> str:
    """
    This function extracts the results section from the XML root, including all nested text and section numbers.
    It stops extraction upon reaching the 'Discussion' section to ensure it is not included in the results.

    Parameters:
    xml_root (ET.Element): The root of the XML document.
    namespace (dict): The namespace for the XML document.

    Returns:
    str: The results section as a string.
    """
    results = ""
    discussion_found = False

    for div in xml_root.findall('.//tei:div', namespace):
        head = div.find('.//tei:head', namespace)
        if head is not None and 'Discussion' in head.text:
            discussion_found = True
            break  # Stop processing once 'Discussion' is found

        if not discussion_found:
            for elem in div.iter():
                if elem.text:
                    results += elem.text.strip() + "\n"
                if elem.tail:
                    results += elem.tail.strip() + "\n"

    return results

def extract_tables(xml_root: ET.Element, namespace: dict) -> str:
    """
    Extracts tables from the XML root using the provided namespace.

    Parameters:
    xml_root (ET.Element): The root of the XML document.
    namespace (dict): The namespace for the XML document.

    Returns:
    str: The tables as a string.
    """
    tables = ""
    for table in xml_root.findall('.//tei:figure[@type="table"]', namespace):
        table_id = table.get('{http://www.w3.org/XML/1998/namespace}id', 'Unknown ID')
        table_head = table.find('.//tei:head', namespace)
        table_desc = table.find('.//tei:figDesc', namespace)
        table_content = table.find('.//tei:table', namespace)

        # Add table title and description
        tables += f"Table {table_id}: {table_head.text.strip() if table_head is not None else ''}\n"
        tables += "-" * 60 + "\n"
        if table_desc is not None:
            tables += f"{table_desc.text.strip()}\n"

        # Extract table rows and format them
        if table_content is not None:
            rows = []
            for row in table_content.findall('.//tei:row', namespace):
                row_data = [cell.text.strip() if cell.text is not None else '' for cell in row.findall('.//tei:cell', namespace)]
                rows.append(row_data)

            # Determine the maximum number of columns
            max_cols = max(len(row) for row in rows)

            # Format the header row
            header_row = rows[0] if rows else []
            tables += " | ".join(header_row) + "\n"
            tables += "-" * (len(" | ".join(header_row))) + "\n"

            # Format the data rows
            for row in rows[1:]:
                tables += " | ".join(row + [''] * (max_cols - len(row))) + "\n"

        tables += "\n"
    return tables

def process_pdf_for_results(pdf_path: str, output_dir: str, grobid_url: str):
    """
    Processes a PDF file to extract the results section, saving the result to the specified output directory.

    Parameters

    put directory.

    Parameters:
    pdf_path (str): The path to the PDF file.
    output_dir (str): The directory to save the output.
    grobid_url (str): The URL of the GROBID service.
    """
    # Send the PDF to GROBID
    with open(pdf_path, 'rb') as f:
        response = requests.post(f'{grobid_url}/api/processFulltextDocument', files={'input': f}, timeout=10)
        response.raise_for_status()

    # Save the XML output
    xml_output_path = os.path.join(output_dir, 'output.xml')
    with open(xml_output_path, 'w', encoding='utf-8') as f:
        f.write(response.text)

    # Parse the XML output
    tree = ET.parse(xml_output_path)
    root = tree.getroot()
    ns = {'tei': 'http://www.tei-c.org/ns/1.0'}

    # Extract the results section
    results_text = extract_results(root, ns)

    # Extract the tables
    tables_text = extract_tables(root, ns)

    # Define the output file paths
    results_output_file_path = os.path.join(output_dir, 'results.txt')
    tables_output_file_path = os.path.join(output_dir, 'tables.txt')

    # Write the results to the output file
    with open(results_output_file_path, 'w', encoding='utf-8') as f:
        f.write(results_text)

    # Write the tables to the output file
    with open(tables_output_file_path, 'w', encoding='utf-8') as f:
        f.write(tables_text)

    print(f"Results have been written to {results_output_file_path}")
    print(f"Tables have been written to {tables_output_file_path}")

    # Print the results and tables in the terminal as well
    print(results_text)
    print(tables_text)

# Start the GROBID service
start_grobid_service()

# Configuration
PDF_DIR = "/Users/franciscoteixeirabarbosa/Dropbox/Science in Dentistry APP/pdf_extractor/sections_extractor/pdfs"
RESULTS_OUTPUT_DIR = '/Users/franciscoteixeirabarbosa/Dropbox/Science in Dentistry APP/pdf_extractor/sections_extractor/results_output'

# Ensure the results output directory exists
os.makedirs(RESULTS_OUTPUT_DIR, exist_ok=True)

# Process each PDF file in the directory
pdf_files = [f for f in os.listdir(PDF_DIR) if f.endswith('.pdf')]
for pdf_file in pdf_files:
    pdf_path = os.path.join(PDF_DIR, pdf_file)
    
    # Debugging: Print the file path
    print(f"Processing file: {pdf_path}")
    
    # Check if the file exists
    if not os.path.exists(pdf_path):
        print(f"File not found: {pdf_path}")
        continue
    
    # Process the PDF to extract the results and tables
    process_pdf_for_results(pdf_path, RESULTS_OUTPUT_DIR, GROBID_URL)