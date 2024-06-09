import re
import xml.etree.ElementTree as ET
import os
import requests
import subprocess
import time

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

def extract_statistical_analysis(xml_root: ET.Element, namespace: dict) -> str:
    """
    Extracts the Statistical Analysis section from the XML root using the provided namespace.

    Parameters:
    xml_root (ET.Element): The root of the XML document.
    namespace (dict): The namespace for the XML document.

    Returns:
    str: The Statistical Analysis text, or an empty string if no section is found.
    """
    for div in xml_root.findall('.//tei:div', namespace):
        head = div.find('.//tei:head', namespace)
        if head is not None and 'Statistical analysis' in head.text:
            return ''.join(div.itertext())
    return "Statistical analysis section not found."

def format_statistical_analysis(text: str) -> str:
    """
    Formats the Statistical Analysis text to include line breaks for better readability.

    Parameters:
    text (str): The Statistical Analysis text.

    Returns:
    str: The formatted Statistical Analysis text.
    """
    formatted_text = re.sub(r'(\.\s+)', r'\1\n', text)
    return formatted_text

def process_pdf_for_statistical_analysis(pdf_path: str, output_dir: str, grobid_url: str):
    """
    Processes a PDF file to extract and format the Statistical Analysis section, saving the result to the specified output directory.

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

    # Extract the Statistical Analysis text
    analysis_text = extract_statistical_analysis(root, ns)

    # Format the Statistical Analysis text
    formatted_analysis_text = format_statistical_analysis(analysis_text)

    # Define the output file path
    output_file_path = os.path.join(output_dir, 'statistical_analysis.txt')

    # Write the formatted Statistical Analysis to the output file
    with open(output_file_path, 'w', encoding='utf-8') as f:
        f.write(formatted_analysis_text)

    print(f"Statistical Analysis section has been written to {output_file_path}")

    # Print the formatted Statistical Analysis in the terminal as well
    print(formatted_analysis_text)

# Start the GROBID service
start_grobid_service()

# Configuration
PDF_DIR = "/Users/franciscoteixeirabarbosa/Dropbox/Science in Dentistry APP/pdf_extractor/sections_extractor/pdfs"
ANALYSIS_OUTPUT_DIR = '/Users/franciscoteixeirabarbosa/Dropbox/Science in Dentistry APP/pdf_extractor/sections_extractor/statistical_analysis'

# Ensure the analysis output directory exists
os.makedirs(ANALYSIS_OUTPUT_DIR, exist_ok=True)

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
    
    # Process the PDF to extract and format the Statistical Analysis
    process_pdf_for_statistical_analysis(pdf_path, ANALYSIS_OUTPUT_DIR, GROBID_URL)