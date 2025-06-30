# create_db.py
# Este script solo se usa una vez para crear la base de datos.

print("--- Iniciando el script de creación de base de datos ---")

# Importamos los objetos 'app' y 'db' desde nuestro archivo principal
from main import app, db

# Importamos todos los modelos para que SQLAlchemy los reconozca
from main import Usuario, Tema, Pregunta, Respuesta, ResultadoTest

# Nos metemos en el "contexto" de la aplicación para poder operar
with app.app_context():
    print("Creando todas las tablas. Esto puede tardar un momento...")

    # El comando mágico para crear todas las tablas definidas en los modelos
    db.create_all()

    print("¡LISTO! Base de datos y tablas creadas con éxito.")