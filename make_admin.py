# Contenido del archivo make_admin.py

from mi_app import create_app, db
from mi_app.models import Usuario

# --- El email del usuario que queremos hacer administrador ---
email_a_promover = 'alejandrofontanil@gmail.com'
# ---------------------------------------------------------


# Creamos una instancia de nuestra app Flask
app = create_app()

# Usamos app.app_context() para asegurarnos de que estamos "dentro" de la aplicación
with app.app_context():
    print(f"Buscando al usuario con el email: {email_a_promover}...")

    # Buscamos al usuario en la base de datos
    usuario = Usuario.query.filter_by(email=email_a_promover).first()

    # Si lo encontramos, lo hacemos admin
    if usuario:
        if usuario.es_admin:
            print(f"-> ¡Éxito! El usuario '{usuario.nombre}' ya es administrador.")
        else:
            print(f"-> Usuario encontrado: '{usuario.nombre}'. Promoviendo a administrador...")
            usuario.es_admin = True
            db.session.commit()
            print("-> ¡Éxito! El usuario ha sido actualizado a administrador.")
    else:
        print(f"-> ¡ERROR! No se encontró ningún usuario con el email '{email_a_promover}'.")

print("-> Proceso finalizado.")