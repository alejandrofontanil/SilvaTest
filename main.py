from mi_app import create_app

# --- IMPORTACIONES PARA LOS COMANDOS CLI ---
from mi_app.models import Usuario
from mi_app.email_utils import get_stats_semanales
from mi_app import mail, db # Se añade db aquí
from flask_mail import Message
from flask import render_template
from datetime import datetime
# --- FIN DE LAS IMPORTACIONES ---

app = create_app()

# === COMANDO PARA EL ENVÍO DE EMAILS ===
@app.cli.command("enviar-resumenes")
def enviar_resumenes_semanales():
    """Busca a todos los usuarios que han activado el resumen semanal y se lo envía."""
    
    # El contexto de la aplicación es necesario para que url_for funcione
    with app.app_context():
        users = Usuario.query.filter_by(recibir_resumen_semanal=True).all()
        print(f"-> Encontrados {len(users)} usuarios para enviar resumen.")
        
        for user in users:
            stats = get_stats_semanales(user)
            
            # Pasamos la función now() a la plantilla para que pueda mostrar el año
            html = render_template('emails/resumen_semanal.html', user=user, stats=stats, now=datetime.utcnow)
            
            msg = Message('Tu Resumen Semanal en SilvaTest',
                          sender=('SilvaTest', app.config['MAIL_USERNAME']),
                          recipients=[user.email])
            msg.html = html
            
            try:
                mail.send(msg)
                print(f"-> Email enviado con éxito a {user.email}")
            except Exception as e:
                print(f"!! Error al enviar email a {user.email}: {e}")
        
        print("-> Proceso de envío de resúmenes finalizado.")

# === NUEVO COMANDO PARA INICIALIZAR LA BBDD Y EL USUARIO INVITADO ===
@app.cli.command("init-db")
def init_db_command():
    """Crea las tablas si no existen y asegura que el usuario Invitado esté configurado."""
    with app.app_context():
        db.create_all()
        
        invitado = Usuario.query.filter_by(nombre='Invitado').first()

        if not invitado:
            print("Creando usuario 'Invitado'...")
            invitado = Usuario(nombre='Invitado', email='invitado@example.com')
            invitado.password = '13579'
            db.session.add(invitado)
            db.session.commit()
            print("¡Usuario 'Invitado' creado con éxito!")
        else:
            if not invitado.check_password('13579'):
                print("Actualizando contraseña del usuario 'Invitado'...")
                invitado.password = '13579'
                db.session.commit()
                print("¡Contraseña del invitado actualizada!")
            else:
                print("El usuario 'Invitado' ya existe y tiene la contraseña correcta.")
        
        print("Base de datos inicializada y usuario Invitado verificado.")
# === FIN DEL NUEVO COMANDO ===


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)