import os
import json
import re
import requests
import time
import fitz  # PyMuPDF
from pathlib import Path

# Create necessary directories
Path("pdfs").mkdir(exist_ok=True)

# Load the JSON data
with open('C#_.NET_items.json', 'r', encoding='utf-8') as f:
    items = json.load(f)

# Regular expression pattern to find PDF links
pdf_link_pattern = r'<a class="instructure_file_link instructure_scribd_file" title="([^"]+\.pdf)" href="([^"]+)" data-api-endpoint="[^"]+" data-api-returntype="File">[^<]+</a>'

# Extract all PDF links
pdf_links = []
for item in items:
    if 'body' in item:
        matches = re.findall(pdf_link_pattern, item['body'])
        for match in matches:
            title, url = match
            pdf_links.append({
                'title': title,
                'url': url
            })

# Remove duplicates based on title
unique_pdf_links = []
seen_titles = set()
for link in pdf_links:
    if link['title'] not in seen_titles:
        unique_pdf_links.append(link)
        seen_titles.add(link['title'])

print(f"Found {len(unique_pdf_links)} unique PDF files to download")

# Download PDFs and extract text
pdf_texts = []
for i, link in enumerate(unique_pdf_links):
    title = link['title']
    url = link['url']
    
    # Clean filename
    safe_filename = "".join([c for c in title if c.isalpha() or c.isdigit() or c==' ' or c=='.']).rstrip()
    pdf_path = os.path.join('pdfs', safe_filename)

    if os.path.exists(pdf_path):
        print(f"Skipping {title}, already downloaded.")
    else:
        print(f"Downloading {i+1}/{len(unique_pdf_links)}: {title}")
        
        try:
            # Download the PDF
            response = requests.get(url)
            with open(pdf_path, 'wb') as f:
                f.write(response.content)
    
            # Wait a bit to avoid rate limiting
            time.sleep(2)
        
        except Exception as e:
            print(f"Error downloading {title}: {e}")
            
    # Extract text from PDF using PyMuPDF
    text = ""
    try:
        doc = fitz.open(pdf_path)
        for page in doc:
            text += page.get_text()
            text += "\n\n"  # Add newlines between pages
        doc.close()
    except Exception as e:
        print(f"Error extracting text from {title}: {e}")
        
    # Add to our collection
    pdf_texts.append({
        'title': title,
        'url': url,
        'body': text
    })
        
# Save extracted text to JSON file
with open('pdf_text.json', 'w', encoding='utf-8') as f:
    json.dump(pdf_texts, f, ensure_ascii=False, indent=2)

print(f"Extracted text from {len(pdf_texts)} PDFs and saved to pdf_text.json")