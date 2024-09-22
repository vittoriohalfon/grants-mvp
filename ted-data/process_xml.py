import xml.etree.ElementTree as ET
import json
import logging
from pathlib import Path
import sys

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_text(element, xpath, default=""):
    try:
        return element.find(xpath, namespaces=namespaces).text
    except AttributeError:
        logging.warning(f"Unable to find {xpath}")
        return default

def extract_contract_info(root):
    contract_info = {
        "buyer": {
            "official_name": extract_text(root, ".//cac:PartyName/cbc:Name"),
            "email": extract_text(root, ".//cac:Contact/cbc:ElectronicMail"),
            "legal_type": extract_text(root, ".//cbc:PartyTypeCode"),
            "activity": extract_text(root, ".//cbc:ActivityTypeCode")
        },
        "procedure": {
            "title": extract_text(root, ".//cac:ProcurementProject/cbc:Name"),
            "description": extract_text(root, ".//cac:ProcurementProject/cbc:Description"),
            "identifier": extract_text(root, ".//cbc:ID[@schemeName='notice-id']"),
            "type": extract_text(root, ".//cbc:ProcedureCode"),
            "accelerated": extract_text(root, ".//cbc:ProcessReasonCode[@listName='accelerated-procedure']")
        },
        "purpose": {
            "main_nature": extract_text(root, ".//cbc:ProcurementTypeCode"),
            "main_classification": extract_text(root, ".//cac:MainCommodityClassification/cbc:ItemClassificationCode"),
            "place_of_performance": ""  # Not found in the provided XML
        },
        "value": {
            "estimated_value": extract_text(root, ".//cbc:EstimatedOverallContractAmount"),
            "maximum_value": extract_text(root, ".//efbc:FrameworkMaximumAmount")
        },
        "general_information": {
            "terms_of_submission": extract_text(root, ".//cbc:SubmissionMethodCode")
        },
        "lots": [],
        "useful_links": []
    }

    # Extract useful links
    for attachment in root.findall(".//cac:CallForTendersDocumentReference/cac:Attachment/cac:ExternalReference", namespaces):
        uri = extract_text(attachment, "cbc:URI")
        if uri:
            contract_info["useful_links"].append(uri)

    return contract_info

def extract_lot_info(lot):
    lot_info = {
        "lot": extract_text(lot, "cbc:ID"),
        "title": extract_text(lot, ".//cac:ProcurementProject/cbc:Name"),
        "description": extract_text(lot, ".//cac:ProcurementProject/cbc:Description"),
        "main_nature": extract_text(lot, ".//cac:ProcurementProject/cbc:ProcurementTypeCode"),
        "main_classification": extract_text(lot, ".//cac:MainCommodityClassification/cbc:ItemClassificationCode"),
        "place_of_performance": "",  # Not found in the provided XML
        "country": "",  # Not found in the provided XML
        "value": {
            "estimated_value": extract_text(lot, ".//cbc:EstimatedOverallContractAmount"),
            "maximum_value": extract_text(lot, ".//efbc:FrameworkMaximumAmount")
        },
        "general_information": {
            "reserved_participation": extract_text(lot, ".//cbc:TendererRequirementTypeCode[@listName='reserved-procurement']"),
            "selection_criteria": extract_text(lot, ".//cbc:CriterionTypeCode[@listName='selection-criterion']")
        }
    }
    return lot_info

def process_xml_file(file_path):
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        global namespaces
        namespaces = {k: v for k, v in root.attrib.items() if k.startswith('xmlns')}
        namespaces['cac'] = 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2'
        namespaces['cbc'] = 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'
        namespaces['efbc'] = 'http://data.europa.eu/p27/eforms-ubl-extension-basic-components/1'

        contract_info = extract_contract_info(root)

        for lot in root.findall(".//cac:ProcurementProjectLot", namespaces):
            lot_info = extract_lot_info(lot)
            contract_info["lots"].append(lot_info)

        return contract_info

    except ET.ParseError as e:
        logging.error(f"Error parsing XML file {file_path}: {e}")
    except Exception as e:
        logging.error(f"Unexpected error processing file {file_path}: {e}")

def main():
    # Get the directory of the script
    script_dir = Path(__file__).parent.resolve()
    input_directory = script_dir / "contracts_xml"  # Change to contracts_xml folder
    output_file = script_dir / "processed_contracts.json"

    all_contracts = []

    # Process all XML files in the contracts_xml directory
    for xml_file in input_directory.glob("*.xml"):
        logging.info(f"Processing file: {xml_file}")
        contract_info = process_xml_file(xml_file)
        if contract_info:
            all_contracts.append(contract_info)

    # Ensure the output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_contracts, f, ensure_ascii=False, indent=2)

    logging.info(f"Processed {len(all_contracts)} contracts. Output saved to {output_file}")

if __name__ == "__main__":
    main()

