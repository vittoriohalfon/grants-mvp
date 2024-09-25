import requests
import time
import json
from datetime import datetime
from pathlib import Path
import subprocess
import logging
import os
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
import traceback

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
    RATE_LIMIT_DELAY: float = 1.2  # seconds
    MAX_NOTICES: int = 15000
    THREADS: int = 3  # Number of threads for concurrent downloads
    CONCURRENT_DOWNLOADS: int = 1  # Reduce concurrent downloads
    DOWNLOAD_DELAY: float = 1.1  # Delay between downloads (seconds)
    MAX_DOWNLOAD_RETRIES: int = 5  # Maximum number of retries for downloads

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

    try:
        response = requests.post(Config.API_URL, json=payload, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        if 'notices' in result:
            result['notices'] = [filter_english_links(notice) for notice in result['notices']]
        return result
    except requests.RequestException as e:
        logger.error(f"Error in API request: {e}")
        return None

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

@retry(
    stop=stop_after_attempt(Config.MAX_DOWNLOAD_RETRIES),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception_type(requests.exceptions.RequestException)
)
def download_xml_file(xml_url: str, filepath: Path) -> bool:
    """
    Download XML file with retry logic and rate limiting.
    
    :param xml_url: URL of the XML file
    :param filepath: Path to save the file
    :return: True if download was successful, False otherwise
    """
    try:
        response = requests.get(xml_url)
        response.raise_for_status()
        with open(filepath, 'wb') as file:
            file.write(response.content)
        logger.info(f"Downloaded: {filepath.name}")
        return True
    except requests.RequestException as e:
        logger.warning(f"Error downloading {filepath.name}: {e}")
        raise  # This will trigger a retry
    except IOError as e:
        logger.error(f"Error writing file {filepath.name}: {e}")
        return False

def download_xml_files(contracts: List[Dict[str, Any]], xml_dir: Path) -> Tuple[int, int, List[Dict[str, Any]]]:
    new_downloads = 0
    skipped_downloads = 0
    failed_downloads = []

    with ThreadPoolExecutor(max_workers=Config.CONCURRENT_DOWNLOADS) as executor:
        future_to_contract = {}
        for contract in contracts:
            xml_path = xml_dir / f"{contract['publication-number']}.xml"
            if xml_path.exists():
                skipped_downloads += 1
                logger.info(f"Skipped existing file: {xml_path.name}")
            else:
                future = executor.submit(download_xml_file, contract['links']['xml']['MUL'], xml_path)
                future_to_contract[future] = contract

        for future in as_completed(future_to_contract):
            contract = future_to_contract[future]
            try:
                if future.result():
                    new_downloads += 1
                else:
                    failed_downloads.append(contract)
            except Exception as e:
                logger.error(f"Error downloading {contract['publication-number']}: {e}")
                failed_downloads.append(contract)
            
            # Add delay between downloads
            time.sleep(Config.DOWNLOAD_DELAY)

    # Retry failed downloads
    for contract in failed_downloads[:]:  # Create a copy to iterate over
        xml_url = contract['links']['xml']['MUL']
        filepath = xml_dir / f"{contract['publication-number']}.xml"
        logger.info(f"Retrying download for {contract['publication-number']}")
        try:
            if download_xml_file(xml_url, filepath):
                new_downloads += 1
                failed_downloads.remove(contract)
            else:
                logger.warning(f"Failed to download {contract['publication-number']} after retries")
        except Exception as e:
            logger.error(f"Failed to download {contract['publication-number']} after retries: {e}")

        # Add delay between retries
        time.sleep(Config.DOWNLOAD_DELAY)

    # Log remaining failed downloads
    if failed_downloads:
        logger.warning(f"Failed to download {len(failed_downloads)} files after retries:")
        for contract in failed_downloads:
            logger.warning(f"  - {contract['publication-number']}")

    return new_downloads, skipped_downloads, failed_downloads

def process_xml_file(xml_file: Path, output_dir: Path) -> None:
    """
    Process a single XML file using process_single_xml.py
    
    :param xml_file: Path to the XML file
    :param output_dir: Directory to save the processed JSON file
    """
    output_file = output_dir / f"{xml_file.stem}.json"
    try:
        subprocess.run(["python", "process_single_xml.py", str(xml_file), str(output_file)], check=True)
        logger.info(f"Processed: {xml_file.name} -> {output_file.name}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error processing {xml_file.name}: {e}")
        logger.error(f"Command output: {e.output}")
    except Exception as e:
        logger.error(f"Unexpected error processing {xml_file.name}: {e}")
        logger.error(traceback.format_exc())  # Log the full traceback

def process_xml_files(xml_dir: Path, output_dir: Path) -> None:
    """
    Process all XML files in the given directory
    
    :param xml_dir: Directory containing XML files
    :param output_dir: Directory to save processed JSON files
    """
    output_dir.mkdir(exist_ok=True)
    xml_files = list(xml_dir.glob("*.xml"))
    logger.info(f"Found {len(xml_files)} XML files to process.")
    
    for i, xml_file in enumerate(xml_files, 1):
        logger.info(f"Processing file {i} of {len(xml_files)}: {xml_file.name}")
        process_xml_file(xml_file, output_dir)
    
    logger.info(f"Finished processing {len(xml_files)} XML files.")

# Main function to run the script
def main() -> None:
    try:
        all_notices: List[Dict[str, Any]] = []
        page = 1
        total_retrieved = 0

        while True:
            logger.info(f"Retrieving page {page}...")
            result = search_ted_contracts(page=page)
            
            if not result or 'notices' not in result:
                logger.warning(f"No notices found on page {page}. Stopping retrieval.")
                break

            notices = result['notices']
            all_notices.extend(notices)
            total_retrieved += len(notices)
            
            logger.info(f"Retrieved {len(notices)} notices. Total: {total_retrieved}")

            if len(notices) < 250 or total_retrieved >= Config.MAX_NOTICES:
                break

            page += 1

        if not all_notices:
            logger.warning("No notices retrieved. Exiting.")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"TED_IRELAND_CONTRACTS_{timestamp}.json"
        save_to_json(all_notices, filename)
        logger.info(f"Saved {len(all_notices)} notices to {filename}")

        # Load the JSON file containing contract information
        try:
            with open(filename, 'r') as file:
                contracts = json.load(file)
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from {filename}: {e}")
            return
        except IOError as e:
            logger.error(f"Error reading file {filename}: {e}")
            return

        # Create directories
        xml_dir = Path('contracts_xml')
        xml_dir.mkdir(exist_ok=True)
        processed_dir = Path('processed_contracts')
        processed_dir.mkdir(exist_ok=True)

        # Download XML files concurrently
        logger.info("Starting XML file downloads...")
        new_downloads, skipped_downloads, failed_downloads = download_xml_files(contracts, xml_dir)
        logger.info(f"Downloaded {new_downloads} new XML files, skipped {skipped_downloads} existing files.")

        # If there are failed downloads, wait and retry
        if failed_downloads:
            logger.info(f"Waiting 2 minutes before retrying {len(failed_downloads)} failed downloads...")
            time.sleep(120)  # Wait for 2 minutes
            retry_downloads, retry_skipped, still_failed = download_xml_files(failed_downloads, xml_dir)
            logger.info(f"Successfully downloaded {retry_downloads} files on retry, skipped {retry_skipped}.")
            if still_failed:
                logger.warning(f"Failed to download {len(still_failed)} files after retries:")
                for contract in still_failed:
                    logger.warning(f"  - {contract['publication-number']}")

        # Process XML files
        logger.info("Starting XML file processing...")
        process_xml_files(xml_dir, processed_dir)
        logger.info("XML processing complete. Check the processed_contracts directory for results.")

    except Exception as e:
        logger.error(f"Unexpected error in main function: {e}")
        logger.error(traceback.format_exc())  # Log the full traceback
        sys.exit(1)

if __name__ == "__main__":
    main()