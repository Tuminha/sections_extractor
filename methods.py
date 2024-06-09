import subprocess
import time
import xml.etree.ElementTree as ET
import requests
import re
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
            subprocess.Popen(['./gradlew', 'run', '--stacktrace'], cwd=GROBID_PATH)
            time.sleep(10)
    except requests.exceptions.RequestException:
        print("GROBID service is not running. Starting it now...")
        subprocess.Popen(['./gradlew', 'run', '--stacktrace'], cwd=GROBID_PATH)
        time.sleep(10)

def format_formulas(text):
    # Define patterns for common chemical notations and other scientific formulas
    patterns = {
        r'(\d+)\s*H\s*2\s*O': r'\1H₂O',  # H2O with subscript
        r'(\d+)\s*O\s*2': r'\1O₂',        # O2 with subscript
        r'(\d+)\s*CO\s*2': r'\1CO₂',      # CO2 with subscript
        r'(\d+)\s*NO\s*3': r'\1NO₃',      # NO3 with subscript
        r'(\d+)\s*SO\s*4': r'\1SO₄',      # SO4 with subscript
        r'(\d+)\s*PO\s*4': r'\1PO₄',      # PO4 with subscript
        r'(\d+)\s*NH\s*4': r'\1NH₄',      # NH4 with subscript
        r'(\d+)\s*Ca\s*10': r'\1Ca₁₀',    # Ca10 with subscript
        r'(\d+)\s*OH\s*2': r'\1OH₂',      # OH2 with subscript
        r'(\d+)\s*C\s*6\s*H\s*12\s*O\s*6': r'\1C₆H₁₂O₆',  # Glucose formula
        r'(\d+)\s*NaCl': r'\1NaCl',       # Sodium chloride
        r'(\d+)\s*C\s*2\s*H\s*5\s*OH': r'\1C₂H₅OH',  # Ethanol
        r'(\d+)\s*CH\s*4': r'\1CH₄',      # Methane
        r'(\d+)\s*H\s*2\s*SO\s*4': r'\1H₂SO₄',  # Sulfuric acid
        r'(\d+)\s*Na\s*HCO\s*3': r'\1NaHCO₃',  # Sodium bicarbonate
        r'(\d+)\s*Fe\s*2\s*O\s*3': r'\1Fe₂O₃',  # Iron(III) oxide
        r'(\d+)\s*Cu\s*SO\s*4': r'\1CuSO₄',  # Copper(II) sulfate
        r'(\d+)\s*HCl': r'\1HCl',          # Hydrochloric acid
        r'(\d+)\s*NaOH': r'\1NaOH',        # Sodium hydroxide
        r'(\d+)\s*KMnO\s*4': r'\1KMnO₄',   # Potassium permanganate
    }
    # Apply each pattern to the text
    for pattern, replacement in patterns.items():
        text = re.sub(pattern, replacement, text)

    return text

def format_text(text: str) -> str:
    """
    Formats the text to include line breaks and paragraphs for better readability.

    Parameters:
    text (str): The text to format.

    Returns:
    str: The formatted text.
    """
    # Split text into paragraphs
    paragraphs = text.split('\n\n')
    formatted_paragraphs = [re.sub(r'(\.\s+)', r'\1\n', p) for p in paragraphs]
    return '\n\n'.join(formatted_paragraphs)

def extract_material_and_methods(xml_root: ET.Element, namespace: dict) -> str:
    """
    Extracts the 'Materials and Methods' section and its subheadings from the XML root.
    """
    material_and_methods = ""
    capture_text = False

    # Iterate over all 'div' elements in the XML
    for div in xml_root.findall('.//tei:div', namespace):
        head = div.find('.//tei:head', namespace)
        if head is not None:
            title = head.text.strip().lower() if head.text else ""
            # Check if the title indicates the start of 'Materials and Methods'
            if any(method_title.lower() in title for method_title in section_mappings['Methods']):
                capture_text = True
            # Check if the title indicates the end of 'Materials and Methods'
            elif any(result_title.lower() in title for result_title in section_mappings['Results']):
                break

        if capture_text:
            for elem in div.iter():
                if elem.text:
                    formatted_text = format_formulas(elem.text)
                    material_and_methods += formatted_text + " "

    return format_text(material_and_methods.strip())

def process_pdf_for_methods(pdf_path: str, output_dir: str, grobid_url: str):
    """
    Processes a PDF file to extract and format the 'Materials and Methods' section, saving the result to the specified output directory.

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
    namespace = {'tei': 'http://www.tei-c.org/ns/1.0'}

    # Extract the Materials and Methods section
    methods_text = extract_material_and_methods(root, namespace)

    # Define the output file path
    output_file_path = os.path.join(output_dir, 'methods.txt')

    # Write the methods to the output file
    with open(output_file_path, 'w', encoding='utf-8') as f:
        f.write(methods_text)

    print(f"Materials and Methods section has been written to {output_file_path}")

    # Print the methods in the terminal as well
    print(methods_text)

# Example usage
def main():
    # Start the GROBID service
    start_grobid_service()

    # Configuration
    PDF_DIR = "/Users/franciscoteixeirabarbosa/Dropbox/Science in Dentistry APP/pdf_extractor/sections_extractor/pdfs"
    METHODS_OUTPUT_DIR = '/Users/franciscoteixeirabarbosa/Dropbox/Science in Dentistry APP/pdf_extractor/sections_extractor/methods_output'

    # Ensure the methods output directory exists
    os.makedirs(METHODS_OUTPUT_DIR, exist_ok=True)

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
        
        # Process the PDF to extract the 'Materials and Methods' section
        process_pdf_for_methods(pdf_path, METHODS_OUTPUT_DIR, GROBID_URL)

if __name__ == "__main__":
    main()

   