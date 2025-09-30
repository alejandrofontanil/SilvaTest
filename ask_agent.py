import os
from dotenv import load_dotenv
import pinecone
import vertexai
from vertexai.generative_models import GenerativeModel
from vertexai.language_models import TextEmbeddingModel
from pinecone import Pinecone

# --- 1. CONFIGURACIÓN INICIAL ---
print("Cargando configuración...")
load_dotenv()

# Leemos el ID del proyecto y la REGIÓN desde el .env
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
LOCATION = os.getenv("GCP_REGION")

# Inicializa Vertex AI explícitamente con tu ID de proyecto y tu REGIÓN
vertexai.init(project=PROJECT_ID, location=LOCATION)

# CAMBIO: Usamos el modelo más reciente
embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")
chat_model = GenerativeModel("gemini-1.5-flash-preview-0514")

# Inicializa la conexión con Pinecone
print("Conectando a Pinecone...")
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

# Conecta con nuestro índice
INDEX_NAME = "silvatest-temario"
index = pc.Index(INDEX_NAME)
print("¡Conexión exitosa!")

# --- 2. LÓGICA DEL CHAT ---

def run_chat():
    """Inicia un bucle de chat interactivo en la terminal."""
    print("\n--- Agente de IA SilvaTest (Escribe 'salir' para terminar) ---")
    while True:
        query = input("Tú: ")
        if query.lower() == 'salir':
            print("Agente: ¡Hasta luego!")
            break
        
        print("Agente: Pensando...")

        query_embedding = embedding_model.get_embeddings([query])[0].values

        results = index.query(
            vector=query_embedding,
            top_k=3,
            include_metadata=True
        )

        context = ""
        sources = set()
        for match in results['matches']:
            context += match['metadata']['text'] + "\n---\n"
            sources.add(match['metadata']['source'])

        prompt = f"""
        Basándote únicamente en el siguiente contexto extraído del temario, responde a la pregunta del usuario.
        Si la respuesta no está en el contexto, di que no tienes suficiente información.
        Sé claro y conciso.

        --- CONTEXTO ---
        {context}
        --- FIN DEL CONTEXTO ---

        Pregunta del usuario: {query}
        Respuesta:
        """
        response = chat_model.generate_content(prompt)
        
        print("\nAgente:", response.text)
        if sources:
            print(f"(Fuentes encontradas: {', '.join(sources)})")
        print("-" * 20)


if __name__ == "__main__":
    run_chat()