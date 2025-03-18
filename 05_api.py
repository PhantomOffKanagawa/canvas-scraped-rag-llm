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
def retrieve_relevant_context(query, top_k=5):
    query_embedding = generate_embedding(query)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    retrieved_texts = [doc["text"] for doc in results["metadatas"][0]]

    print(len(retrieved_texts), "chunks retrieved")
    for i, text in enumerate(retrieved_texts):
        print(f"Chunk {i+1}: {text[:500]}...\n")

    return retrieved_texts

# Function to generate response using RAG (Retrieval-Augmented Generation)
def generate_rag_response(question, answer_options):
    if answer_options[0] == "True" and answer_options[1] == "False":
        query = f"Question: {question}"
    else:
        query = f"Question: {question}\nOptions: {', '.join(answer_options)}"
    
    context = retrieve_relevant_context(query)  # Retrieve context based on the constructed query
    context_text = " ".join(context)  # Join the retrieved texts into a single string

    prompt = f"""
    Context:
    {context_text}
    
    Question:
    {question}

    Answer options:
    {', '.join(answer_options)}

    If a context explicitly states the answer, it overrides other explanations.
    Begin the response solely with the correct option(s). This should be in **bold** and if there are multiple correct option seperate them on a new line.
    If the correct answer is not explicitly stated in the context, choose the most appropriate option based on the context.
    **And** ***ALWAYS*** justify your answer using information from the context, specifically explaining what led to the conclusion.
    """

    response = client.chat.completions.create(model="gpt-3.5-turbo",
    messages=[{"role": "system", "content": "You are a helpful tutor. Your users are asking questions about information contained in course material. "
               "You will be shown the user's question, and the relevant information from the course material. Answer the user's question using only this information."},
              {"role": "user", "content": prompt}])

    return (context, response.choices[0].message.content)
    
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin

app = Flask(__name__)
cors = CORS(app, resources={r"/ask": {"origins": "*"}})
app.config['CORS_HEADERS'] = 'Content-Type'

@app.route("/ask", methods=["POST"])
def ask():
    print("Received request:", request.json)

    question = request.json["query"]
    answers = request.json["answers"]

    print("Question:", question)
    print("Answers:", answers)

    context, answer = generate_rag_response(question, answers)

    print("AI Response:", answer)

    return jsonify({"response": answer,
                    "context": context})

if __name__ == "__main__":
    app.run(debug=True)
