import requests
import json
from datetime import datetime
from pathlib import Path
import subprocess
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# TED API endpoint
API_URL = "https://api.ted.europa.eu/v3/notices/search"

# Expert search query
QUERY = "OJ = () AND total-value-cur=EUR AND notice-type IN (cn-standard cn-social) AND buyer-country=IRL SORT BY deadline-receipt-request DESC"

# Fields to retrieve
FIELDS = ["BT-09(b)-Procedure"]

def filter_english_links(notice):
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

def search_ted_contracts(page=1, limit=250):
    payload = {
        "query": QUERY,
        "fields": FIELDS,
        "page": page,
        "limit": limit,
        "scope": "ACTIVE",
        "paginationMode": "PAGE_NUMBER",
        "onlyLatestVersions": True
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    response = requests.post(API_URL, json=payload, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        if 'notices' in result:
            result['notices'] = [filter_english_links(notice) for notice in result['notices']]
        return result
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

def save_to_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def download_xml_file(xml_url, filepath):
    try:
        response = requests.get(xml_url)
        response.raise_for_status()
        with open(filepath, 'wb') as file:
            file.write(response.content)
        logging.info(f"Downloaded: {filepath.name}")
        return True
    except requests.RequestException as e:
        logging.error(f"Failed to download {filepath.name}: {e}")
        return False

def main():
    all_notices = []
    page = 1
    total_retrieved = 0

    while True:
        logging.info(f"Retrieving page {page}...")
        result = search_ted_contracts(page=page)
        
        if not result or 'notices' not in result:
            break

        notices = result['notices']
        all_notices.extend(notices)
        total_retrieved += len(notices)
        
        logging.info(f"Retrieved {len(notices)} notices. Total: {total_retrieved}")

        if len(notices) < 250 or total_retrieved >= 15000:
            break

        page += 1

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"TED_IRELAND_CONTRACTS_{timestamp}.json"
    save_to_json(all_notices, filename)
    logging.info(f"Saved {len(all_notices)} notices to {filename}")

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
            logging.info(f"Skipping existing file: {filename}")
            continue

        if download_xml_file(xml_url, filepath):
            new_downloads += 1

    logging.info(f"Downloaded {new_downloads} new XML files.")

    # After downloading all XML files, run process_xml.py
    if new_downloads > 0:
        logging.info("Running process_xml.py...")
        try:
            subprocess.run(["python", "process_xml.py"], check=True)
            logging.info("XML processing complete. Check processed_contracts.json for results.")
        except subprocess.CalledProcessError as e:
            logging.error(f"Error running process_xml.py: {e}")
    else:
        logging.info("No new XML files to process. Skipping process_xml.py")

if __name__ == "__main__":
    main()