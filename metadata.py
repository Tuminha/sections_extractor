"""Module for managing OS-level operations and subprocesses."""
import os
import subprocess
import time
import xml.etree.ElementTree as ET
import requests

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

# Check if the GROBID service is already running
try:
    response = requests.get('http://localhost:8070/api/isalive', timeout=10)
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

# Wait for the GROBID service to start
time.sleep(10)

#PDF_PATH = config.pdf_path
import os

PDF_DIR = "/Users/franciscoteixeirabarbosa/Dropbox/Science in Dentistry APP/pdf_extractor/sections_extractor/pdfs"
pdf_files = [os.path.join(PDF_DIR, f) for f in os.listdir(PDF_DIR) if f.endswith('.pdf')]
# Send each PDF to GROBID
for pdf_path in pdf_files:
    with open(pdf_path, 'rb') as f:
        response = requests.post('http://localhost:8070/api/processFulltextDocument', files={'input': f}, timeout=10)
# Save the XML output
with open('output.xml', 'w', encoding='utf-8') as f:
    f.write(response.text)

# Parse the XML output
tree = ET.parse('output.xml')
root = tree.getroot()

# Define the namespace
ns = {'tei': 'http://www.tei-c.org/ns/1.0'}

def extract_metadata(xml_root: ET.Element, namespace: dict) -> dict:
    """
    Extracts metadata from the XML root, specifically the main article author, publication year, journal, and title.
    """
    metadata = {
        'title': None,
        'authors': [],
        'publication_year': None,
        'journal': None
    }

    # Extracting the title
    title_element = xml_root.find('.//tei:title[@type="main"]', namespace)
    if title_element is not None:
        metadata['title'] = title_element.text

    # Extracting main article authors
    # Assuming the main article authors are under the first <analytic> tag
    main_article = xml_root.find('.//tei:analytic', namespace)
    if main_article is not None:
        for author in main_article.findall('.//tei:author/tei:persName', namespace):
            forename_element = author.find('.//tei:forename', namespace)
            surname_element = author.find('.//tei:surname', namespace)
            if forename_element is not None and surname_element is not None:
                forename = forename_element.text
                surname = surname_element.text
                metadata['authors'].append(f"{forename} {surname}")

    # Extracting publication year
    date_element = xml_root.find('.//tei:imprint/tei:date[@type="published"]', namespace)
    if date_element is not None:
        metadata['publication_year'] = date_element.get('when')

    # Extracting journal title
    journal_title_element = xml_root.find('.//tei:monogr/tei:title[@level="j"]', namespace)
    if journal_title_element is not None:
        metadata['journal'] = journal_title_element.text

    return metadata

# Extract the metadata
metadata = extract_metadata(root, ns)

# Ensure the output directory exists
output_dir = 'metadata_output'
os.makedirs(output_dir, exist_ok=True)

# Define the output file path
output_file_path = os.path.join(output_dir, 'metadata.txt')

# Write the metadata to the output file
with open(output_file_path, 'w', encoding='utf-8') as f:
    for key, value in metadata.items():
        if isinstance(value, list):
            f.write(f"{key.capitalize()}: {', '.join(value)}\n")
        else:
            f.write(f"{key.capitalize()}: {value}\n")

print(f"Metadata has been written to {output_file_path}")

# Print the metadata in the terminal as well
for key, value in metadata.items():
    if isinstance(value, list):
        print(f"{key.capitalize()}: {', '.join(value)}")
    else:
        print(f"{key.capitalize()}: {value}")