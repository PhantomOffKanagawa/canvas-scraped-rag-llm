import json
import tiktoken
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pathlib import Path

# Initialize tokenizer (for token estimation)
tokenizer = tiktoken.get_encoding("cl100k_base")

# Function to count tokens
def count_tokens(text):
    return len(tokenizer.encode(text))

# Function to process JSON objects into chunks
def process_json_documents(json_data, chunk_size=500, chunk_overlap=50):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    processed_chunks = []
    for idx, obj in enumerate(json_data):
        text = obj.get("body", "").strip()
        if not text:
            continue  # Skip empty pages

        token_count = count_tokens(text)

        # Keep small pages whole, otherwise split
        if token_count <= chunk_size:
            processed_chunks.append({"page_index": idx, "chunk_index": 0, "text": text})
        else:
            chunks = text_splitter.split_text(text)
            for chunk_idx, chunk in enumerate(chunks):
                processed_chunks.append({"page_index": idx, "chunk_index": chunk_idx, "text": chunk})

    return processed_chunks

def main():
    # List of JSON files to process
    json_files = [
        'C#_.NET_sanitized_items.json',
        'pdf_text.json',
        'all_quiz_output.json',
    ]

    for json_file in json_files:
        # Load the JSON file
        with open(json_file, 'r', encoding='utf-8') as file:
            data = json.load(file)

        processed_chunks = process_json_documents(data, chunk_size=1000)

        # Save processed chunks to a JSON file named after the input file
        output_file = "./tokens/" + Path(json_file).stem + "_tokens.json"
        with open(output_file, "w", encoding="utf-8") as output:
            json.dump(processed_chunks, output, indent=4, ensure_ascii=False)
        print(f"Processed chunks saved to {output_file}")

if __name__ == "__main__":
    main()