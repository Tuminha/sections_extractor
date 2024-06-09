"""
This file is where the discussion section is extracted from the XML root.
First, we check if GROBID is running. If it is not, we start it. Then, we send the PDF to GROBID and save the XML output.
Next, we parse the XML output and define the namespace. Then, we find all 'div' elements in the XML and check if the title contains any of the specified sections.
If it does, we print the title of the section and recursively find all 'p' elements in the 'div'. Then, we print the paragraph text and the text of any 'ref' elements within the paragraph.
Finally, we add a newline after the paragraph.
"""

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

# First check if the GROBID service is already running, and if it already running do not start it again
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

def extract_discussion(xml_root: ET.Element, namespace: dict) -> str:
    """
    This function extracts the discussion section from the XML root, including all nested text and section numbers.

    Parameters:
    xml_root (ET.Element): The root of the XML document.
    namespace (dict): The namespace for the XML document.

    Returns:
    str: The discussion section as a string.
    """
    in_discussion = False
    discussion = ""

    for div in xml_root.findall('.//tei:div', namespace):
        head = div.find('.//tei:head', namespace)
        if head is not None:
            section_title = head.text.strip()
            section_number = head.get('n', '').strip()

            # Check if the title indicates the start of the 'Discussion' section
            if 'discussion' in section_title.lower():
                in_discussion = True
                discussion += f"\n{section_number} {section_title}\n" if section_number else f"\n{section_title}\n"

            # Check if the title indicates the end of the 'Discussion' section
            if 'conclusion' in section_title.lower() and in_discussion:
                break

        if in_discussion:
            # Extract all text within the 'div', including nested paragraphs and figures
            for elem in div.iter():
                if elem.tag.endswith('head'):
                    section_title = elem.text.strip()
                    section_number = elem.get('n', '').strip()
                    discussion += f"\n{section_number} {section_title}\n" if section_number else f"\n{section_title}\n"
                elif elem.tag.endswith('p') or elem.tag.endswith('figDesc'):
                    if elem.text:
                        discussion += elem.text + "\n"
                if elem.tail:
                    discussion += elem.tail.strip() + "\n"

    return discussion

if __name__ == "__main__":
    PDF_DIR = "/Users/franciscoteixeirabarbosa/Dropbox/Science in Dentistry APP/pdf_extractor/sections_extractor/pdfs"
    XML_DIR = "/Users/franciscoteixeirabarbosa/Dropbox/Science in Dentistry APP/pdf_extractor/sections_extractor/xml_files"
    OUTPUT_DIR = "/Users/franciscoteixeirabarbosa/Dropbox/Science in Dentistry APP/pdf_extractor/sections_extractor/discussion_output"
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    pdf_files = [f for f in os.listdir(PDF_DIR) if f.endswith('.pdf')]
    for pdf_file in pdf_files:
        pdf_path = os.path.join(PDF_DIR, pdf_file)
        xml_filename = pdf_file.replace('.pdf', '.xml')
        xml_output_path = os.path.join(XML_DIR, xml_filename)

        # Send the PDF to GROBID
        try:
            with open(pdf_path, 'rb') as f:
                response = requests.post(f'{GROBID_URL}/api/processFulltextDocument', files={'input': f}, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error processing file {pdf_path}: {e}")
            continue

        # Save the XML output
        with open(xml_output_path, 'w', encoding='utf-8') as f:
            f.write(response.text)

        if not os.path.exists(xml_output_path):
            print(f"XML file not found for {pdf_file}")
            continue

        try:
            tree = ET.parse(xml_output_path)
            root = tree.getroot()
            ns = {'tei': 'http://www.tei-c.org/ns/1.0'}
            discussion = extract_discussion(root, ns)
            output_file_path = os.path.join(OUTPUT_DIR, f'{pdf_file.replace(".pdf", "")}_discussion.txt')
            with open(output_file_path, 'w', encoding='utf-8') as f:
                f.write(discussion)
            print(f"Discussion for {pdf_file} has been written to {output_file_path}")
        except ET.ParseError as e:
            print(f"Error parsing XML file {xml_output_path}: {e}")