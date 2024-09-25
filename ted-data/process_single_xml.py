import xml.etree.ElementTree as ET
import json
import logging
from pathlib import Path
import argparse
import re
import sys
import traceback

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
            else:
                # If there's no text and no attributes, check for child elements
                child_texts = [child.text.strip() for child in result if child.text]
                if child_texts:
                    return ", ".join(child_texts)
        logging.warning(f"Unable to find text for {xpath}")
        return default
    except AttributeError:
        logging.warning(f"Unable to find {xpath}")
        return default
    except Exception as e:
        logging.warning(f"Error extracting text for {xpath}: {e}")
        return default

def extract_contract_info(root, notice_id):
    contract_info = {
        "notice_publication_id": notice_id,
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
            "website": extract_text(root, ".//cbc:BuyerProfileURI"),
            "company_id": extract_text(root, ".//efac:Organization/efac:Company/cac:PartyLegalEntity/cbc:CompanyID"),
            "phone": extract_text(root, ".//efac:Organization/efac:Company/cac:Contact/cbc:Telephone")
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
            "place_of_performance": extract_text(root, ".//cac:RealizedLocation/cac:Address/cbc:Region") or
                                    extract_text(root, ".//cac:RealizedLocation/cac:Address/cac:Country/cbc:IdentificationCode"),
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
        "tendering_process": {
            "procedure_code": extract_text(root, ".//cbc:ProcedureCode"),
            "submission_method": extract_text(root, ".//cbc:SubmissionMethodCode"),
            "government_agreement_constraint": extract_text(root, ".//cbc:GovernmentAgreementConstraintIndicator"),
            "open_tender_date": extract_text(root, ".//cac:OpenTenderEvent/cbc:OccurrenceDate"),
            "open_tender_time": extract_text(root, ".//cac:OpenTenderEvent/cbc:OccurrenceTime"),
            "open_tender_location": extract_text(root, ".//cac:OpenTenderEvent/cac:OccurenceLocation/cbc:Description")
        },
        "tendering_terms": {
            "variant_constraint": extract_text(root, ".//cbc:VariantConstraintCode"),
            "funding_program": extract_text(root, ".//cbc:FundingProgramCode"),
            "recurring_procurement": extract_text(root, ".//cbc:RecurringProcurementIndicator"),
            "multiple_tenders": extract_text(root, ".//cbc:MultipleTendersCode"),
            "esignature_submission": extract_text(root, ".//cbc:ExecutionRequirementCode[@listName='esignature-submission']"),
            "ecatalog_submission": extract_text(root, ".//cbc:ExecutionRequirementCode[@listName='ecatalog-submission']"),
            "tender_validity_period": extract_text(root, ".//cac:TenderValidityPeriod/cbc:DurationMeasure"),
            "tender_validity_period_unit": extract_text(root, ".//cac:TenderValidityPeriod/cbc:DurationMeasure/@unitCode"),
            "security_clearance": extract_text(root, ".//cac:SecurityClearanceTerm/cbc:Code")
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
        "place_of_performance": extract_text(lot, ".//cac:RealizedLocation/cac:Address/cbc:Region") or
                                extract_text(lot, ".//cac:RealizedLocation/cac:Address/cac:Country/cbc:IdentificationCode"),
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
        },
        "specific_information": {
            "procedure_relaunch": extract_text(lot, ".//efbc:ProcedureRelaunchIndicator"),
            "framework_agreement": extract_text(lot, ".//cbc:ContractingSystemTypeCode[@listName='framework-agreement']"),
            "dps_usage": extract_text(lot, ".//cbc:ContractingSystemTypeCode[@listName='dps-usage']"),
            "reserved_execution": extract_text(lot, ".//cbc:ExecutionRequirementCode[@listName='reserved-execution']"),
            "second_stage_indicator": extract_text(lot, ".//efbc:SecondStageIndicator")
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

        # Extract notice publication ID from filename
        filename = Path(file_path).name
        notice_id_match = re.search(r'(\d+)-(\d+)', filename)
        notice_id = f"{notice_id_match.group(1)}-{notice_id_match.group(2)}" if notice_id_match else ""

        contract_info = extract_contract_info(root, notice_id)

        for lot in root.findall(".//cac:ProcurementProjectLot", namespaces):
            lot_info = extract_lot_info(lot)
            contract_info["lots"].append(lot_info)

        return contract_info

    except ET.ParseError as e:
        logging.error(f"Error parsing XML file {file_path}: {e}")
    except Exception as e:
        logging.error(f"Unexpected error processing file {file_path}: {str(e)}")
    return None

def main():
    try:
        # Set up argument parser
        parser = argparse.ArgumentParser(description="Process a single XML file and output a JSON file.")
        parser.add_argument("input_file", type=Path, help="Path to the input XML file")
        parser.add_argument("output_file", type=Path, help="Path to the output JSON file")
        args = parser.parse_args()

        if not args.input_file.exists():
            logging.error(f"The specified input file '{args.input_file}' does not exist.")
            return

        logging.info(f"Processing file: {args.input_file}")
        contract_info = process_xml_file(args.input_file)

        if contract_info:
            # Ensure the output directory exists
            args.output_file.parent.mkdir(parents=True, exist_ok=True)

            # Write the processed contract to a JSON file
            try:
                with open(args.output_file, 'w', encoding='utf-8') as f:
                    json.dump(contract_info, f, ensure_ascii=False, indent=2)
                logging.info(f"Processed contract. Output saved to {args.output_file}")
            except IOError as e:
                logging.error(f"Error writing to output file {args.output_file}: {e}")
        else:
            logging.warning(f"No contract processed for file: {args.input_file}")

    except Exception as e:
        logging.error(f"Unexpected error in main function: {e}")
        logging.error(traceback.format_exc())  # Log the full traceback
        sys.exit(1)

if __name__ == "__main__":
    main()