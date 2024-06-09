import os
import openai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def interpret_tables_with_ai(file_path):
    # Read the content of the tables.txt file
    with open(file_path, 'r', encoding='utf-8') as file:
        tables_text = file.read()

    # Prepare the prompt for the AI
    prompt = f"""
    Interpret the following tables and provide a summary of the key findings:
    {tables_text}
    """

    # Initialize the OpenAI client
    client = openai.OpenAI(
        api_key=os.getenv("OPENAI_API_KEY")
    )

    # Define the messages for the chat completion
    messages = [
        {"role": "system", "content": "You are a data analysis assistant. Your role is to interpret scientific tables and provide clear, concise summaries of the key findings. Focus on the main results, statistical significance, and any notable patterns or trends."},
        {"role": "user", "content": prompt}
    ]

    # Get the response from the AI
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=2000
    )

    # Extract and return the output text
    if response.choices:
        output_text = response.choices[0].message.content
        return output_text.strip()
    else:
        return "No completion found."

if __name__ == "__main__":
    # Define the path to the tables.txt file
    file_path = "/Users/franciscoteixeirabarbosa/Dropbox/Science in Dentistry APP/pdf_extractor/sections_extractor/results_output/tables.txt"
    
    # Interpret the tables using the AI
    summary = interpret_tables_with_ai(file_path)
    
    # Print the summary
    print(summary)