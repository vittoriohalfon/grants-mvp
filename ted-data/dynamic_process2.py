import os
import json
import glob
import xml.etree.ElementTree as ET
import logging
from pathlib import Path
import argparse
import re
import sys
import traceback

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define namespaces for XML1 and XML2
NAMESPACES_XML1 = {
    'ubl': 'urn:oasis:names:specification:ubl:schema:xsd:ContractNotice-2',
    'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
    'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
    'efac': 'http://data.europa.eu/p27/eforms-ubl-extension-aggregate-components/1',
    'efbc': 'http://data.europa.eu/p27/eforms-ubl-extension-basic-components/1',
    'efext': 'http://data.europa.eu/p27/eforms-ubl-extensions/1',
    'ext': 'urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2',
    'xsd': 'http://www.w3.org/2001/XMLSchema',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
}

NAMESPACES_XML2 = {
    'ted': 'http://publications.europa.eu/resource/schema/ted/R2.0.9/publication',
    'xlink': 'http://www.w3.org/1999/xlink',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
    'n2016': 'http://publications.europa.eu/resource/schema/ted/2016/nuts'
}

def extract_text(element, xpath, namespaces, default=""):
    """
    Utility function to extract text from an XML element using XPath.
    Handles missing elements gracefully by returning a default value.
    """
    try:
        result = element.find(xpath, namespaces)
        if result is not None:
            if result.text:
                return result.text.strip()
            elif result.attrib:
                # If the element has attributes but no text, return the first attribute value
                return next(iter(result.attrib.values())).strip()
            else:
                # If there's no text and no attributes, check for child elements
                child_texts = [child.text.strip() for child in result if child.text]
                if child_texts:
                    return ", ".join(child_texts)
        logging.warning(f"Unable to find text for XPath: {xpath}")
        return default
    except AttributeError:
        logging.warning(f"Attribute error for XPath: {xpath}")
        return default
    except Exception as e:
        logging.warning(f"Error extracting text for XPath {xpath}: {e}")
        return default

### ======================
### Parsing Mechanism for XML1
### ======================

def extract_contract_info_xml1(root, notice_id):
    """
    Parses XML1 (ContractNotice) and maps it to the JSON structure.
    """
    contract_info = {
        "notice_publication_id": notice_id,
        "buyer": {
            "official_name": extract_text(root, ".//efac:Organization/efac:Company/cac:PartyName/cbc:Name", NAMESPACES_XML1),
            "email": extract_text(root, ".//efac:Organization/efac:Company/cac:Contact/cbc:ElectronicMail", NAMESPACES_XML1),
            "legal_type": extract_text(root, ".//cac:ContractingPartyType/cbc:PartyTypeCode", NAMESPACES_XML1),
            "activity": extract_text(root, ".//cac:ContractingActivity/cbc:ActivityTypeCode", NAMESPACES_XML1),
            "address": {
                "street": extract_text(root, ".//efac:Organization/efac:Company/cac:PostalAddress/cbc:StreetName", NAMESPACES_XML1),
                "city": extract_text(root, ".//efac:Organization/efac:Company/cac:PostalAddress/cbc:CityName", NAMESPACES_XML1),
                "postal_code": extract_text(root, ".//efac:Organization/efac:Company/cac:PostalAddress/cbc:PostalZone", NAMESPACES_XML1),
                "country": extract_text(root, ".//efac:Organization/efac:Company/cac:PostalAddress/cac:Country/cbc:IdentificationCode", NAMESPACES_XML1)
            },
            "website": extract_text(root, ".//cac:ContractingParty/cbc:BuyerProfileURI", NAMESPACES_XML1),
            "company_id": extract_text(root, ".//efac:Organization/efac:Company/cac:PartyLegalEntity/cbc:CompanyID", NAMESPACES_XML1),
            "phone": extract_text(root, ".//efac:Organization/efac:Company/cac:Contact/cbc:Telephone", NAMESPACES_XML1)
        },
        "procedure": {
            "title": extract_text(root, ".//cac:ProcurementProject/cbc:Name", NAMESPACES_XML1),
            "description": extract_text(root, ".//cac:ProcurementProject/cbc:Description", NAMESPACES_XML1),
            "identifier": extract_text(root, ".//cbc:ID[@schemeName='notice-id']", NAMESPACES_XML1),
            "type": extract_text(root, ".//cac:TenderingProcess/cbc:ProcedureCode", NAMESPACES_XML1),
            "accelerated": extract_text(root, ".//cac:TenderingProcess/cac:ProcessJustification/cbc:ProcessReasonCode[@listName='accelerated-procedure']", NAMESPACES_XML1),
            "deadline_date": extract_text(root, ".//cac:TenderSubmissionDeadlinePeriod/cbc:EndDate", NAMESPACES_XML1),
            "deadline_time": extract_text(root, ".//cac:TenderSubmissionDeadlinePeriod/cbc:EndTime", NAMESPACES_XML1)
        },
        "purpose": {
            "main_nature": extract_text(root, ".//cac:ProcurementProject/cbc:ProcurementTypeCode", NAMESPACES_XML1),
            "main_classification": extract_text(root, ".//cac:ProcurementProject/cac:MainCommodityClassification/cbc:ItemClassificationCode", NAMESPACES_XML1),
            "additional_classifications": [code.text for code in root.findall(".//cac:ProcurementProject/cac:AdditionalCommodityClassification/cbc:ItemClassificationCode", NAMESPACES_XML1)],
            "place_of_performance": extract_text(root, ".//cac:ProcurementProject/cac:RealizedLocation/cac:Address/cbc:Region", NAMESPACES_XML1) or
                                      extract_text(root, ".//cac:ProcurementProject/cac:RealizedLocation/cac:Address/cac:Country/cbc:IdentificationCode", NAMESPACES_XML1)
        },
        "value": {
            "estimated_value": extract_text(root, ".//cac:ProcurementProject/cac:RequestedTenderTotal/cbc:EstimatedOverallContractAmount", NAMESPACES_XML1),
            "currency": extract_text(root, ".//cac:ProcurementProject/cac:RequestedTenderTotal/cbc:EstimatedOverallContractAmount/@currencyID", NAMESPACES_XML1),
            "maximum_value": extract_text(root, ".//cac:ProcurementProject/cac:RequestedTenderTotal/ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent/efext:EformsExtension/efbc:FrameworkMaximumAmount", NAMESPACES_XML1)
        },
        "general_information": {
            "terms_of_submission": extract_text(root, ".//cac:TenderingProcess/cac:TenderSubmissionDeadlinePeriod/cbc:EndDate", NAMESPACES_XML1),  # Adjust XPath as needed
            "variant_submissions": extract_text(root, ".//cac:TenderingTerms/cbc:FundingProgramCode", NAMESPACES_XML1),
            "electronic_invoicing": extract_text(root, ".//cac:TenderingTerms/cac:ContractExecutionRequirement/cbc:ExecutionRequirementCode[@listName='einvoicing']", NAMESPACES_XML1),
            "electronic_ordering": extract_text(root, ".//cac:TenderingTerms/cac:PostAwardProcess/cbc:ElectronicOrderUsageIndicator", NAMESPACES_XML1),
            "electronic_payment": extract_text(root, ".//cac:TenderingTerms/cac:PostAwardProcess/cbc:ElectronicPaymentUsageIndicator", NAMESPACES_XML1)
        },
        "tendering_process": {
            "procedure_code": extract_text(root, ".//cac:TenderingProcess/cbc:ProcedureCode", NAMESPACES_XML1),
            "submission_method": extract_text(root, ".//cac:TenderingTerms/cac:TendererQualificationRequest/cac:SpecificTendererRequirement/cbc:TendererRequirementTypeCode", NAMESPACES_XML1),
            "government_agreement_constraint": extract_text(root, ".//cac:TenderingProcess/cac:ProcessJustification/cbc:ProcessReasonCode[@listName='accelerated-procedure']", NAMESPACES_XML1),
            "open_tender_date": extract_text(root, ".//cac:TenderSubmissionDeadlinePeriod/cbc:EndDate", NAMESPACES_XML1),
            "open_tender_time": extract_text(root, ".//cac:TenderSubmissionDeadlinePeriod/cbc:EndTime", NAMESPACES_XML1),
            "open_tender_location": extract_text(root, ".//cac:TenderRecipientParty/cbc:EndpointID", NAMESPACES_XML1)
        },
        "tendering_terms": {
            "variant_constraint": extract_text(root, ".//cac:TenderingTerms/cac:TendererQualificationRequest/cac:SpecificTendererRequirement/cbc:TendererRequirementTypeCode", NAMESPACES_XML1),
            "funding_program": extract_text(root, ".//cac:TenderingTerms/cbc:FundingProgramCode", NAMESPACES_XML1),
            "recurring_procurement": extract_text(root, ".//cac:TenderingTerms/cbc:RecurringProcurementIndicator", NAMESPACES_XML1),
            "multiple_tenders": extract_text(root, ".//cac:TenderingTerms/cbc:MultipleTendersCode", NAMESPACES_XML1),
            "esignature_submission": extract_text(root, ".//cac:TenderingTerms/cac:ContractExecutionRequirement/cbc:ExecutionRequirementCode[@listName='esignature-submission']", NAMESPACES_XML1),
            "ecatalog_submission": extract_text(root, ".//cac:TenderingTerms/cac:ContractExecutionRequirement/cbc:ExecutionRequirementCode[@listName='ecatalog-submission']", NAMESPACES_XML1),
            "tender_validity_period": extract_text(root, ".//cac:TenderingTerms/cac:TenderValidityPeriod/cbc:DurationMeasure", NAMESPACES_XML1),
            "tender_validity_period_unit": extract_text(root, ".//cac:TenderingTerms/cac:TenderValidityPeriod/cbc:DurationMeasure/@unitCode", NAMESPACES_XML1),
            "security_clearance": extract_text(root, ".//cac:TenderingTerms/cac:SecurityClearanceTerm/cbc:Code", NAMESPACES_XML1)
        },
        "lots": [],
        "useful_links": [],
        "pdf_link": f"https://ted.europa.eu/en/notice/{notice_id}/pdf"
    }

    # Extract useful links
    for attachment in root.findall(".//cac:CallForTendersDocumentReference/cac:Attachment/cac:ExternalReference", NAMESPACES_XML1):
        uri = extract_text(attachment, "cbc:URI", NAMESPACES_XML1)
        if uri:
            contract_info["useful_links"].append(uri)

    return contract_info

def extract_lot_info_xml1(lot):
    """
    Extracts lot information from XML1 (ContractNotice).
    """
    lot_info = {
        "lot": extract_text(lot, "cbc:ID", NAMESPACES_XML1),
        "title": extract_text(lot, ".//cac:ProcurementProject/cbc:Name", NAMESPACES_XML1),
        "description": extract_text(lot, ".//cac:ProcurementProject/cbc:Description", NAMESPACES_XML1),
        "main_nature": extract_text(lot, ".//cac:ProcurementProject/cbc:ProcurementTypeCode", NAMESPACES_XML1),
        "main_classification": extract_text(lot, ".//cac:ProcurementProject/cac:MainCommodityClassification/cbc:ItemClassificationCode", NAMESPACES_XML1),
        "additional_classifications": [code.text for code in lot.findall(".//cac:ProcurementProject/cac:AdditionalCommodityClassification/cbc:ItemClassificationCode", NAMESPACES_XML1)],
        "place_of_performance": extract_text(lot, ".//cac:ProcurementProject/cac:RealizedLocation/cac:Address/cbc:Region", NAMESPACES_XML1) or
                                  extract_text(lot, ".//cac:ProcurementProject/cac:RealizedLocation/cac:Address/cac:Country/cbc:IdentificationCode", NAMESPACES_XML1),
        "country": extract_text(lot, ".//cac:ProcurementProject/cac:RealizedLocation/cac:Address/cac:Country/cbc:IdentificationCode", NAMESPACES_XML1),
        "value": {
            "estimated_value": extract_text(lot, ".//cac:ProcurementProject/cac:RequestedTenderTotal/cbc:EstimatedOverallContractAmount", NAMESPACES_XML1),
            "currency": extract_text(lot, ".//cac:ProcurementProject/cac:RequestedTenderTotal/cbc:EstimatedOverallContractAmount/@currencyID", NAMESPACES_XML1),
            "maximum_value": extract_text(lot, ".//cac:ProcurementProject/cac:RequestedTenderTotal/ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent/efext:EformsExtension/efbc:FrameworkMaximumAmount", NAMESPACES_XML1)
        },
        "general_information": {
            "reserved_participation": extract_text(lot, ".//cac:TenderingTerms/cac:TendererQualificationRequest/cac:SpecificTendererRequirement/cbc:TendererRequirementTypeCode[@listName='reserved-procurement']", NAMESPACES_XML1),
            "selection_criteria": extract_text(lot, ".//cac:TenderingTerms/cac:SelectionCriteria/cbc:CriterionTypeCode[@listName='selection-criterion']", NAMESPACES_XML1),
            "variant_submissions": extract_text(lot, ".//cac:TenderingTerms/cbc:VariantConstraintCode", NAMESPACES_XML1),
            "electronic_invoicing": extract_text(lot, ".//cac:TenderingTerms/cac:ContractExecutionRequirement/cbc:ExecutionRequirementCode[@listName='einvoicing']", NAMESPACES_XML1),
            "electronic_ordering": extract_text(lot, ".//cac:TenderingTerms/cac:PostAwardProcess/cbc:ElectronicOrderUsageIndicator", NAMESPACES_XML1),
            "electronic_payment": extract_text(lot, ".//cac:TenderingTerms/cac:PostAwardProcess/cbc:ElectronicPaymentUsageIndicator", NAMESPACES_XML1)
        },
        "specific_information": {
            "procedure_relaunch": extract_text(lot, ".//cac:TenderingTerms/cac:ContractExecutionRequirement/cbc:ExecutionRequirementCode[@listName='reserved-execution']", NAMESPACES_XML1),
            "framework_agreement": extract_text(lot, ".//cac:TenderingTerms/cac:ContractExecutionRequirement/cbc:ContractingSystemTypeCode[@listName='framework-agreement']", NAMESPACES_XML1),
            "dps_usage": extract_text(lot, ".//cac:TenderingTerms/cac:ContractExecutionRequirement/cbc:ContractingSystemTypeCode[@listName='dps-usage']", NAMESPACES_XML1),
            "reserved_execution": extract_text(lot, ".//cac:TenderingTerms/cac:ContractExecutionRequirement/cbc:ExecutionRequirementCode[@listName='reserved-execution']", NAMESPACES_XML1),
            "second_stage_indicator": extract_text(lot, ".//cac:TenderingTerms/cac:ContractExecutionRequirement/cbc:SecondStageIndicator", NAMESPACES_XML1)
        }
    }
    return lot_info

### ======================
### Parsing Mechanism for XML2
### ======================

def extract_contract_info_xml2(root):
    """
    Parses XML2 (TED_EXPORT) and maps it to the JSON structure.
    """
    contract_info = {
        "notice_publication_id": extract_text(root, ".//REF_OJS/COLL_OJ", NAMESPACES_XML2),
        "buyer": {
            "official_name": extract_text(root, ".//FORM_SECTION/F02_2014/CONTRACTING_BODY/ADDRESS_CONTRACTING_BODY/OFFICIALNAME", NAMESPACES_XML2),
            "email": extract_text(root, ".//FORM_SECTION/F02_2014/CONTRACTING_BODY/ADDRESS_CONTRACTING_BODY/E_MAIL", NAMESPACES_XML2),
            "legal_type": extract_text(root, ".//CODED_DATA_SECTION/CODIF_DATA/AA_AUTHORITY_TYPE", NAMESPACES_XML2),
            "activity": extract_text(root, ".//CODED_DATA_SECTION/CODIF_DATA/AA_ACTIVITY", NAMESPACES_XML2),
            "address": {
                "street": extract_text(root, ".//FORM_SECTION/F02_2014/CONTRACTING_BODY/ADDRESS_CONTRACTING_BODY/ADDRESS", NAMESPACES_XML2),
                "city": extract_text(root, ".//FORM_SECTION/F02_2014/CONTRACTING_BODY/ADDRESS_CONTRACTING_BODY/TOWN", NAMESPACES_XML2),
                "postal_code": "",  # XML2 does not provide postal code in the sample
                "country": extract_text(root, ".//FORM_SECTION/F02_2014/CONTRACTING_BODY/ADDRESS_CONTRACTING_BODY/COUNTRY/@VALUE", NAMESPACES_XML2)
            },
            "website": extract_text(root, ".//FORM_SECTION/F02_2014/CONTRACTING_BODY/ADDRESS_CONTRACTING_BODY/URL_BUYER", NAMESPACES_XML2),
            "company_id": extract_text(root, ".//FORM_SECTION/F02_2014/CONTRACTING_BODY/ADDRESS_CONTRACTING_BODY/NATIONALID", NAMESPACES_XML2),
            "phone": extract_text(root, ".//FORM_SECTION/F02_2014/CONTRACTING_BODY/ADDRESS_CONTRACTING_BODY/PHONE", NAMESPACES_XML2)
        },
        "procedure": {
            "title": extract_text(root, ".//FORM_SECTION/F02_2014/OBJECT_CONTRACT/TITLE/P", NAMESPACES_XML2),
            "description": extract_text(root, ".//FORM_SECTION/F02_2014/OBJECT_CONTRACT/SHORT_DESCR/P", NAMESPACES_XML2),
            "identifier": extract_text(root, ".//DOC_ID", NAMESPACES_XML2),
            "type": extract_text(root, ".//CODED_DATA_SECTION/CODIF_DATA/PR_PROC", NAMESPACES_XML2),
            "accelerated": extract_text(root, ".//CODED_DATA_SECTION/CODIF_DATA/RP_REGULATION/@CODE", NAMESPACES_XML2),
            "deadline_date": extract_text(root, ".//PROCEDURE/DATE_RECEIPT_TENDERS", NAMESPACES_XML2),
            "deadline_time": extract_text(root, ".//PROCEDURE/TIME_RECEIPT_TENDERS", NAMESPACES_XML2)
        },
        "purpose": {
            "main_nature": extract_text(root, ".//CODED_DATA_SECTION/CODIF_DATA/NC_CONTRACT_NATURE/@CODE", NAMESPACES_XML2),
            "main_classification": extract_text(root, ".//CODED_DATA_SECTION/CODIF_DATA/CPV_MAIN/CPV_CODE/@CODE", NAMESPACES_XML2),
            "additional_classifications": [code.attrib.get('CODE') for code in root.findall(".//CODED_DATA_SECTION/CODIF_DATA/OBJECT_DESCR/CPV_ADDITIONAL/CPV_CODE", NAMESPACES_XML2)],
            "place_of_performance": extract_text(root, ".//CODED_DATA_SECTION/CODIF_DATA/n2016:PERFORMANCE_NUTS", NAMESPACES_XML2)
        },
        "value": {
            "estimated_value": extract_text(root, ".//CODED_DATA_SECTION/CODIF_DATA/VALUES/VALUE[@TYPE='ESTIMATED_TOTAL']", NAMESPACES_XML2),
            "currency": extract_text(root, ".//CODED_DATA_SECTION/CODIF_DATA/VALUES/VALUE/@CURRENCY", NAMESPACES_XML2),
            "maximum_value": extract_text(root, ".//CODED_DATA_SECTION/CODIF_DATA/VALUES/VALUE[@TYPE='ESTIMATED_TOTAL']", NAMESPACES_XML2)  # XML2 does not provide maximum value separately
        },
        "general_information": {
            "terms_of_submission": extract_text(root, ".//FORM_SECTION/F02_2014/OBJECT_CONTRACT/VAL_ESTIMATED_TOTAL", NAMESPACES_XML2),  # Adjust XPath as needed
            "variant_submissions": extract_text(root, ".//FORM_SECTION/F02_2014/OBJECT_CONTRACT/NO_ACCEPTED_VARIANTS", NAMESPACES_XML2),
            "electronic_invoicing": extract_text(root, ".//FORM_SECTION/F02_2014/OBJECT_CONTRACT/VAL_OBJECT/@CURRENCY", NAMESPACES_XML2),  # Adjust XPath as needed
            "electronic_ordering": extract_text(root, ".//FORM_SECTION/F02_2014/OBJECT_CONTRACT/DURATION/@TYPE", NAMESPACES_XML2),
            "electronic_payment": extract_text(root, ".//FORM_SECTION/F02_2014/OBJECT_CONTRACT/DURATION/@TYPE", NAMESPACES_XML2)  # Adjust XPath as needed
        },
        "tendering_process": {
            "procedure_code": extract_text(root, ".//CODED_DATA_SECTION/CODIF_DATA/PR_PROC", NAMESPACES_XML2),
            "submission_method": extract_text(root, ".//PROCEDURE/LANGUAGES/LANGUAGE/@VALUE", NAMESPACES_XML2),
            "government_agreement_constraint": extract_text(root, ".//CODED_DATA_SECTION/CODIF_DATA/RP_REGULATION/@CODE", NAMESPACES_XML2),
            "open_tender_date": extract_text(root, ".//PROCEDURE/DATE_OPENING_TENDERS", NAMESPACES_XML2),
            "open_tender_time": extract_text(root, ".//PROCEDURE/TIME_OPENING_TENDERS", NAMESPACES_XML2),
            "open_tender_location": extract_text(root, ".//FORM_SECTION/F02_2014/OBJECT_CONTRACT/URL_PARTICIPATION", NAMESPACES_XML2)
        },
        "tendering_terms": {
            "variant_constraint": extract_text(root, ".//FORM_SECTION/F02_2014/OBJECT_CONTRACT/NO_OPTIONS", NAMESPACES_XML2),
            "funding_program": extract_text(root, ".//FORM_SECTION/F02_2014/OBJECT_CONTRACT/VAL_OBJECT/@CURRENCY", NAMESPACES_XML2),  # Adjust XPath as needed
            "recurring_procurement": extract_text(root, ".//FORM_SECTION/F02_2014/OBJECT_CONTRACT/NO_RENEWAL", NAMESPACES_XML2),
            "multiple_tenders": extract_text(root, ".//FORM_SECTION/F02_2014/OBJECT_CONTRACT/NO_OPTIONS", NAMESPACES_XML2),
            "esignature_submission": extract_text(root, ".//FORM_SECTION/F02_2014/OBJECT_CONTRACT/VAL_OBJECT/@CURRENCY", NAMESPACES_XML2),  # Adjust XPath as needed
            "ecatalog_submission": extract_text(root, ".//FORM_SECTION/F02_2014/OBJECT_CONTRACT/VAL_OBJECT/@CURRENCY", NAMESPACES_XML2),  # Adjust XPath as needed
            "tender_validity_period": extract_text(root, ".//FORM_SECTION/F02_2014/OBJECT_CONTRACT/DURATION", NAMESPACES_XML2),
            "tender_validity_period_unit": extract_text(root, ".//FORM_SECTION/F02_2014/OBJECT_CONTRACT/DURATION/@TYPE", NAMESPACES_XML2),
            "security_clearance": extract_text(root, ".//FORM_SECTION/F02_2014/OBJECT_CONTRACT/VAL_OBJECT/@CURRENCY", NAMESPACES_XML2)  # Adjust XPath as needed
        },
        "lots": [],  # XML2 sample does not include lots; implement if needed
        "useful_links": [
            extract_text(root, ".//FORM_SECTION/F02_2014/OBJECT_CONTRACT/URL_DOCUMENT", NAMESPACES_XML2)
        ],
        "pdf_link": f"https://ted.europa.eu/en/notice/{extract_text(root, './/DOC_ID', NAMESPACES_XML2)}/pdf"
    }

    return contract_info

### ======================
### Identification and Processing
### ======================

def identify_xml_type(root):
    """
    Identifies the type of XML based on the root tag or namespace.
    Returns 'XML1', 'XML2', or 'Unknown'.
    """
    if root.tag.endswith('ContractNotice'):
        return 'XML1'
    elif root.tag.endswith('TED_EXPORT'):
        return 'XML2'
    else:
        return 'Unknown'

def process_xml_file(file_path):
    """
    Processes a single XML file and returns the mapped JSON data.
    """
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        xml_type = identify_xml_type(root)
        logging.info(f"Identified XML type: {xml_type} for file: {file_path}")

        if xml_type == 'XML1':
            # Extract namespaces for XML1
            namespaces = {k.split(':')[1]: v for k, v in root.attrib.items() if k.startswith('xmlns:')}
            namespaces['cac'] = NAMESPACES_XML1['cac']
            namespaces['cbc'] = NAMESPACES_XML1['cbc']
            namespaces['efac'] = NAMESPACES_XML1['efac']
            namespaces['efbc'] = NAMESPACES_XML1['efbc']
            namespaces['efext'] = NAMESPACES_XML1['efext']
            namespaces['ext'] = NAMESPACES_XML1['ext']

            # Extract notice publication ID from filename
            filename = Path(file_path).stem
            notice_id_match = re.search(r'(\d+)-(\d+)', filename)
            notice_id = f"{notice_id_match.group(1)}-{notice_id_match.group(2)}" if notice_id_match else ""

            contract_info = extract_contract_info_xml1(root, notice_id)

            for lot in root.findall(".//cac:ProcurementProjectLot", NAMESPACES_XML1):
                lot_info = extract_lot_info_xml1(lot)
                contract_info["lots"].append(lot_info)

            return contract_info

        elif xml_type == 'XML2':
            # Extract namespaces for XML2
            namespaces = {k.split(':')[1]: v for k, v in root.attrib.items() if k.startswith('xmlns:')}
            namespaces.update(NAMESPACES_XML2)

            contract_info = extract_contract_info_xml2(root)

            # XML2 does not have lot information in the sample; implement if necessary

            return contract_info

        else:
            logging.warning(f"Unknown XML type for file: {file_path}")
            return None

    except ET.ParseError as e:
        logging.error(f"Error parsing XML file {file_path}: {e}")
    except Exception as e:
        logging.error(f"Unexpected error processing file {file_path}: {str(e)}")
        logging.error(traceback.format_exc())
    return None

### ======================
### Main Function
### ======================

def main():
    try:
        # Set up argument parser
        parser = argparse.ArgumentParser(description="Process multiple XML files and output a standardized JSON file.")
        parser.add_argument("input_directory", type=Path, help="Path to the directory containing input XML files")
        parser.add_argument("output_file", type=Path, help="Path to the output JSON file")
        args = parser.parse_args()

        if not args.input_directory.exists() or not args.input_directory.is_dir():
            logging.error(f"The specified input directory '{args.input_directory}' does not exist or is not a directory.")
            sys.exit(1)

        xml_files = glob.glob(os.path.join(args.input_directory, '*.xml'))
        if not xml_files:
            logging.warning(f"No XML files found in directory: {args.input_directory}")
            sys.exit(0)

        all_contracts = []
        for xml_file in xml_files:
            logging.info(f"Processing file: {xml_file}")
            contract_info = process_xml_file(xml_file)
            if contract_info:
                all_contracts.append(contract_info)
            else:
                logging.warning(f"Failed to process file: {xml_file}")

        if all_contracts:
            # Ensure the output directory exists
            args.output_file.parent.mkdir(parents=True, exist_ok=True)

            # Write the compiled JSON data to the output file
            try:
                with open(args.output_file, 'w', encoding='utf-8') as f:
                    json.dump(all_contracts, f, ensure_ascii=False, indent=2)
                logging.info(f"JSON output written to {args.output_file}")
            except IOError as e:
                logging.error(f"Error writing to output file {args.output_file}: {e}")
        else:
            logging.warning("No contracts were processed. No JSON output generated.")

    except Exception as e:
        logging.error(f"Unexpected error in main function: {e}")
        logging.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
