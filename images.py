import os
import pdfplumber
import logging
import xml.etree.ElementTree as ET
import openai
import base64
import subprocess
import time
from dotenv import load_dotenv
import requests
import json

# Load environment variables from .env file
load_dotenv()

# Configuration
PDF_DIR = '/Users/franciscoteixeirabarbosa/Dropbox/Science in Dentistry APP/pdf_extractor/sections_extractor/pdfs'
OUTPUT_DIR = '/Users/franciscoteixeirabarbosa/Dropbox/Science in Dentistry APP/pdf_extractor/sections_extractor/images'
XML_DIR = '/Users/franciscoteixeirabarbosa/Dropbox/Science in Dentistry APP/pdf_extractor/sections_extractor/xml_files'
GROBID_PATH = '/Users/franciscoteixeirabarbosa/projects/test/sections_pdf/grobid'
GROBID_URL = 'http://localhost:8070'
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Ensure the output directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(XML_DIR, exist_ok=True)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

openai.api_key = OPENAI_API_KEY

def start_grobid_service():
    try:
        response = requests.get(f'{GROBID_URL}/api/isalive', timeout=10)
        if response.status_code == 200:
            logging.info("GROBID service is already running.")
        else:
            # Start the GROBID service
            p = subprocess.Popen(['./gradlew', 'run', '--stacktrace'], cwd=GROBID_PATH)
            # Wait for the GROBID service to start
            time.sleep(10)
    except requests.exceptions.RequestException as e:
        # If the request fails, it means the service is not running
        logging.info("GROBID service is not running. Starting it now...")
        p = subprocess.Popen(['./gradlew', 'run', '--stacktrace'], cwd=GROBID_PATH)
        # Wait for the GROBID service to start
        time.sleep(10)

def extract_images_with_pdfplumber(pdf_path, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    images = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            for img_index, img in enumerate(page.images):
                img_bbox = (img['x0'], img['top'], img['x1'], img['bottom'])
                cropped_img = page.within_bbox(img_bbox).to_image()
                img_path = os.path.join(output_folder, f"page{page_num+1}_img{img_index+1}.png")
                cropped_img.save(img_path, format="PNG")
                images.append({"description": f"Image from page {page_num+1}, image {img_index+1}", "path": img_path})
                logging.info(f"Saved image: {img_path}")
    return images

def extract_figures_from_xml(xml_path):
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        ns = {'tei': 'http://www.tei-c.org/ns/1.0'}
        
        figures = []
        for figure in root.findall('.//tei:figure', ns):
            fig_id = figure.get('{http://www.w3.org/XML/1998/namespace}id')
            fig_desc = figure.find('tei:figDesc', ns).text if figure.find('tei:figDesc', ns) is not None else "No description"
            figures.append((fig_id, fig_desc))
        return figures
    except Exception as e:
        logging.error(f"Unexpected error with XML file {xml_path}: {e}")
        return []

def match_image_with_description(image_path, descriptions):
    with open(image_path, "rb") as image_file:
        image_data = image_file.read()
    
    image_base64 = base64.b64encode(image_data).decode('utf-8')
    
    prompt = f"""
    You are an AI assistant. Please match the following image with the correct description from the list below:
    Image (base64): {image_base64}
    Descriptions:
    """
    client = openai.OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY")
    )
    
    for i, desc in enumerate(descriptions):
        prompt += f"{i+1}. {desc}\n"
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant. Your role is to match images with their correct descriptions based on the provided list. Use your vision capabilities to analyze the image and find the best matching description."},
        {"role": "user", "content": prompt}
    ]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=3000,
        temperature=0.3
    )
    
    if response.choices:
        return response.choices[0].message.content.strip()
    else:
        return "No match found"

def process_pdf_with_grobid(pdf_path, xml_output_path, grobid_url):
    with open(pdf_path, 'rb') as f:
        response = requests.post(f'{grobid_url}/api/processFulltextDocument', files={'input': f}, timeout=10)
        response.raise_for_status()
    
    with open(xml_output_path, 'w', encoding='utf-8') as f:
        f.write(response.text)

def main():
    logging.info("Starting GROBID service...")
    start_grobid_service()

    if not os.path.exists(PDF_DIR):
        logging.error(f"PDF directory does not exist: {PDF_DIR}")
        return

    if not os.path.exists(XML_DIR):
        logging.error(f"XML directory does not exist: {XML_DIR}")
        return

    pdf_files = [f for f in os.listdir(PDF_DIR) if f.endswith('.pdf')]
    logging.info(f"Found {len(pdf_files)} PDF files in {PDF_DIR}")

    all_images_info = []

    for pdf_file in pdf_files:
        pdf_path = os.path.join(PDF_DIR, pdf_file)
        xml_file = pdf_file.replace('.pdf', '.xml')
        xml_path = os.path.join(XML_DIR, xml_file)
        
        if not os.path.exists(xml_path):
            logging.info(f"Processing PDF with GROBID: {pdf_file}")
            process_pdf_with_grobid(pdf_path, xml_path, GROBID_URL)
        
        if not os.path.exists(xml_path):
            logging.warning(f"XML file not found for {pdf_file}")
            continue

        logging.info(f"Processing file: {pdf_path}")
        images_info = extract_images_with_pdfplumber(pdf_path, OUTPUT_DIR)
        logging.info(f"Extracted {len(images_info)} images from {pdf_path}")
        
        figures = extract_figures_from_xml(xml_path)
        logging.info(f"Extracted {len(figures)} figures from {xml_path}")
        
        descriptions = [desc for _, desc in figures]
        
        for image_info in images_info:
            image_path = image_info['path']
            logging.info(f"Processing image file: {image_path}")
            matched_description = match_image_with_description(image_path, descriptions)
            new_image_name = f"{matched_description[:50].replace(' ', '_').replace('/', '_')}.png"
            new_image_path = os.path.join(OUTPUT_DIR, new_image_name)
            os.rename(image_path, new_image_path)
            logging.info(f"Renamed image to: {new_image_path}")
            image_info['description'] = matched_description
            image_info['path'] = new_image_path

        all_images_info.extend(images_info)

    # Save all images information to a JSON file
    images_info_path = os.path.join(OUTPUT_DIR, 'images_info.json')
    with open(images_info_path, 'w', encoding='utf-8') as file:
        json.dump(all_images_info, file, indent=4)

    logging.info(f"Saved images information to {images_info_path}")

if __name__ == "__main__":
    main()
        