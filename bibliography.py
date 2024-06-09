import os
import xml.etree.ElementTree as ET
import subprocess
import time
import requests

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

def extract_bibliography(root, ns):
    bibliography = []
    for bibl in root.findall('.//tei:listBibl/tei:biblStruct', ns):
        analytic = bibl.find('tei:analytic', ns)
        monogr = bibl.find('tei:monogr', ns)

        if analytic is not None:
            title = analytic.find('tei:title', ns)
            authors = analytic.findall('tei:author', ns)
            author_names = []
            for author in authors:
                persName = author.find('tei:persName', ns)
                if persName is not None:
                    forename = persName.find('tei:forename', ns)
                    surname = persName.find('tei:surname', ns)
                    if forename is not None and surname is not None:
                        author_names.append(f"{forename.text} {surname.text}")

        if monogr is not None:
            publication = monogr.find('tei:title', ns)
            date = monogr.find('tei:imprint/tei:date', ns)
            volume = monogr.find('tei:imprint/tei:biblScope[@unit="volume"]', ns)
            pages = monogr.find('tei:imprint/tei:biblScope[@unit="page"]', ns)

        if title is not None and publication is not None and date is not None:
            ref = f"Title: {title.text}\n"
            ref += f"Authors: {', '.join(author_names)}\n"
            ref += f"Published in: {publication.text}\n"
            ref += f"Date: {date.get('when')}\n"
            if volume is not None:
                ref += f"Volume: {volume.text}\n"
            if pages is not None:
                ref += f"Pages: {pages.text}\n"
            ref += "\n"  # Add a newline for separation
            bibliography.append(ref)

    return '\n'.join(bibliography)

if __name__ == "__main__":
    PDF_DIR = "/Users/franciscoteixeirabarbosa/Dropbox/Science in Dentistry APP/pdf_extractor/sections_extractor/pdfs"
    XML_DIR = "/Users/franciscoteixeirabarbosa/Dropbox/Science in Dentistry APP/pdf_extractor/sections_extractor/xml_files"
    OUTPUT_DIR = "/Users/franciscoteixeirabarbosa/Dropbox/Science in Dentistry APP/pdf_extractor/sections_extractor/bibliography_output"
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Start the GROBID service
    start_grobid_service()

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
            bibliography = extract_bibliography(root, ns)
            output_file_path = os.path.join(OUTPUT_DIR, f'{pdf_file.replace(".pdf", "")}_bibliography.txt')
            with open(output_file_path, 'w', encoding='utf-8') as f:
                f.write(bibliography)
            print(f"Bibliography for {pdf_file} has been written to {output_file_path}")
        except ET.ParseError as e:
            print(f"Error parsing XML file {xml_output_path}: {e}")