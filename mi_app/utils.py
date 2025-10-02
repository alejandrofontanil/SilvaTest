from flask import url_for, render_template
from flask_mail import Message
from mi_app import mail
import os

def send_reset_email(user):
    """
    Envía un correo electrónico al usuario con un token para restablecer su contraseña.
    """
    token = user.get_reset_token()
    
    # El remitente se coge de la variable de entorno, que debería ser tu email configurado
    sender_email = os.environ.get('MAIL_USERNAME')

    msg = Message('Solicitud de Restablecimiento de Contraseña - SilvaTest',
                  sender=('SilvaTest', sender_email),
                  recipients=[user.email])
    
    msg.html = render_template(
        'email/reset_password.html',
        user=user,
        token=token
    )

    try:
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error al enviar el correo de restablecimiento: {e}")
        return False
