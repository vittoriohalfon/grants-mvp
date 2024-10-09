import xml.etree.ElementTree as ET
import json
import os

def parse_xml_to_json(xml_content, file_name):
    # Define all relevant namespaces
    namespaces = {
        'ns': 'http://publications.europa.eu/resource/schema/ted/R2.0.9/publication',
        'n2021': 'http://publications.europa.eu/resource/schema/ted/2021/nuts',
        'xlink': 'http://www.w3.org/1999/xlink',
        'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
    }
    
    root = ET.fromstring(xml_content)
    
    # Helper function to find elements or attributes
    def find_element(path, is_attribute=False, attribute_name=None, default=""):
        try:
            element = root.find(path, namespaces)
            if element is not None:
                if is_attribute and attribute_name:
                    return element.get(attribute_name, default)
                else:
                    return element.text.strip() if element.text else default
            return default
        except Exception:
            return default

    # Extract notice_publication_id from file name
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
            "place_of_performance": find_element(".//ns:OBJECT_CONTRACT/ns:OBJECT_DESCR/n2021:NUTS", is_attribute=True, attribute_name="CODE")
        },
        "value": {
            "estimated_value": find_element(".//ns:OBJECT_CONTRACT/ns:VAL_ESTIMATED_TOTAL"),
            "currency": find_element(".//ns:OBJECT_CONTRACT/ns:VAL_OBJECT", is_attribute=True, attribute_name="CURRENCY"),
            "maximum_value": find_element(".//ns:OBJECT_CONTRACT/ns:VAL_OBJECT"),
        },
        "lots": [
            {
                "lot": "LOT-0001",
                "title": find_element(".//ns:OBJECT_CONTRACT/ns:TITLE/ns:P"),
                "description": find_element(".//ns:OBJECT_CONTRACT/ns:SHORT_DESCR/ns:P"),
                "main_nature": find_element(".//ns:OBJECT_CONTRACT/ns:TYPE_CONTRACT", is_attribute=True, attribute_name="CTYPE").lower(),
                "main_classification": find_element(".//ns:OBJECT_CONTRACT/ns:CPV_MAIN/ns:CPV_CODE", is_attribute=True, attribute_name="CODE"),
                "additional_classifications": [
                    code.get('CODE', '') 
                    for code in root.findall(".//ns:OBJECT_CONTRACT/ns:CPV_ADDITIONAL/ns:CPV_CODE", namespaces)
                ],
                "place_of_performance": find_element(".//ns:OBJECT_CONTRACT/ns:OBJECT_DESCR/n2021:NUTS", is_attribute=True, attribute_name="CODE"),
                "value": {
                    "estimated_value": find_element(".//ns:OBJECT_CONTRACT/ns:VAL_ESTIMATED_TOTAL"),
                    "currency": find_element(".//ns:OBJECT_CONTRACT/ns:VAL_ESTIMATED_TOTAL", is_attribute=True, attribute_name="CURRENCY"),
                    "maximum_value": find_element(".//ns:OBJECT_CONTRACT/ns:VAL_OBJECT")
                }
            }
        ]
    }

    return json.dumps(result, indent=2)

def process_all_xml_files(input_dir='contracts_xml', output_dir='processed_contracts_2'):
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # List all files in the input directory
    try:
        files = os.listdir(input_dir)
    except FileNotFoundError:
        print(f"Input directory '{input_dir}' does not exist.")
        return
    
    # Filter out only XML files
    xml_files = [file for file in files if file.lower().endswith('.xml')]
    
    if not xml_files:
        print(f"No XML files found in the directory '{input_dir}'.")
        return
    
    for file_name in xml_files:
        xml_file_path = os.path.join(input_dir, file_name)
        try:
            with open(xml_file_path, 'r', encoding='utf-8') as file:
                xml_content = file.read()
            
            # Parse XML to JSON
            json_output = parse_xml_to_json(xml_content, file_name)
            
            # Define output file name and path
            output_file_name = f"{os.path.splitext(file_name)[0]}.json"
            output_file_path = os.path.join(output_dir, output_file_name)
            
            # Write JSON to file
            with open(output_file_path, 'w', encoding='utf-8') as out_file:
                out_file.write(json_output)
            
            print(f"Processed and created JSON file: {output_file_path}")
        
        except Exception as e:
            print(f"Failed to process file '{file_name}'. Error: {e}")

if __name__ == "__main__":
    process_all_xml_files()