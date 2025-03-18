import json
import chromadb
from openai import OpenAI
import dotenv

client = OpenAI(api_key=dotenv.get_key('.env', 'OPENAI_API_KEY'))
import dotenv


# Initialize ChromaDB client and collection
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="course_material")

# Function to generate OpenAI embeddings
def generate_embedding(text):
    response = client.embeddings.create(
        input=[text],
        model="text-embedding-ada-002"
    )
    embedding = response.data[0].embedding
    print(f"✅ Generated Embedding (first 5 values): {embedding[:5]}")
    return embedding


# Function to retrieve relevant context from ChromaDB
def retrieve_relevant_context(query, top_k=7):
    query_embedding = generate_embedding(query)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    retrieved_texts = [doc["text"] for doc in results["metadatas"][0]]

    print(len(retrieved_texts), "chunks retrieved")
    for i, text in enumerate(retrieved_texts):
        print(f"Chunk {i+1}: {text[:500]}...\n")

    return " ".join(retrieved_texts)

# Function to generate response using RAG (Retrieval-Augmented Generation)
def generate_rag_response(question, answer_options):
    query = f"Question: {question}\nOptions: {', '.join(answer_options)}"
    # context = retrieve_relevant_context(query)
    context = retrieve_relevant_context(question)

    prompt = f"""
    You are an AI tutor helping answer multiple-choice questions.
    Use the following course material to answer the question.
    
    Context:
    {context}
    
    Question:
    {question}

    Answer options:
    {', '.join(answer_options)}

    Answer with the correct option **and** justify your answer using information from the context.
    """

    response = client.chat.completions.create(model="gpt-3.5-turbo",
    messages=[{"role": "system", "content": "You are a helpful tutor."},
              {"role": "user", "content": prompt}])

    return response.choices[0].message.content

def main():
    # Example question and answer options
    question = "Checkbox supports a three-state mode, where the state toggles from checked to indeterminate to unchecked."
    answer_options = [
        "True",
        "False",
    ]
    response = generate_rag_response(question, answer_options)
    print("AI Response:")
    print(response)

if __name__ == "__main__":
    main()
    # all_vectors = chroma_client.get_collection("course_material").get(include=["documents", "embeddings"])
    # Print the first 5 vectors for debugging
    # for i, vector in enumerate(all_vectors["embeddings"][:10]):
    #     print(f"Vector {i+1}: {vector[:10]}...")  # Show only first 5 values
    # print(f"Total vectors stored: {len(all_vectors)}")
    # print(all_vectors)
