from bs4 import BeautifulSoup
import json

def parse_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    extracted_data = {
        "noticeDetails": {},
        "contractingAuthority": {},
        "procurement": {
            "lots": []
        },
        "additionalInformation": {},
        "reviewProcedures": {}
    }
    
    # Extract the title and publication details
    header = soup.find('div', class_='header-content')
    if header:
        titles = header.find_all('span', class_='title bold')
        if len(titles) >= 2:
            extracted_data['noticeDetails']['id'] = titles[0].text.strip()
            extracted_data['noticeDetails']['title'] = titles[1].text.strip()
        
        publication_details = header.find_all('div', class_='bold')
        if publication_details:
            extracted_data['noticeDetails']['publicationDetails'] = [pd.text.strip() for pd in publication_details]
    
    # Extract sections
    sections = soup.find_all('div', class_='level')
    for section in sections:
        section_title = section.find('span', {'data-labels-key': lambda x: x and x.startswith('ted_label.2014_common|section_')})
        if section_title:
            section_name = section_title.text.strip()
            
            # Extract subsections
            subsections = section.find_next_siblings('div', class_='sublevel')
            for subsection in subsections:
                subsection_number = subsection.find('div', class_='sublevel__number')
                subsection_content = subsection.find('div', class_='sublevel__content')
                if subsection_number and subsection_content:
                    subsection_name = subsection_number.text.strip().replace('.', '')
                    
                    # Populate specific sections
                    if section_name == "Section I":
                        if subsection_name == "I1":
                            extracted_data['contractingAuthority'] = parse_contracting_authority(subsection_content)
                    elif section_name == "Section II":
                        if subsection_name == "II11":
                            extracted_data['procurement']['title'] = subsection_content.find('div').text.strip()
                            extracted_data['procurement']['referenceNumber'] = subsection_content.find('span', {'data-labels-key': 'ted_label.2014_common|fileref'}).find_next('span').text.strip()
                        elif subsection_name == "II14":
                            extracted_data['procurement']['shortDescription'] = subsection_content.get_text(strip=True, separator=' ')
                        elif subsection_name == "II24":
                            extracted_data['procurement']['description'] = subsection_content.get_text(strip=True, separator=' ')
                        elif subsection_name.startswith("II2"):
                            lot = parse_lot(subsection_content)
                            if lot:
                                extracted_data['procurement']['lots'].append(lot)
                    elif section_name == "Section VI":
                        if subsection_name == "VI3":
                            extracted_data['additionalInformation']['info'] = subsection_content.get_text(strip=True, separator=' ')
                        elif subsection_name == "VI41":
                            extracted_data['reviewProcedures']['reviewBody'] = parse_review_body(subsection_content)
                
                # Stop when we reach the next section
                if subsection.find_next_sibling('div', class_='level'):
                    break
    
    return extracted_data

def parse_contracting_authority(content):
    authority = {}
    authority['officialName'] = content.find('span', {'data-labels-key': 'ted_label.2014_common|name_official'}).find_next().text.strip()
    authority['nationalId'] = content.find('span', {'data-labels-key': 'ted_label.2014_common|national_id'}).find_next().text.strip()
    authority['address'] = {
        'street': content.find('span', {'data-labels-key': 'ted_label.2014_common|address_postal'}).find_next().text.strip(),
        'town': content.find('span', {'data-labels-key': 'ted_label.2014_common|address_town'}).find_next().text.strip(),
        'country': content.find('span', {'data-labels-key': 'ted_label.2014_common|address_country'}).find_next().text.strip()
    }
    authority['contact'] = {
        'email': content.find('span', {'data-labels-key': 'ted_label.2014_common|address_email'}).find_next().text.strip(),
        'phone': content.find('span', {'data-labels-key': 'ted_label.2014_common|address_phone'}).find_next().text.strip()
    }
    return authority

def parse_lot(content):
    lot = {}
    lot_number = content.find('span', {'data-labels-key': 'ted_label.2014_common|lot_number'})
    if lot_number:
        lot['number'] = lot_number.find_next('span').text.strip()
    lot_title = content.find('div', class_='bold')
    if lot_title:
        lot['title'] = lot_title.text.strip()
    lot_description = content.find('span', {'data-labels-key': 'ted_label.2014_common|descr_procurement'})
    if lot_description:
        lot['description'] = lot_description.find_next('div').text.strip()
    return lot if lot else None

def parse_review_body(content):
    review_body = {}
    review_body['officialName'] = content.find('span', {'data-labels-key': 'ted_label.2014_common|name_official'}).find_next().text.strip()
    review_body['town'] = content.find('span', {'data-labels-key': 'ted_label.2014_common|address_town'}).find_next('span').text.strip()
    review_body['country'] = content.find('span', {'data-labels-key': 'ted_label.2014_common|address_country'}).find_next('span').text.strip()
    review_body['phone'] = content.find('span', {'data-labels-key': 'ted_label.2014_common|address_phone'}).find_next('span').text.strip()
    return review_body

# New code to test the function with test-html.html
if __name__ == "__main__":
    # Read the content of test-html.html
    with open('test-html.html', 'r', encoding='utf-8') as file:
        html_content = file.read()

    # Parse the HTML content
    parsed_data = parse_html(html_content)

    # Print the parsed data
    print(json.dumps(parsed_data, indent=2, ensure_ascii=False))