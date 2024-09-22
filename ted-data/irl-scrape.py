import requests
import json
from datetime import datetime
from pathlib import Path
import subprocess
import logging
import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
class Config:
    API_URL: str = "https://api.ted.europa.eu/v3/notices/search"
    QUERY: str = "OJ = () AND total-value-cur=EUR AND notice-type IN (cn-standard cn-social) AND buyer-country=IRL SORT BY deadline-receipt-request DESC"
    FIELDS: List[str] = ["BT-09(b)-Procedure"]
    MAX_RETRIES: int = 3
    RATE_LIMIT_DELAY: float = 1.0  # seconds
    MAX_NOTICES: int = 15000

# Load API key from environment variable
API_KEY: str = os.getenv("TED_API_KEY", "")
if not API_KEY:
    raise ValueError("TED_API_KEY environment variable is not set")

@retry(stop=stop_after_attempt(Config.MAX_RETRIES), wait=wait_exponential(multiplier=1, min=4, max=10))
def search_ted_contracts(page: int = 1, limit: int = 250) -> Optional[Dict[str, Any]]:
    """
    Search TED contracts with retry logic.
    
    :param page: Page number for pagination
    :param limit: Number of results per page
    :return: JSON response from the API or None if failed
    """
    payload = {
        "query": Config.QUERY,
        "fields": Config.FIELDS,
        "page": page,
        "limit": limit,
        "scope": "ACTIVE",
        "paginationMode": "PAGE_NUMBER",
        "onlyLatestVersions": True
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    response = requests.post(Config.API_URL, json=payload, headers=headers)
    response.raise_for_status()
    
    result = response.json()
    if 'notices' in result:
        result['notices'] = [filter_english_links(notice) for notice in result['notices']]
    return result

def filter_english_links(notice: Dict[str, Any]) -> Dict[str, Any]:
    """Filter out non-English links from the notice."""
    if 'links' in notice:
        for link_type in notice['links']:
            if isinstance(notice['links'][link_type], dict) and 'ENG' in notice['links'][link_type]:
                notice['links'][link_type] = {'ENG': notice['links'][link_type]['ENG']}
            elif link_type == 'xml':
                # Keep the 'xml' link as it's usually language-independent
                pass
            else:
                notice['links'][link_type] = {}
    return notice

def save_to_json(data: List[Dict[str, Any]], filename: str) -> None:
    """Save data to a JSON file."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@retry(stop=stop_after_attempt(Config.MAX_RETRIES), wait=wait_exponential(multiplier=1, min=4, max=10))
def download_xml_file(xml_url: str, filepath: Path) -> bool:
    """
    Download XML file with retry logic.
    
    :param xml_url: URL of the XML file
    :param filepath: Path to save the file
    :return: True if download was successful, False otherwise
    """
    response = requests.get(xml_url)
    response.raise_for_status()
    with open(filepath, 'wb') as file:
        file.write(response.content)
    logger.info(f"Downloaded: {filepath.name}")
    return True

def main() -> None:
    all_notices: List[Dict[str, Any]] = []
    page = 1
    total_retrieved = 0

    while True:
        logger.info(f"Retrieving page {page}...")
        result = search_ted_contracts(page=page)
        
        if not result or 'notices' not in result:
            break

        notices = result['notices']
        all_notices.extend(notices)
        total_retrieved += len(notices)
        
        logger.info(f"Retrieved {len(notices)} notices. Total: {total_retrieved}")

        if len(notices) < 250 or total_retrieved >= Config.MAX_NOTICES:
            break

        page += 1

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"TED_IRELAND_CONTRACTS_{timestamp}.json"
    save_to_json(all_notices, filename)
    logger.info(f"Saved {len(all_notices)} notices to {filename}")

    # Load the JSON file containing contract information
    with open(filename, 'r') as file:
        contracts = json.load(file)

    # Create a directory to store XML files
    xml_dir = Path('contracts_xml')
    xml_dir.mkdir(exist_ok=True)

    # Download XML files
    new_downloads = 0
    for contract in contracts:
        xml_url = contract['links']['xml']['MUL']
        publication_number = contract['publication-number']
        
        # Construct the filename
        filename = f"{publication_number}.xml"
        filepath = xml_dir / filename
        
        if filepath.exists():
            logger.info(f"Skipping existing file: {filename}")
            continue

        if download_xml_file(xml_url, filepath):
            new_downloads += 1

    logger.info(f"Downloaded {new_downloads} new XML files.")

    # After downloading all XML files, run process_xml.py
    if new_downloads > 0:
        logger.info("Running process_xml.py...")
        try:
            subprocess.run(["python", "process_xml.py"], check=True)
            logger.info("XML processing complete. Check processed_contracts.json for results.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error running process_xml.py: {e}")
    else:
        logger.info("No new XML files to process. Skipping process_xml.py")

if __name__ == "__main__":
    main()