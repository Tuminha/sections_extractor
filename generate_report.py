import os
import openai
import base64
import json
import subprocess
import time
from dotenv import load_dotenv
import requests

# Load environment variables from .env file
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# Configuration
OUTPUT_DIR = '/Users/franciscoteixeirabarbosa/Dropbox/Science in Dentistry APP/pdf_extractor/sections_extractor/images'
INTRODUCTION_OUTPUT_DIR = '/Users/franciscoteixeirabarbosa/Dropbox/Science in Dentistry APP/pdf_extractor/sections_extractor/introduction_output'
DISCUSSION_OUTPUT_DIR = '/Users/franciscoteixeirabarbosa/Dropbox/Science in Dentistry APP/pdf_extractor/sections_extractor/discussion_output'
RESULTS_OUTPUT_DIR = '/Users/franciscoteixeirabarbosa/Dropbox/Science in Dentistry APP/pdf_extractor/sections_extractor/results_output'
METHODS_OUTPUT_DIR = '/Users/franciscoteixeirabarbosa/Dropbox/Science in Dentistry APP/pdf_extractor/sections_extractor/methods_output'
METADATA_OUTPUT_DIR = '/Users/franciscoteixeirabarbosa/Dropbox/Science in Dentistry APP/pdf_extractor/sections_extractor/metadata_output'
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

def read_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def generate_report():
    # Ensure GROBID service is running
    start_grobid_service()

    # Read the content from the various sections
    introduction = read_file(os.path.join(INTRODUCTION_OUTPUT_DIR, 'introduction.txt'))
    discussion = read_file(os.path.join(DISCUSSION_OUTPUT_DIR, 'discussion.txt'))
    results = read_file(os.path.join(RESULTS_OUTPUT_DIR, 'results.txt'))
    methods = read_file(os.path.join(METHODS_OUTPUT_DIR, 'methods.txt'))
    metadata = read_file(os.path.join(METADATA_OUTPUT_DIR, 'metadata.txt'))

    # Read the images information
    images_info_path = os.path.join(OUTPUT_DIR, 'images_info.json')
    with open(images_info_path, 'r', encoding='utf-8') as file:
        images_info = json.load(file)

    # Extract the article title from metadata
    article_title = None
    for line in metadata.split('\n'):
        if line.startswith('Title:'):
            article_title = line.split(':', 1)[1].strip()
            break

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
        {"role": "system", "content": "You are a helpful assistant. Your role is to generate a comprehensive report based on the provided sections and images."},
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
    report_path = os.path.join(OUTPUT_DIR, 'final_report.txt')
    with open(report_path, 'w', encoding='utf-8') as file:
        file.write(report)

    print(f"Report has been written to {report_path}")

if __name__ == "__main__":
    generate_report()