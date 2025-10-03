import os
import json
from dotenv import load_dotenv
from google.cloud import aiplatform
from langchain_google_vertexai import VertexAIEmbeddings, VertexAI
from langchain_pinecone import Pinecone
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from google.oauth2 import service_account 

# Carga las variables de entorno
load_dotenv()

# Variables de Pinecone
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = "silvatest-rag" 

# Variables de Vertex AI
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCP_REGION = 'us-central1' # Región estable para Vertex AI
GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDS_JSON") 

# Modelo con enfoque en velocidad y calidad
LLM_MODEL_NAME = "gemini-2.5-flash" 

# --- CONFIGURACIÓN DE CREDENCIALES ---
try:
    credentials = None
    if GOOGLE_CREDS_JSON:
        creds_info = json.loads(GOOGLE_CREDS_JSON)
        credentials = service_account.Credentials.from_service_account_info(creds_info)
        
    aiplatform.init(project=GCP_PROJECT_ID, location=GCP_REGION, credentials=credentials)
    print("✅ Vertex AI inicializado para el agente RAG.")

except Exception as e:
    print(f"Error al inicializar Vertex AI en rag_agent.py: {e}")

# Diccionario de templates de prompts con Meta Prompting Potente
PROMPT_TEMPLATES = {
    "formal": """
        ## 🎯 Meta Prompt: Modo Formal (Precisión Legal)

        Eres un asistente RAG especializado en el temario oficial (Oposición Agente Medioambiental de Castilla y León/Asturias).
        Tu rol es actuar como un **experto legal y técnico**.

        **REGLAS ESTRICTAS:**
        1.  **Exclusividad del Contexto:** Responde ÚNICA y EXCLUSIVAMENTE con la información contenida en la sección {context}.
        2.  **Concisión:** Sé lo más breve y directo posible. Usa una lista si la información lo permite, pero sin preámbulos.
        3.  **Tono:** Objetivo, técnico y neutro.

        Contexto:
        {context}

        Pregunta del usuario: {question}

        Respuesta concisa:
    """,
    "didactico": """
        ## 🧑‍🏫 Meta Prompt: Modo Didáctico (Tutoría de Oposiciones)

        Eres Silva, un preparador de oposiciones de élite con una personalidad **motivadora y didáctica**. Tu misión es transformar el contexto en **apuntes de estudio memorables**.

        **REGLAS Y FORMATO (Notebook Style):**
        1.  **Formato:** Utiliza Markdown enriquecido (##, viñetas, **negritas**) para crear secciones.
        2.  **Estructura:** La respuesta DEBE contener estas secciones (o las más relevantes):
            * **## 📖 Concepto Clave:** Define el término principal.
            * **## 🐟 Ejemplo/Aplicación:** Proporciona un ejemplo práctico del temario.
            * **## 💡 Nota de Estudio:** Añade un dato relacionado o una diferencia clave para memorizar.
        3.  **Fuentes Legales:** Finaliza siempre con una sección `## 📚 Fuentes Legales/Temario` donde **identificas y nombras** el documento o la ley de origen (ej: "Ley 42/2007 de Patrimonio Natural", "Tema 8. Especies de Pesca (nuevo)"). No uses nombres de archivo crudos como "documento-1.pdf".

        Contexto para el análisis: {context}

        Pregunta del usuario: {question}

        Respuesta en formato de estudio:
    """
}

# La función principal
def get_rag_response(query: str, mode: str = "formal"):
    """
    Busca en el índice de Pinecone y genera una respuesta con Vertex AI.
    Permite seleccionar el modo de respuesta (formal o didáctico).
    """
    try:
        credentials = service_account.Credentials.from_service_account_info(json.loads(GOOGLE_CREDS_JSON))
    except Exception:
        credentials = None 
        
    try:
        # --- AJUSTE DE PARÁMETROS CLAVE ---
        # Temperatura: Baja (0.3) para máxima precisión y mínima creatividad, ideal para oposiciones.
        TEMPERATURE = 0.3
        
        # Inicializa los embeddings y el LLM, pasando las credenciales
        embeddings_model = VertexAIEmbeddings(model_name="text-embedding-004", credentials=credentials)
        llm = VertexAI(
            model_name=LLM_MODEL_NAME, 
            credentials=credentials,
            temperature=TEMPERATURE # AÑADIDO: Control de temperatura
        )

        # Conexión a Pinecone (ya corregida)
        vectorstore = Pinecone.from_existing_index(
            index_name=INDEX_NAME, 
            embedding=embeddings_model
        )
        
        # Retrieval: k=5 para obtener 5 fragmentos, asegurando suficiente contexto.
        retriever = vectorstore.as_retriever(search_kwargs={"k": 5}) 
        
        prompt_template_str = PROMPT_TEMPLATES.get(mode, PROMPT_TEMPLATES["formal"])
        prompt = PromptTemplate(template=prompt_template_str, input_variables=["context", "question"])

        # Creación de la cadena RAG
        qa = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            chain_type_kwargs={"prompt": prompt},
            return_source_documents=True 
        )
        
        response = qa.invoke({"query": query})
        
        # La lógica de fuentes se mantiene aquí, pero el PROMPT le indica a Gemini
        # cómo formatear el nombre de la fuente de manera amigable.
        sources = sorted(list(set([doc.metadata.get('tema', doc.metadata.get('source', 'Fuente no identificada')) for doc in response.get('source_documents', [])])))
        
        # Instruir al LLM para que filtre y presente las fuentes de manera amigable
        # Enviamos las fuentes de vuelta al LLM para que las cite limpiamente dentro del formato.
        final_result = response.get('result', "No se encontró una respuesta.")
        
        # Si el modo es didáctico, adjuntamos la información de la fuente de forma legible
        if mode == "didactico" and sources:
             final_result += "\n\n" + "## 📚 Fuentes Legales/Temario:\n" + "\n".join([f"- {s}" for s in sources])

        return {
            "result": final_result,
            "sources": sources
        }

    except Exception as e:
        print(f"Error en get_rag_response: {e}")
        return {
            "result": f"Error: No se pudo conectar a Google AI. Detalles: {e}",
            "sources": []
        }
