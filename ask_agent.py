import os
from dotenv import load_dotenv
import pinecone
import google.generativeai as genai
from pinecone import Pinecone

# --- 1. CONFIGURACIÓN INICIAL ---
print("Cargando configuración...")
load_dotenv()

# CAMBIO: Usamos la nueva librería con la API Key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# CAMBIO: Cargamos los modelos con la nueva sintaxis
embedding_model = "models/embedding-004"
chat_model = genai.GenerativeModel("gemini-1.5-flash")

print("Conectando a Pinecone...")
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
INDEX_NAME = "silvatest-temario"
index = pc.Index(INDEX_NAME)
print("¡Conexión exitosa!")

# --- 2. LÓGICA DEL CHAT ---
def run_chat():
    print("\n--- Agente de IA SilvaTest (Escribe 'salir' para terminar) ---")
    while True:
        query = input("Tú: ")
        if query.lower() == 'salir':
            break
        print("Agente: Pensando...")

        # CAMBIO: Nueva forma de generar el embedding de la pregunta
        query_embedding = genai.embed_content(
            model=embedding_model,
            content=query,
            task_type="RETRIEVAL_QUERY"
        )['embedding']

        results = index.query(vector=query_embedding, top_k=3, include_metadata=True)
        
        context = ""
        sources = set()
        for match in results['matches']:
            context += match['metadata']['text'] + "\n---\n"
            sources.add(match['metadata']['source'])
        
        prompt = f"Basándote únicamente en el siguiente contexto, responde a la pregunta. Si la respuesta no está en el contexto, di que no tienes información.\n\n--- CONTEXTO ---\n{context}\n--- FIN DEL CONTEXTO ---\n\nPregunta: {query}\nRespuesta:"
        
        response = chat_model.generate_content(prompt)
        
        print("\nAgente:", response.text)
        if sources:
            print(f"(Fuentes encontradas: {', '.join(sources)})")
        print("-" * 20)
    print("Agente: ¡Hasta luego!")

if __name__ == "__main__":
    run_chat()