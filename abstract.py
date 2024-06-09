import re
import xml.etree.ElementTree as ET
import os
import requests
import subprocess
import time

# Path to the GROBID service
GROBID_PATH = '/Users/franciscoteixeirabarbosa/projects/test/sections_pdf/grobid'
GROBID_URL = 'http://localhost:8070'

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

def extract_abstract(xml_root: ET.Element, namespace: dict) -> str:
    """
    Extracts the abstract from the XML root using the provided namespace.

    Parameters:
    xml_root (ET.Element): The root of the XML document.
    namespace (dict): The namespace for the XML document.

    Returns:
    str: The abstract text, or an empty string if no abstract is found.
    """
    abstract_element = xml_root.find('.//tei:profileDesc/tei:abstract', namespace)
    if abstract_element is not None:
        return ''.join(abstract_element.itertext())
    return "Abstract not found."

def format_abstract(text: str) -> str:
    """
    Formats the abstract text to include line breaks for better readability.

    Parameters:
    text (str): The abstract text.

    Returns:
    str: The formatted abstract text.
    """
    formatted_text = re.sub(r'(\.\s+)', r'\1\n', text)
    return formatted_text

def process_pdf_for_abstract(pdf_path: str, output_dir: str, grobid_url: str):
    """
    Processes a PDF file to extract and format the abstract, saving the result to the specified output directory.

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

    # Extract the abstract text
    abstract_text = extract_abstract(root, ns)

    # Format the abstract text
    formatted_abstract_text = format_abstract(abstract_text)

    # Define the output file path
    output_file_path = os.path.join(output_dir, 'abstract.txt')

    # Write the formatted abstract to the output file
    with open(output_file_path, 'w', encoding='utf-8') as f:
        f.write(formatted_abstract_text)

    print(f"Abstract has been written to {output_file_path}")

    # Print the formatted abstract in the terminal as well
    print(formatted_abstract_text)

# Start the GROBID service
start_grobid_service()

# Configuration
PDF_DIR = "/Users/franciscoteixeirabarbosa/Dropbox/Science in Dentistry APP/pdf_extractor/sections_extractor/pdfs"
ABSTRACT_OUTPUT_DIR = '/Users/franciscoteixeirabarbosa/Dropbox/Science in Dentistry APP/pdf_extractor/sections_extractor/abstract_output'

# Ensure the abstract output directory exists
os.makedirs(ABSTRACT_OUTPUT_DIR, exist_ok=True)

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
    
    # Process the PDF to extract and format the abstract
    process_pdf_for_abstract(pdf_path, ABSTRACT_OUTPUT_DIR, GROBID_URL)