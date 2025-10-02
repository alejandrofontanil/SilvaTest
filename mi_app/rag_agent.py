import os
import json
from dotenv import load_dotenv
from google.cloud import aiplatform
from langchain_google_vertexai import VertexAIEmbeddings, VertexAI
from langchain_pinecone import Pinecone
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

# Carga las variables de entorno para que este módulo también las use
load_dotenv()

# Variables de Pinecone
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = "silvatest-rag" 

# Variables de Vertex AI
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCP_REGION = os.getenv("GCP_REGION")
GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDS_JSON")

# Inicialización del entorno de Vertex AI
try:
    if GOOGLE_CREDS_JSON:
        creds_info = json.loads(GOOGLE_CREDS_JSON)
        pass
    aiplatform.init(project=GCP_PROJECT_ID, location=GCP_REGION)
    print("✅ Vertex AI inicializado para el agente RAG.")
except Exception as e:
    print(f"Error al inicializar Vertex AI en rag_agent.py: {e}")


# Diccionario de templates de prompts para cada modo
PROMPT_TEMPLATES = {
    "formal": """
        Eres un asistente experto en oposiciones de Agente Medioambiental.
        Responde a la pregunta basándote ÚNICAMENTE en el siguiente contexto, de forma directa y concisa, sin añadir detalles o preámbulos.
        Si la información no está en el contexto, simplemente di "No se encontró información relevante.".

        Contexto:
        {context}

        Pregunta:
        {question}

        Respuesta concisa:
    """,
    "didactico": """
        Eres Silva, un preparador de oposiciones de élite. Tu objetivo es explicar conceptos de forma clara, didáctica y en un tono motivador, como en un cuaderno de estudio.
        Utiliza el siguiente contexto para responder a la pregunta.
        Organiza la respuesta con un formato de cuaderno, usando títulos en markdown (##), viñetas y negritas.
        Siempre comienza con una breve introducción didáctica.
        Cita las fuentes de donde extraes la información, al final de la respuesta, en una sección separada.

        Ejemplo de formato:
        ## 📖 Definición
        Una especie **catádroma** vive en agua dulce, pero migra al mar para reproducirse.

        ## 🐟 Ejemplo
        La anguila europea es el caso más típico...

        ## 📚 Fuente principal:
        - [Fuente 1]

        Contexto:
        {context}

        Pregunta:
        {question}

        Respuesta en formato de estudio:
    """
}

def get_rag_response(query: str, mode: str = "formal"):
    """
    Busca en el índice de Pinecone y genera una respuesta con Vertex AI.
    Permite seleccionar el modo de respuesta (formal o didáctico).
    """
    try:
        embeddings_model = VertexAIEmbeddings(model_name="text-embedding-004")
        llm = VertexAI(model_name="gemini-1.0-pro")

        vectorstore = Pinecone.from_existing_index(
            index_name=INDEX_NAME, 
            embedding=embeddings_model
        )

        retriever = vectorstore.as_retriever(search_kwargs={"k": 5}) # Aumentar a 5 chunks para más contexto
        
        # Seleccionar el prompt adecuado según el modo
        prompt_template_str = PROMPT_TEMPLATES.get(mode, PROMPT_TEMPLATES["formal"])
        prompt = PromptTemplate(template=prompt_template_str, input_variables=["context", "question"])

        # Crear una cadena RAG con el nuevo prompt
        qa = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            chain_type_kwargs={"prompt": prompt},
            return_source_documents=True # Esencial para citar las fuentes
        )
        
        response = qa.invoke({"query": query})
        
        sources = sorted(list(set([doc.metadata.get('source', 'N/A') for doc in response.get('source_documents', [])])))
        
        return {
            "result": response.get('result', "No se encontró una respuesta."),
            "sources": sources
        }

    except Exception as e:
        print(f"Error en get_rag_response: {e}")
        return {
            "result": f"Error: No se pudo generar la respuesta. {e}",
            "sources": []
        }