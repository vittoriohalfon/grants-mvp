# process_xml_directory.py

import xml.etree.ElementTree as ET
import json
import logging
from pathlib import Path
import argparse
import re
import sys
import traceback
import os
import time

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add a file handler to log to a file
file_handler = logging.FileHandler('process_contracts.log')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

##############################
# Helper Functions
##############################

def get_localname(tag):
    """
    Extracts the local name from an XML tag.

    Args:
        tag (str): The XML tag with or without namespace.

    Returns:
        str: The local name of the tag.
    """
    if '}' in tag:
        return tag.split('}', 1)[1]
    else:
        return tag

def extract_text(element, xpath, namespaces, default="", attribute=None, current_root=None):
    """
    Extracts text or attribute from an XML element based on the provided XPath.

    Args:
        element (xml.etree.ElementTree.Element): The XML element to search within.
        xpath (str): The XPath string to locate the desired element.
        namespaces (dict): Dictionary of XML namespaces.
        default (str, optional): Default value to return if the element or attribute is not found.
        attribute (str, optional): The attribute name to extract from the found element.
        current_root (xml.etree.ElementTree.Element, optional): The current root for relative searching.

    Returns:
        str: Extracted text or attribute value, or the default value.
    """
    try:
        root = current_root if current_root is not None else element
        result = root.find(xpath, namespaces=namespaces)
        if result is not None:
            if attribute:
                return result.get(attribute, default)
            elif result.text:
                return result.text.strip()
            elif result.attrib:
                # Return the first attribute value if no specific attribute is requested
                return next(iter(result.attrib.values())).strip()
            else:
                # If there's no text and no attributes, check for child elements
                child_texts = [child.text.strip() for child in result if child.text]
                if child_texts:
                    return ", ".join(child_texts)
        logger.warning(f"Unable to find text for XPath: {xpath}")
        return default
    except AttributeError:
        logger.warning(f"AttributeError while extracting XPath: {xpath}")
        return default
    except Exception as e:
        logger.warning(f"Error extracting text for XPath: {xpath} - {e}")
        return default

##############################
# Processing for <ContractNotice>
##############################

def extract_contract_info(root, notice_id, namespaces):
    """
    Extracts contract information from a <ContractNotice> XML root.

    Args:
        root (xml.etree.ElementTree.Element): The root element of the XML.
        notice_id (str): The notice publication ID extracted from the filename.
        namespaces (dict): Dictionary of XML namespaces.

    Returns:
        dict: A dictionary containing the extracted contract information.
    """
    contract_info = {
        "notice_publication_id": notice_id,
        "buyer": {
            "official_name": extract_text(root, ".//efac:Organization/efac:Company/cac:PartyName/cbc:Name", namespaces),
            "email": extract_text(root, ".//efac:Organization/efac:Company/cac:Contact/cbc:ElectronicMail", namespaces),
            "legal_type": extract_text(root, ".//cbc:PartyTypeCode", namespaces),
            "activity": extract_text(root, ".//cbc:ActivityTypeCode", namespaces),
            "address": {
                "street": extract_text(root, ".//efac:Organization/efac:Company/cac:PostalAddress/cbc:StreetName", namespaces),
                "city": extract_text(root, ".//efac:Organization/efac:Company/cac:PostalAddress/cbc:CityName", namespaces),
                "postal_code": extract_text(root, ".//efac:Organization/efac:Company/cac:PostalAddress/cbc:PostalZone", namespaces),
                "country": extract_text(root, ".//efac:Organization/efac:Company/cac:PostalAddress/cac:Country/cbc:IdentificationCode", namespaces)
            },
            "website": extract_text(root, ".//cbc:BuyerProfileURI", namespaces),
            "company_id": extract_text(root, ".//efac:Organization/efac:Company/cac:PartyLegalEntity/cbc:CompanyID", namespaces),
            "phone": extract_text(root, ".//efac:Organization/efac:Company/cac:Contact/cbc:Telephone", namespaces)
        },
        "procedure": {
            "title": extract_text(root, ".//cac:ProcurementProject/cbc:Name", namespaces),
            "description": extract_text(root, ".//cac:ProcurementProject/cbc:Description", namespaces),
            "identifier": extract_text(root, ".//cbc:ID[@schemeName='notice-id']", namespaces),
            "type": extract_text(root, ".//cbc:ProcedureCode", namespaces),
            "accelerated": extract_text(root, ".//cbc:ProcessReasonCode[@listName='accelerated-procedure']", namespaces),
            "deadline_date": extract_text(root, ".//cac:TenderSubmissionDeadlinePeriod/cbc:EndDate", namespaces),
            "deadline_time": extract_text(root, ".//cac:TenderSubmissionDeadlinePeriod/cbc:EndTime", namespaces)
        },
        "purpose": {
            "main_nature": extract_text(root, ".//cbc:ProcurementTypeCode", namespaces),
            "main_classification": extract_text(root, ".//cac:MainCommodityClassification/cbc:ItemClassificationCode", namespaces),
            "additional_classifications": [code.text for code in root.findall(".//cac:AdditionalCommodityClassification/cbc:ItemClassificationCode", namespaces)],
            "place_of_performance": extract_text(root, ".//cac:RealizedLocation/cac:Address/cbc:Region", namespaces) or
                                    extract_text(root, ".//cac:RealizedLocation/cac:Address/cac:Country/cbc:IdentificationCode", namespaces),
        },
        "value": {
            "estimated_value": extract_text(root, ".//cbc:EstimatedOverallContractAmount", namespaces),
            "currency": extract_text(root, ".//cbc:EstimatedOverallContractAmount", namespaces, attribute='currencyID'),
            "maximum_value": extract_text(root, ".//efbc:FrameworkMaximumAmount", namespaces)
        },
        "general_information": {
            "terms_of_submission": extract_text(root, ".//cbc:SubmissionMethodCode", namespaces),
            "variant_submissions": extract_text(root, ".//cbc:VariantConstraintCode", namespaces),
            "electronic_invoicing": extract_text(root, ".//cbc:ExecutionRequirementCode[@listName='einvoicing']", namespaces),
            "electronic_ordering": extract_text(root, ".//cbc:ElectronicOrderUsageIndicator", namespaces),
            "electronic_payment": extract_text(root, ".//cbc:ElectronicPaymentUsageIndicator", namespaces)
        },
        "tendering_process": {
            "procedure_code": extract_text(root, ".//cbc:ProcedureCode", namespaces),
            "submission_method": extract_text(root, ".//cbc:SubmissionMethodCode", namespaces),
            "government_agreement_constraint": extract_text(root, ".//cbc:GovernmentAgreementConstraintIndicator", namespaces),
            "open_tender_date": extract_text(root, ".//cac:OpenTenderEvent/cbc:OccurrenceDate", namespaces),
            "open_tender_time": extract_text(root, ".//cac:OpenTenderEvent/cbc:OccurrenceTime", namespaces),
            "open_tender_location": extract_text(root, ".//cac:OpenTenderEvent/cac:OccurenceLocation/cbc:Description", namespaces)
        },
        "tendering_terms": {
            "variant_constraint": extract_text(root, ".//cbc:VariantConstraintCode", namespaces),
            "funding_program": extract_text(root, ".//cbc:FundingProgramCode", namespaces),
            "recurring_procurement": extract_text(root, ".//cbc:RecurringProcurementIndicator", namespaces),
            "multiple_tenders": extract_text(root, ".//cbc:MultipleTendersCode", namespaces),
            "esignature_submission": extract_text(root, ".//cbc:ExecutionRequirementCode[@listName='esignature-submission']", namespaces),
            "ecatalog_submission": extract_text(root, ".//cbc:ExecutionRequirementCode[@listName='ecatalog-submission']", namespaces),
            "tender_validity_period": extract_text(root, ".//cac:TenderValidityPeriod/cbc:DurationMeasure", namespaces),
            "tender_validity_period_unit": extract_text(root, ".//cac:TenderValidityPeriod/cbc:DurationMeasure", namespaces, attribute='unitCode'),
            "security_clearance": extract_text(root, ".//cac:SecurityClearanceTerm/cbc:Code", namespaces)
        },
        "lots": [],
        "useful_links": [],
        "pdf_link": f"https://ted.europa.eu/en/notice/{notice_id}/pdf"
    }

    # Extract useful links
    for attachment in root.findall(".//cac:CallForTendersDocumentReference/cac:Attachment/cac:ExternalReference", namespaces):
        uri = extract_text(attachment, "cbc:URI", namespaces)
        if uri:
            contract_info["useful_links"].append(uri)

    return contract_info

def extract_lot_info(lot, namespaces):
    """
    Extracts lot information from a <ProcurementProjectLot> XML element.

    Args:
        lot (xml.etree.ElementTree.Element): The <ProcurementProjectLot> element.
        namespaces (dict): Dictionary of XML namespaces.

    Returns:
        dict: A dictionary containing the extracted lot information.
    """
    lot_info = {
        "lot": extract_text(lot, "cbc:ID", namespaces),
        "title": extract_text(lot, ".//cac:ProcurementProject/cbc:Name", namespaces),
        "description": extract_text(lot, ".//cac:ProcurementProject/cbc:Description", namespaces),
        "main_nature": extract_text(lot, ".//cac:ProcurementProject/cbc:ProcurementTypeCode", namespaces),
        "main_classification": extract_text(lot, ".//cac:MainCommodityClassification/cbc:ItemClassificationCode", namespaces),
        "additional_classifications": [code.text for code in lot.findall(".//cac:AdditionalCommodityClassification/cbc:ItemClassificationCode", namespaces)],
        "place_of_performance": extract_text(lot, ".//cac:RealizedLocation/cac:Address/cbc:Region", namespaces) or
                                    extract_text(lot, ".//cac:RealizedLocation/cac:Address/cac:Country/cbc:IdentificationCode", namespaces),
        "country": extract_text(lot, ".//cac:RealizedLocation/cac:Address/cac:Country/cbc:IdentificationCode", namespaces),
        "value": {
            "estimated_value": extract_text(lot, ".//cbc:EstimatedOverallContractAmount", namespaces),
            "currency": extract_text(lot, ".//cbc:EstimatedOverallContractAmount", namespaces, attribute='currencyID'),
            "maximum_value": extract_text(lot, ".//efbc:FrameworkMaximumAmount", namespaces)
        },
        "general_information": {
            "reserved_participation": extract_text(lot, ".//cbc:TendererRequirementTypeCode[@listName='reserved-procurement']", namespaces),
            "selection_criteria": extract_text(lot, ".//cbc:CriterionTypeCode[@listName='selection-criterion']", namespaces),
            "variant_submissions": extract_text(lot, ".//cbc:VariantConstraintCode", namespaces),
            "electronic_invoicing": extract_text(lot, ".//cbc:ExecutionRequirementCode[@listName='einvoicing']", namespaces),
            "electronic_ordering": extract_text(lot, ".//cbc:ElectronicOrderUsageIndicator", namespaces),
            "electronic_payment": extract_text(lot, ".//cbc:ElectronicPaymentUsageIndicator", namespaces)
        },
        "specific_information": {
            "procedure_relaunch": extract_text(lot, ".//efbc:ProcedureRelaunchIndicator", namespaces),
            "framework_agreement": extract_text(lot, ".//cbc:ContractingSystemTypeCode[@listName='framework-agreement']", namespaces),
            "dps_usage": extract_text(lot, ".//cbc:ContractingSystemTypeCode[@listName='dps-usage']", namespaces),
            "reserved_execution": extract_text(lot, ".//cbc:ExecutionRequirementCode[@listName='reserved-execution']", namespaces),
            "second_stage_indicator": extract_text(lot, ".//efbc:SecondStageIndicator", namespaces)
        }
    }
    return lot_info

def process_contract_notice(file_path):
    """
    Processes a <ContractNotice> XML file and extracts contract information.

    Args:
        file_path (Path): Path to the XML file.

    Returns:
        dict or None: Extracted contract information or None if processing fails.
    """
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        # Extract namespaces
        namespaces = {k.split(':')[1]: v for k, v in root.attrib.items() if k.startswith('xmlns:')}
        # Add default namespaces used in the extraction functions
        namespaces.update({
            'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
            'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
            'efbc': 'http://data.europa.eu/p27/eforms-ubl-extension-basic-components/1',
            'efac': 'http://data.europa.eu/p27/eforms-ubl-extension-aggregate-components/1'
        })

        # Extract notice publication ID from filename
        filename = Path(file_path).name
        notice_id_match = re.search(r'(\d+)-(\d+)', filename)
        notice_id = f"{notice_id_match.group(1)}-{notice_id_match.group(2)}" if notice_id_match else ""

        contract_info = extract_contract_info(root, notice_id, namespaces)

        for lot in root.findall(".//cac:ProcurementProjectLot", namespaces):
            lot_info = extract_lot_info(lot, namespaces)
            contract_info["lots"].append(lot_info)

        return contract_info

    except ET.ParseError as e:
        logger.error(f"Error parsing XML file {file_path}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error processing file {file_path}: {str(e)}")
        logger.debug(traceback.format_exc())
    return None

##############################
# Processing for <TED_EXPORT>
##############################

def parse_type2_xml_to_json(xml_content, file_name):
    """
    Parses a <TED_EXPORT> XML content and converts it into a JSON-compatible dictionary.

    Args:
        xml_content (str): The XML content as a string.
        file_name (str): The name of the XML file.

    Returns:
        dict: A dictionary containing the extracted TED_EXPORT information.
    """
    # Define all relevant namespaces
    namespaces = {
        'ns': 'http://publications.europa.eu/resource/schema/ted/R2.0.9/publication',
        'n2021': 'http://publications.europa.eu/resource/schema/ted/2021/nuts',
        'xlink': 'http://www.w3.org/1999/xlink',
        'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
    }

    root = ET.fromstring(xml_content)

    # Helper function to find elements or attributes
    def find_element(path, is_attribute=False, attribute_name=None, default="", current_root=root):
        try:
            element = current_root.find(path, namespaces)
            if element is not None:
                if is_attribute and attribute_name:
                    return element.get(attribute_name, default)
                else:
                    return element.text.strip() if element.text else default
            return default
        except Exception:
            return default

    # Extract notice_publication_id from file name (e.g., "199167" from "199167-2021.xml")
    notice_publication_id = os.path.splitext(file_name)[0].split('-')[0]

    # Construct JSON
    result = {
        "notice_publication_id": notice_publication_id,
        "buyer": {
            "official_name": find_element(".//ns:CONTRACTING_BODY/ns:ADDRESS_CONTRACTING_BODY/ns:OFFICIALNAME"),
            "email": find_element(".//ns:CONTRACTING_BODY/ns:ADDRESS_CONTRACTING_BODY/ns:E_MAIL"),
            "legal_type": "body-pl-" + find_element(".//ns:CONTRACTING_BODY/ns:CA_TYPE", is_attribute=True, attribute_name="VALUE").lower(),
            "activity": find_element(".//ns:CONTRACTING_BODY/ns:CA_ACTIVITY", is_attribute=True, attribute_name="VALUE").lower(),
            "address": {
                "street": find_element(".//ns:CONTRACTING_BODY/ns:ADDRESS_CONTRACTING_BODY/ns:ADDRESS"),
                "city": find_element(".//ns:CONTRACTING_BODY/ns:ADDRESS_CONTRACTING_BODY/ns:TOWN"),
                "postal_code": find_element(".//ns:CONTRACTING_BODY/ns:ADDRESS_CONTRACTING_BODY/ns:POSTAL_CODE"),
                "country": find_element(".//ns:CONTRACTING_BODY/ns:ADDRESS_CONTRACTING_BODY/ns:COUNTRY", is_attribute=True, attribute_name="VALUE")
            },
            "website": find_element(".//ns:CONTRACTING_BODY/ns:ADDRESS_CONTRACTING_BODY/ns:URL_GENERAL")
        },
        "procedure": {
            "title": find_element(".//ns:OBJECT_CONTRACT/ns:TITLE/ns:P"),
            "description": find_element(".//ns:OBJECT_CONTRACT/ns:SHORT_DESCR/ns:P"),
            "identifier": find_element(".//ns:FORM_SECTION/ns:NOTICE_UUID"),
            "type": "restricted" if find_element(".//ns:PROCEDURE/ns:PT_RESTRICTED") else "open",
            "accelerated": "false",
            "deadline_date": find_element(".//ns:PROCEDURE/ns:DATE_RECEIPT_TENDERS"),
            "deadline_time": find_element(".//ns:PROCEDURE/ns:TIME_RECEIPT_TENDERS")
        },
        "purpose": {
            "main_nature": find_element(".//ns:OBJECT_CONTRACT/ns:TYPE_CONTRACT", is_attribute=True, attribute_name="CTYPE").lower(),
            "main_classification": find_element(".//ns:OBJECT_CONTRACT/ns:CPV_MAIN/ns:CPV_CODE", is_attribute=True, attribute_name="CODE"),
            "additional_classifications": [
                code.get('CODE', '') 
                for code in root.findall(".//ns:OBJECT_CONTRACT/ns:CPV_ADDITIONAL/ns:CPV_CODE", namespaces)
            ],
            "place_of_performance": find_element(".//ns:OBJECT_CONTRACT/ns:OBJECT_DESCR/ns:n2021:PERFORMANCE_NUTS", is_attribute=True, attribute_name="CODE")
        },
        "value": {
            "estimated_value": find_element(".//ns:OBJECT_CONTRACT/ns:VAL_ESTIMATED_TOTAL"),
            "currency": find_element(".//ns:OBJECT_CONTRACT/ns:VAL_ESTIMATED_TOTAL", is_attribute=True, attribute_name="CURRENCY"),
            "maximum_value": find_element(".//ns:OBJECT_CONTRACT/ns:VAL_OBJECT")  # Adjust if needed
        },
        "lots": [],  # Initialize as empty list; will be populated below
        "useful_links": [],
        "pdf_link": f"https://ted.europa.eu/en/notice/{notice_publication_id}/pdf"
    }

    # Extract useful links
    # Iterate through different link types as per your XML structure
    link_tags = [
        "XML_SCHEMA_DEFINITION_LINK",
        "OFFICIAL_FORMS_LINK",
        "FORMS_LABELS_LINK",
        "ORIGINAL_CPV_LINK",
        "ORIGINAL_NUTS_LINK"
    ]
    for link_tag in link_tags:
        for attachment in root.findall(f".//ns:LINKS_SECTION/ns:{link_tag}", namespaces):
            uri = find_element(f".//ns:{link_tag}", current_root=attachment)
            if uri:
                result["useful_links"].append(uri)

    # Process all lots
    for lot in root.findall(".//ns:OBJECT_CONTRACT/ns:OBJECT_DESCR", namespaces):
        lot_number = find_element(".//ns:LOT_NO", current_root=lot)
        lot_title = find_element(".//ns:TITLE/ns:P", current_root=lot)
        lot_description = find_element(".//ns:SHORT_DESCR/ns:P", current_root=lot)
        lot_main_nature = find_element(".//ns:TYPE_CONTRACT", is_attribute=True, attribute_name="CTYPE", current_root=lot).lower()
        lot_main_classification = find_element(".//ns:CPV_ADDITIONAL/ns:CPV_CODE", is_attribute=True, attribute_name="CODE", current_root=lot)
        # Extract all additional classifications for the lot
        additional_classifications = [
            code.get('CODE', '') 
            for code in lot.findall(".//ns:CPV_ADDITIONAL/ns:CPV_CODE", namespaces)
        ]
        # Extract place_of_performance from n2021:NUTS
        place_of_performance = find_element(".//n2021:NUTS", is_attribute=True, attribute_name="CODE", current_root=lot)

        # Extract value information
        estimated_value = find_element(".//ns:VAL_OBJECT", current_root=lot)
        currency = find_element(".//ns:VAL_OBJECT", is_attribute=True, attribute_name="CURRENCY", current_root=lot)
        maximum_value = find_element(".//ns:VAL_OBJECT", current_root=lot)  # Adjust if needed

        # Format lot number as LOT-XXXX
        if lot_number.isdigit():
            formatted_lot_number = f"LOT-{int(lot_number):04d}"
        else:
            formatted_lot_number = lot_number

        lot_info = {
            "lot": formatted_lot_number,
            "title": lot_title,
            "description": lot_description,
            "main_nature": lot_main_nature,
            "main_classification": lot_main_classification,
            "additional_classifications": additional_classifications,
            "place_of_performance": place_of_performance,
            "value": {
                "estimated_value": estimated_value,
                "currency": currency,
                "maximum_value": maximum_value
            }
        }

        result["lots"].append(lot_info)

    return result

def process_ted_export(file_path, output_file):
    """
    Processes a <TED_EXPORT> XML file and writes the extracted information to a JSON file.

    Args:
        file_path (Path): Path to the XML file.
        output_file (Path): Path where the JSON file will be saved.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            xml_content = file.read()
        
        filename = Path(file_path).name
        json_output = parse_type2_xml_to_json(xml_content, filename)
        
        # Ensure the output directory exists
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        
        # Write JSON to file
        with open(output_file, 'w', encoding='utf-8') as out_file:
            json.dump(json_output, out_file, ensure_ascii=False, indent=2)
        
        logger.info(f"Processed TED_EXPORT file. Output saved to {output_file}")

    except Exception as e:
        logger.error(f"Failed to process TED_EXPORT file '{file_path}'. Error: {e}")
        logger.debug(traceback.format_exc())

##############################
# Dispatcher and File Processing
##############################

def process_xml_file(file_path, output_dir):
    """
    Determines the type of XML file based on its root tag and processes it accordingly.

    Args:
        file_path (Path): Path to the XML file.
        output_dir (Path): Directory where the JSON file will be saved.
    """
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        root_tag = get_localname(root.tag)
        logger.info(f"Processing file: {file_path.name} with root tag: <{root_tag}>")

        if root_tag == "ContractNotice":
            contract_info = process_contract_notice(file_path)
            if contract_info:
                output_file = output_dir / f"{file_path.stem}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(contract_info, f, ensure_ascii=False, indent=2)
                logger.info(f"Processed ContractNotice file. Output saved to {output_file}")
            else:
                logger.warning(f"No contract information extracted from file: {file_path}")
        elif root_tag == "TED_EXPORT":
            output_file = output_dir / f"{file_path.stem}.json"
            process_ted_export(file_path, output_file)
        else:
            logger.warning(f"Unknown root tag <{root_tag}> in file: {file_path}. Skipping.")
    except ET.ParseError as e:
        logger.error(f"Error parsing XML file {file_path}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error processing file {file_path}: {str(e)}")
        logger.debug(traceback.format_exc())

##############################
# Main Function
##############################

def main():
    """
    Main function to parse command-line arguments and process XML files.
    """
    try:
        # Set up argument parser
        parser = argparse.ArgumentParser(description="Process XML files and output JSON files based on their structure.")
        parser.add_argument("input_dir", type=Path, help="Path to the input directory containing XML files")
        parser.add_argument("output_dir", type=Path, help="Path to the output directory for JSON files")
        args = parser.parse_args()

        input_dir = args.input_dir
        output_dir = args.output_dir

        if not input_dir.exists() or not input_dir.is_dir():
            logger.error(f"The specified input directory '{input_dir}' does not exist or is not a directory.")
            sys.exit(1)

        # Ensure the output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        # Iterate over all XML files in the input directory
        xml_files = list(input_dir.glob("*.xml"))

        if not xml_files:
            logger.warning(f"No XML files found in the directory '{input_dir}'.")
            sys.exit(0)

        total_files = len(xml_files)
        processed_files = 0
        start_time = time.time()

        for xml_file in xml_files:
            try:
                process_xml_file(xml_file, output_dir)
                processed_files += 1
                if processed_files % 10 == 0:  # Log progress every 10 files
                    elapsed_time = time.time() - start_time
                    files_per_second = processed_files / elapsed_time if elapsed_time > 0 else 0
                    logger.info(f"Processed {processed_files}/{total_files} files. "
                                f"Speed: {files_per_second:.2f} files/second")
            except Exception as e:
                logger.error(f"Error processing file {xml_file}: {str(e)}")

        logger.info(f"Processing complete. Processed {processed_files}/{total_files} files.")

    except Exception as e:
        logger.error(f"Unexpected error in main function: {e}")
        logger.error(traceback.format_exc())  # Log the full traceback
        sys.exit(1)

if __name__ == "__main__":
    main()
