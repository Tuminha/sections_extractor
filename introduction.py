import os
import subprocess
import time
import xml.etree.ElementTree as ET
import requests
import re

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

def extract_introduction(xml_root: ET.Element, namespace: dict) -> str:
    """
    This function extracts the introduction from the XML root.
    """
    introduction = ""
    capture_text = False

    # Find the abstract element
    abstract = xml_root.find('.//tei:abstract', namespace)
    if abstract is not None:
        # Start capturing text after the abstract
        capture_text = True

    # Iterate through all elements in the XML
    for elem in xml_root.iter():
        # Check if we should stop capturing text
        if elem.tag == f"{{{namespace['tei']}}}head" and elem.text and 'materials and methods' in elem.text.lower():
            capture_text = False
            break

        # Capture text if we are in the introduction section
        if capture_text and elem.tag == f"{{{namespace['tei']}}}p":
            paragraph_text = ' '.join(elem.itertext()).strip()
            introduction += paragraph_text + "\n\n"

    return format_text(introduction.strip())

def format_text(text: str) -> str:
    """
    Formats the text to include line breaks for better readability.

    Parameters:
    text (str): The text to format.

    Returns:
    str: The formatted text.
    """
    formatted_text = re.sub(r'(\.\s+)', r'\1\n', text)
    return formatted_text

def process_pdf_for_introduction(pdf_path: str, output_dir: str, grobid_url: str):
    """
    Processes a PDF file to extract the introduction, saving the result to the specified output directory.

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

    # Extract the introduction text
    introduction_text = extract_introduction(root, ns)

    # Define the output file path
    output_file_path = os.path.join(output_dir, 'introduction.txt')

    # Write the introduction to the output file
    with open(output_file_path, 'w', encoding='utf-8') as f:
        f.write(introduction_text)

    print(f"Introduction has been written to {output_file_path}")

    # Print the introduction in the terminal as well
    print(introduction_text)

# Start the GROBID service
start_grobid_service()

# Configuration
PDF_DIR = "/Users/franciscoteixeirabarbosa/Dropbox/Science in Dentistry APP/pdf_extractor/sections_extractor/pdfs"
INTRODUCTION_OUTPUT_DIR = '/Users/franciscoteixeirabarbosa/Dropbox/Science in Dentistry APP/pdf_extractor/sections_extractor/introduction_output'

# Ensure the introduction output directory exists
os.makedirs(INTRODUCTION_OUTPUT_DIR, exist_ok=True)

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
    
    # Process the PDF to extract the introduction
    process_pdf_for_introduction(pdf_path, INTRODUCTION_OUTPUT_DIR, GROBID_URL)