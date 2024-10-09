import os
import json
import glob
import time
import logging
import requests
from dotenv import load_dotenv
from datetime import datetime

# -------------------- Configuration --------------------

# Load environment variables
load_dotenv()

# Directory containing the JSON files
JSON_DIR = 'processed_contracts/'

# Directory to save the enhanced JSON files
ENHANCED_JSON_DIR = 'enhanced_contracts/'

# Ensure the enhanced directory exists
os.makedirs(ENHANCED_JSON_DIR, exist_ok=True)

# Perplexity API endpoint
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"

# Perplexity API model
PERPLEXITY_MODEL = "llama-3.1-sonar-small-128k-online"

# Your Perplexity API token
PERPLEXITY_API_TOKEN = os.getenv("PERPLEXITY_API_KEY")

# Delay between API calls in seconds to respect rate limits
API_DELAY = 1  # Adjust as needed

# Maximum number of retries for API calls
MAX_RETRIES = 3

# Logging configuration
LOG_FILE = 'enhance_descriptions.log'
logging.basicConfig(
    filename=LOG_FILE,
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# -------------------------------------------------------

def enhance_description(website, title, description):
    """
    Sends a prompt to Perplexity API to enhance the description.

    Args:
        website (str): The buyer's website URL.
        title (str): The title of the procedure.
        description (str): The original description of the procedure.

    Returns:
        str: The enhanced description returned by the API.
    """
    prompt = (
        f"This is the buyer of a public tender:\n"
        f"{website}\n\n"
        f"They published a public tender notice with the following info:\n"
        f"\"title\": {title},\n"
        f"\"description\": {description}\n\n"
        f"Based on who they are and what they do, augment the proposal description such that I will be effectively able to look for suitable bidders. Reply ONLY with the enhanced description, NO OTHER TEXT OR EXPLANATION."
    )

    payload = {
        "model": PERPLEXITY_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "Be precise and concise. It is essential that you reply ONLY with the enhanced description, NO OTHER TEXT OR EXPLANATION."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.2,
        "top_p": 0.9,
        "return_citations": False,
        "search_domain_filter": [],
        "return_images": False,
        "return_related_questions": False,
        "search_recency_filter": "",
        "top_k": 0,
        "stream": False,
        "presence_penalty": 0,
        "frequency_penalty": 1
    }

    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_TOKEN}",
        "Content-Type": "application/json"
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.post(PERPLEXITY_API_URL, json=payload, headers=headers, timeout=60)
            if response.status_code == 200:
                data = response.json()
                # Extract the enhanced description from the response
                # Assuming the enhanced description is in the first choice
                enhanced_description = data.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
                if enhanced_description:
                    return enhanced_description
                else:
                    logging.error("Empty enhanced description received.")
                    return description  # Return original if empty
            else:
                logging.error(f"API request failed with status code {response.status_code}: {response.text}")
        except requests.exceptions.RequestException as e:
            logging.error(f"API request exception on attempt {attempt}: {e}")

        # Wait before retrying
        time.sleep(API_DELAY * attempt)

    logging.error("Max retries exceeded. Returning original description.")
    return description  # Return original if all retries fail

def process_json_file(file_path):
    """
    Processes a single JSON file: enhances the 'description' fields and saves to a new directory.

    Args:
        file_path (str): Path to the JSON file.
    """
    # Define the path for the enhanced JSON file
    file_name = os.path.basename(file_path)
    enhanced_file_path = os.path.join(ENHANCED_JSON_DIR, file_name)

    # Check if the enhanced file already exists
    if os.path.exists(enhanced_file_path):
        logging.info(f"Enhanced file already exists for {file_path}. Skipping processing.")
        return

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        buyer_website = data.get('buyer', {}).get('website', '')
        procedure_title = data.get('procedure', {}).get('title', '')
        procedure_description = data.get('procedure', {}).get('description', '')

        if not (buyer_website and procedure_title and procedure_description):
            logging.warning(f"Missing fields in {file_path}. Skipping enhancement.")
            return

        logging.info(f"Enhancing description for {file_path}")

        enhanced_description = enhance_description(buyer_website, procedure_title, procedure_description)

        # Update the 'procedure.description'
        data['procedure']['description'] = enhanced_description

        # Optionally, update 'lots[].description' if it exists
        lots = data.get('lots', [])
        for lot in lots:
            original_lot_description = lot.get('description', '')
            if original_lot_description:
                lot_enhanced_description = enhance_description(
                    buyer_website,
                    lot.get('title', ''),
                    original_lot_description
                )
                lot['description'] = lot_enhanced_description
        
        # Save the updated JSON to the enhanced directory
        with open(enhanced_file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logging.info(f"Successfully enhanced and saved to {enhanced_file_path}")

    except json.JSONDecodeError as e:
        logging.error(f"JSON decode error in {file_path}: {e}")
    except Exception as e:
        logging.error(f"Unexpected error processing {file_path}: {e}")

def main():
    """
    Main function to process all JSON files in the directory and save enhanced files to a new directory.
    """
    json_files = glob.glob(os.path.join(JSON_DIR, '*.json'))
    total_files = len(json_files)
    logging.info(f"Starting processing of {total_files} JSON files.")

    for idx, file_path in enumerate(json_files, start=1):
        logging.info(f"Processing file {idx}/{total_files}: {file_path}")
        process_json_file(file_path)
        time.sleep(API_DELAY)  # Respect API rate limits

    logging.info("Completed processing all JSON files.")

if __name__ == "__main__":
    main()
