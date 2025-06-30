# Este es el contenido para diagnostico.py

# Importamos las herramientas necesarias de nuestra aplicación
from main import app, db, Tema

# Activamos el contexto de la aplicación para poder hablar con la base de datos
app.app_context().push()

print("--- COMPROBANDO ESTRUCTURA DE TEMAS ---")

# Buscamos todos los temas que hay en la base de datos
todos_los_temas = Tema.query.all()

if not todos_los_temas:
    print("No se encontraron temas en la base de datos.")
else:
    print("Analizando los temas guardados:")
    # Para cada tema, comprobamos si tiene un padre o no
    for tema in todos_los_temas:
        if tema.parent:
            print(f"- Tema: '{tema.nombre}' (ID: {tema.id}) -> es SUBTEMA de: '{tema.parent.nombre}' (ID: {tema.parent_id})")
        else:
            print(f"- Tema: '{tema.nombre}' (ID: {tema.id}) -> es un TEMA PRINCIPAL (Parent ID: {tema.parent_id})")

print("--- FIN DE LA COMPROBACIÓN ---")