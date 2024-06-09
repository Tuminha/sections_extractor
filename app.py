import os
import xml.etree.ElementTree as ET
import subprocess
import time
import requests
import json
import openai
from metadata import extract_metadata
from abstract import process_pdf_for_abstract
from bibliography import extract_bibliography
from discussion import extract_discussion
from methods import extract_material_and_methods
from conclusion import extract_conclusion
from introduction import extract_introduction
from results import extract_results
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# Configuration
PDF_DIR = "/Users/franciscoteixeirabarbosa/Dropbox/Science in Dentistry APP/pdf_extractor/sections_extractor/pdfs"
OUTPUT_DIR = 'Users/franciscoteixeirabarbosa/Dropbox/Science in Dentistry APP/pdf_extractor/sections_extractor/articles_generated'
OUTPUT_DIR = '/Users/franciscoteixeirabarbosa/Dropbox/Science in Dentistry APP/pdf_extractor/sections_extractor/articles_generated'
XML_DIR = '/Users/franciscoteixeirabarbosa/Dropbox/Science in Dentistry APP/pdf_extractor/sections_extractor/xml_files'
ABSTRACT_OUTPUT_DIR = '/Users/franciscoteixeirabarbosa/Dropbox/Science in Dentistry APP/pdf_extractor/sections_extractor/abstract_output'
IMAGES_OUTPUT_DIR = '/Users/franciscoteixeirabarbosa/Dropbox/Science in Dentistry APP/pdf_extractor/sections_extractor/images'
PHD_REPORT_DIR = '/Users/franciscoteixeirabarbosa/Dropbox/Science in Dentistry APP/pdf_extractor/sections_extractor/phd_report'
GROBID_PATH = '/Users/franciscoteixeirabarbosa/projects/test/sections_pdf/grobid'
GROBID_URL = 'http://localhost:8070'

# Ensure the necessary directories exist
os.makedirs(XML_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(ABSTRACT_OUTPUT_DIR, exist_ok=True)
os.makedirs(IMAGES_OUTPUT_DIR, exist_ok=True)
os.makedirs(PHD_REPORT_DIR, exist_ok=True)

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

def read_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def generate_final_report(metadata, introduction, methods, results, discussion, conclusion, bibliography, images_info):
    # Extract the article title from metadata
    article_title = metadata.get('title', 'Unknown Title')

    # Prepare the prompt for the OpenAI API
    prompt = f"""
    You are an AI assistant. Please generate a comprehensive report for the article titled "{article_title}". 
    The report should analyze the images provided and include context from the following sections:

    Introduction:
    {introduction}

    Methods:
    {methods}

    Results:
    {results}

    Discussion:
    {discussion}

    Conclusion:
    {conclusion}

    Bibliography:
    {bibliography}

    Images:
    """
    for image_info in images_info:
        prompt += f"\n- {image_info['description']}: {image_info['path']}"

    prompt += "\n\nPlease provide a detailed analysis of the images in the context of the provided sections. The report should be between 1000 to 2000 tokens."

    # Make the API call to OpenAI
    client = openai.OpenAI(
        api_key=OPENAI_API_KEY
    )

    messages = [
        {"role": "system", "content": "You are a critical-thinking AI trained to analyze scientific articles meticulously. Your role is to critically evaluate each section of the article, looking for gaps, flaws, and inconsistencies."},
        {"role": "user", "content": prompt}
    ]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=2000,
        temperature=0.7
    )

    if response.choices:
        report = response.choices[0].message.content.strip()
    else:
        report = "No report generated."

    # Save the report to a file
    report_path = os.path.join(PHD_REPORT_DIR, f'{article_title.replace(" ", "_").replace("/", "_")}_final_report.txt')
    with open(report_path, 'w', encoding='utf-8') as file:
        file.write(report)

    print(f"Report has been written to {report_path}")

def main():
    # Start the GROBID service
    start_grobid_service()

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

        # Send the PDF to GROBID
        try:
            with open(pdf_path, 'rb') as f:
                response = requests.post(f'{GROBID_URL}/api/processFulltextDocument', files={'input': f}, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error processing file {pdf_path}: {e}")
            continue

        # Generate a consistent XML filename based on the PDF filename
        pdf_filename = os.path.basename(pdf_path)
        xml_filename = pdf_filename.replace('.pdf', '.xml')
        xml_output_path = os.path.join(XML_DIR, xml_filename)

        # Save the XML output
        with open(xml_output_path, 'w', encoding='utf-8') as f:
            f.write(response.text)

        if os.path.exists(xml_output_path):
            print(f"XML file created: {xml_output_path}")
        else:
            print(f"Failed to create XML file: {xml_output_path}")
            continue

        # Parse the XML output
        try:
            tree = ET.parse(xml_output_path)
            root = tree.getroot()
            ns = {'tei': 'http://www.tei-c.org/ns/1.0'}
        except ET.ParseError as e:
            print(f"Error parsing XML file {xml_output_path}: {e}")
            continue

        # Extract sections
        metadata = extract_metadata(root, ns)
        introduction = extract_introduction(root, ns)
        methods = extract_material_and_methods(root, ns)
        results = extract_results(root, ns)
        discussion = extract_discussion(root, ns)
        conclusion = extract_conclusion(root, ns)
        bibliography = extract_bibliography(root, ns)

        # Read images information
        images_info_path = os.path.join(IMAGES_OUTPUT_DIR, 'images_info.json')
        with open(images_info_path, 'r', encoding='utf-8') as file:
            images_info = json.load(file)

        # Generate the final report
        generate_final_report(metadata, introduction, methods, results, discussion, conclusion, bibliography, images_info)

if __name__ == "__main__":
    main()

