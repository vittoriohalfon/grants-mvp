import xml.etree.ElementTree as ET
import json
import logging
from pathlib import Path
import sys
import hashlib

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_text(element, xpath, default=""):
    try:
        result = element.find(xpath, namespaces=namespaces)
        if result is not None:
            if result.text:
                return result.text.strip()
            elif result.attrib:
                # If the element has attributes but no text, return the first attribute value
                return next(iter(result.attrib.values())).strip()
        logging.warning(f"Unable to find text for {xpath}")
        return default
    except AttributeError:
        logging.warning(f"Unable to find {xpath}")
        return default
    except Exception as e:
        logging.warning(f"Error extracting text for {xpath}: {e}")
        return default

def extract_contract_info(root):
    contract_info = {
        "buyer": {
            "official_name": extract_text(root, ".//efac:Organization/efac:Company/cac:PartyName/cbc:Name"),
            "email": extract_text(root, ".//efac:Organization/efac:Company/cac:Contact/cbc:ElectronicMail"),
            "legal_type": extract_text(root, ".//cbc:PartyTypeCode"),
            "activity": extract_text(root, ".//cbc:ActivityTypeCode"),
            "address": {
                "street": extract_text(root, ".//efac:Organization/efac:Company/cac:PostalAddress/cbc:StreetName"),
                "city": extract_text(root, ".//efac:Organization/efac:Company/cac:PostalAddress/cbc:CityName"),
                "postal_code": extract_text(root, ".//efac:Organization/efac:Company/cac:PostalAddress/cbc:PostalZone"),
                "country": extract_text(root, ".//efac:Organization/efac:Company/cac:PostalAddress/cac:Country/cbc:IdentificationCode")
            },
            "website": extract_text(root, ".//cbc:BuyerProfileURI")
        },
        "procedure": {
            "title": extract_text(root, ".//cac:ProcurementProject/cbc:Name"),
            "description": extract_text(root, ".//cac:ProcurementProject/cbc:Description"),
            "identifier": extract_text(root, ".//cbc:ID[@schemeName='notice-id']"),
            "type": extract_text(root, ".//cbc:ProcedureCode"),
            "accelerated": extract_text(root, ".//cbc:ProcessReasonCode[@listName='accelerated-procedure']"),
            "deadline_date": extract_text(root, ".//cac:TenderSubmissionDeadlinePeriod/cbc:EndDate"),
            "deadline_time": extract_text(root, ".//cac:TenderSubmissionDeadlinePeriod/cbc:EndTime")
        },
        "purpose": {
            "main_nature": extract_text(root, ".//cbc:ProcurementTypeCode"),
            "main_classification": extract_text(root, ".//cac:MainCommodityClassification/cbc:ItemClassificationCode"),
            "additional_classifications": [code.text for code in root.findall(".//cac:AdditionalCommodityClassification/cbc:ItemClassificationCode", namespaces)],
            "place_of_performance": extract_text(root, ".//cac:RealizedLocation/cbc:Description")
        },
        "value": {
            "estimated_value": extract_text(root, ".//cbc:EstimatedOverallContractAmount"),
            "currency": extract_text(root, ".//cbc:EstimatedOverallContractAmount/@currencyID"),
            "maximum_value": extract_text(root, ".//efbc:FrameworkMaximumAmount")
        },
        "general_information": {
            "terms_of_submission": extract_text(root, ".//cbc:SubmissionMethodCode"),
            "variant_submissions": extract_text(root, ".//cbc:VariantConstraintCode"),
            "electronic_invoicing": extract_text(root, ".//cbc:ExecutionRequirementCode[@listName='einvoicing']"),
            "electronic_ordering": extract_text(root, ".//cbc:ElectronicOrderUsageIndicator"),
            "electronic_payment": extract_text(root, ".//cbc:ElectronicPaymentUsageIndicator")
        },
        "lots": [],
        "useful_links": [],
        "pdf_link": extract_text(root, ".//cac:CallForTendersDocumentReference/cac:Attachment/cac:ExternalReference/cbc:URI")
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
        "additional_classifications": [code.text for code in lot.findall(".//cac:AdditionalCommodityClassification/cbc:ItemClassificationCode", namespaces)],
        "place_of_performance": extract_text(lot, ".//cac:RealizedLocation/cbc:Description"),
        "country": extract_text(lot, ".//cac:RealizedLocation/cac:Address/cac:Country/cbc:IdentificationCode"),
        "value": {
            "estimated_value": extract_text(lot, ".//cbc:EstimatedOverallContractAmount"),
            "currency": extract_text(lot, ".//cbc:EstimatedOverallContractAmount/@currencyID"),
            "maximum_value": extract_text(lot, ".//efbc:FrameworkMaximumAmount")
        },
        "general_information": {
            "reserved_participation": extract_text(lot, ".//cbc:TendererRequirementTypeCode[@listName='reserved-procurement']"),
            "selection_criteria": extract_text(lot, ".//cbc:CriterionTypeCode[@listName='selection-criterion']"),
            "variant_submissions": extract_text(lot, ".//cbc:VariantConstraintCode"),
            "electronic_invoicing": extract_text(lot, ".//cbc:ExecutionRequirementCode[@listName='einvoicing']"),
            "electronic_ordering": extract_text(lot, ".//cbc:ElectronicOrderUsageIndicator"),
            "electronic_payment": extract_text(lot, ".//cbc:ElectronicPaymentUsageIndicator")
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
        namespaces['efac'] = 'http://data.europa.eu/p27/eforms-ubl-extension-aggregate-components/1'

        contract_info = extract_contract_info(root)

        for lot in root.findall(".//cac:ProcurementProjectLot", namespaces):
            lot_info = extract_lot_info(lot)
            contract_info["lots"].append(lot_info)

        return contract_info

    except ET.ParseError as e:
        logging.error(f"Error parsing XML file {file_path}: {e}")
    except Exception as e:
        logging.error(f"Unexpected error processing file {file_path}: {str(e)}")

def calculate_file_hash(file_path):
    """Calculate the MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def main():
    # Get the directory of the script
    script_dir = Path(__file__).parent.resolve()
    input_directory = script_dir / "contracts_xml"
    output_file = script_dir / "processed_contracts.json"
    hash_file = script_dir / "processed_files_hashes.json"

    all_contracts = []
    processed_hashes = {}

    # Load existing processed file hashes
    if hash_file.exists():
        with open(hash_file, 'r') as f:
            processed_hashes = json.load(f)

    new_processed = 0

    # Process all XML files in the contracts_xml directory
    for xml_file in input_directory.glob("*.xml"):
        file_hash = calculate_file_hash(xml_file)
        
        # Skip files that have already been processed
        if file_hash in processed_hashes:
            logging.info(f"Skipping already processed file: {xml_file.name}")
            continue

        logging.info(f"Processing file: {xml_file}")
        contract_info = process_xml_file(xml_file)
        if contract_info:
            all_contracts.append(contract_info)
            processed_hashes[file_hash] = xml_file.name
            new_processed += 1

    if new_processed > 0:
        # Ensure the output directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Always overwrite the existing processed contracts
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_contracts, f, ensure_ascii=False, indent=2)

        # Save updated hash file
        with open(hash_file, 'w') as f:
            json.dump(processed_hashes, f, indent=2)

        logging.info(f"Processed {new_processed} contracts. Total contracts: {len(all_contracts)}. Output saved to {output_file}")
    else:
        logging.info("No contracts processed.")

if __name__ == "__main__":
    main()

