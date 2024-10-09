import xml.etree.ElementTree as ET
import json
import logging
import re
from pathlib import Path
import sys
import traceback
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Import functions from process_single_xml.py
from process_single_xml import extract_contract_info, extract_lot_info, namespaces as xml_namespaces

# Import function from process_single_type2.py
from process_single_type2 import parse_xml_to_json as parse_type2_xml_to_json

def process_contract_notice(root, file_path):
    try:
        # Extract notice publication ID from filename
        filename = Path(file_path).name
        notice_id_match = re.search(r'(\d+)-(\d+)', filename)
        notice_id = f"{notice_id_match.group(1)}-{notice_id_match.group(2)}" if notice_id_match else ""

        contract_info = extract_contract_info(root, notice_id)

        for lot in root.findall(".//cac:ProcurementProjectLot", xml_namespaces):
            lot_info = extract_lot_info(lot)
            contract_info["lots"].append(lot_info)

        return contract_info

    except Exception as e:
        logging.error(f"Error processing ContractNotice file {file_path}: {str(e)}")
        logging.error(traceback.format_exc())
        return None

def process_ted_export(xml_content, file_name):
    try:
        return json.loads(parse_type2_xml_to_json(xml_content, file_name))
    except Exception as e:
        logging.error(f"Error processing TED_EXPORT file {file_name}: {str(e)}")
        logging.error(traceback.format_exc())
        return None

def process_xml_file(file_path):
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        if root.tag.endswith('ContractNotice'):
            return process_contract_notice(root, file_path)
        elif root.tag == 'TED_EXPORT':
            with open(file_path, 'r', encoding='utf-8') as file:
                xml_content = file.read()
            return process_ted_export(xml_content, Path(file_path).name)
        else:
            logging.warning(f"Unknown root element {root.tag} in file {file_path}")
            return None

    except ET.ParseError as e:
        logging.error(f"Error parsing XML file {file_path}: {e}")
    except Exception as e:
        logging.error(f"Unexpected error processing file {file_path}: {str(e)}")
        logging.error(traceback.format_exc())
    return None

def process_all_xml_files(input_dir='contracts_xml', output_dir='processed_contracts'):
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for xml_file in input_path.glob('*.xml'):
        logging.info(f"Processing file: {xml_file}")
        contract_info = process_xml_file(xml_file)

        if contract_info:
            output_file = output_path / f"{xml_file.stem}.json"
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(contract_info, f, ensure_ascii=False, indent=2)
                logging.info(f"Processed contract. Output saved to {output_file}")
            except IOError as e:
                logging.error(f"Error writing to output file {output_file}: {e}")
        else:
            logging.warning(f"No contract processed for file: {xml_file}")

def main():
    try:
        process_all_xml_files()
    except Exception as e:
        logging.error(f"Unexpected error in main function: {e}")
        logging.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()