from mi_app import create_app

# --- NUEVAS IMPORTACIONES AÑADIDAS ---
from mi_app.models import Usuario
from mi_app.email_utils import get_stats_semanales
from mi_app import mail
from flask_mail import Message
from flask import render_template
from datetime import datetime
# --- FIN DE LAS NUEVAS IMPORTACIONES ---

app = create_app()

# === CÓDIGO AÑADIDO PARA EL COMANDO DE ENVÍO DE EMAILS ===
@app.cli.command("enviar-resumenes")
def enviar_resumenes_semanales():
    """Busca a todos los usuarios que han activado el resumen semanal y se lo envía."""
    
    # El contexto de la aplicación es necesario para que url_for funcione en la plantilla del email
    with app.app_context():
        users = Usuario.query.filter_by(recibir_resumen_semanal=True).all()
        print(f"-> Encontrados {len(users)} usuarios para enviar resumen.")
        
        for user in users:
            stats = get_stats_semanales(user)
            
            # Pasamos la función now() a la plantilla para que pueda mostrar el año
            html = render_template('emails/resumen_semanal.html', user=user, stats=stats, now=datetime.utcnow)
            
            msg = Message('Tu Resumen Semanal en SilvaTest',
                          sender=('SilvaTest', app.config['MAIL_USERNAME']), # Usamos el email de la configuración
                          recipients=[user.email])
            msg.html = html
            
            try:
                mail.send(msg)
                print(f"-> Email enviado con éxito a {user.email}")
            except Exception as e:
                print(f"!! Error al enviar email a {user.email}: {e}")
        
        print("-> Proceso de envío de resúmenes finalizado.")
# === FIN DEL CÓDIGO AÑADIDO ===


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)