from mi_app import create_app, db
from mi_app.models import Usuario

# --- IMPORTANTE: Revisa que este sea tu email ---
USER_EMAIL_TO_ACTIVATE = "alejandrofontanil@gmail.com"
# ----------------------------------------------------

def activate_ia_access():
    """
    Función para encontrar un usuario y activar su acceso a la IA.
    """
    app = create_app()
    with app.app_context():
        # Busca al usuario por su email
        user = Usuario.query.filter_by(email=USER_EMAIL_TO_ACTIVATE).first()

        if user:
            # Activa la bandera de acceso a la IA
            user.tiene_acceso_ia = True
            
            # Guarda los cambios en la base de datos
            db.session.commit()
            
            print(f"✅ ¡Éxito! Acceso a la IA activado para el usuario {user.email}")
        else:
            print(f"❌ Error: No se encontró ningún usuario con el email {USER_EMAIL_TO_ACTIVATE}")

if __name__ == '__main__':
    activate_ia_access()