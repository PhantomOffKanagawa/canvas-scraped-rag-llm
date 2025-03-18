import json
from openai import OpenAI
import chromadb
import dotenv
import os
import shutil

# Function to generate OpenAI embeddings
def generate_embedding(text):
    response = client.embeddings.create(input=text,
    model="text-embedding-ada-002")
    return response.data[0].embedding

# Function to store chunks in ChromaDB
def store_chunks_in_chroma(chunks, file_index=0):
    for chunk in chunks:
        text = chunk["text"]
        print(f"Storing chunk: {text[:50]}...")
        embedding = generate_embedding(text)
        print(f"✅ Generated Embedding (first 5 values): {embedding[:5]}")
        doc_id = f"{file_index}-{chunk['page_index']}-{chunk['chunk_index']}"
        print(f"Storing chunk with ID: {doc_id}")
        collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            metadatas=[chunk]
        )
        print(f"Collection size: {len(collection.get()['ids'])}")

def main():
    # List of JSON file paths
    json_files = [
        './tokens/C#_.NET_sanitized_items_tokens.json',
        './tokens/pdf_text_tokens.json',
        './tokens/all_quiz_output_tokens.json',
    ]

    for i, file_path in enumerate(json_files):
        # Load the JSON file
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        print(f"Loaded {len(data)} chunks from {file_path}")

        # Store chunks in ChromaDB
        store_chunks_in_chroma(data, i)

    print("Chunks from all files stored in ChromaDB.")

if __name__ == "__main__":
    client = OpenAI(api_key=dotenv.get_key('.env', 'OPENAI_API_KEY'))

    # Remove existing ChromaDB directory if it exists
    if os.path.exists("./chroma_db"):
        shutil.rmtree("./chroma_db")

    # Initialize ChromaDB client and collection
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    collection = chroma_client.get_or_create_collection(name="course_material")

    main()
