# send_summary.py (Versión final corregida)

import os
from datetime import datetime, timedelta
from flask import render_template
from mi_app import create_app, db, mail
from mi_app.models import User, ResultadoTest
from flask_mail import Message

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
ctx = app.app_context()
ctx.push()

print("Script iniciado y contexto de la aplicación cargado.")

def send_weekly_summary():
    fecha_fin = datetime.utcnow()
    fecha_inicio = fecha_fin - timedelta(days=7)
    current_year = fecha_fin.year # <-- AÑADIDO: Obtenemos el año actual aquí

    print(f"Buscando tests entre {fecha_inicio.strftime('%Y-%m-%d')} y {fecha_fin.strftime('%Y-%m-%d')}.")

    usuarios_suscritos = User.query.filter_by(recibir_resumen_semanal=True).all()
    print(f"Se encontraron {len(usuarios_suscritos)} usuarios suscritos.")

    for usuario in usuarios_suscritos:
        print(f"Procesando usuario: {usuario.email}")
        
        resultados = ResultadoTest.query.filter(
            ResultadoTest.user_id == usuario.id,
            ResultadoTest.fecha.between(fecha_inicio, fecha_fin)
        ).all()
        
        # Si no hay resultados, ahora creamos un diccionario de stats vacío para que la plantilla funcione
        if not resultados:
            stats = None # <-- CAMBIO: Usamos None para que el 'if stats' de la plantilla falle correctamente
            print(f"  -> El usuario {usuario.email} no tiene tests esta semana.")
        else:
            # <-- AÑADIDO: Creamos un diccionario 'stats' para agrupar los datos
            stats = {
                'tests_completados': len(resultados),
                'nota_media': "%.2f" % (sum(r.nota for r in resultados) / len(resultados))
            }
            print(f"  -> Tests realizados: {stats['tests_completados']}, Nota media: {stats['nota_media']}")

        # Renderizar la plantilla HTML del correo con los datos
        # Ahora los nombres de las variables coinciden con los de la plantilla
        html_body = render_template('emails/resumen_semanal.html', 
                                    user=usuario,             # <-- CAMBIO: 'usuario' ahora se llama 'user'
                                    stats=stats,              # <-- CAMBIO: Pasamos el diccionario 'stats'
                                    current_year=current_year) # <-- AÑADIDO: Pasamos el año a la plantilla

        msg = Message(
            subject=f'¡Tu Resumen Semanal de Progreso, {usuario.nombre}!', # <-- MEJORA: Asunto personalizado
            sender=os.environ.get('MAIL_USERNAME'),
            recipients=[usuario.email]
        )
        msg.html = html_body
        
        try:
            # Solo enviamos el correo si el usuario tuvo actividad
            if stats: # <-- MEJORA: Añadimos esta condición para no molestar a usuarios inactivos
                mail.send(msg)
                print(f"  -> Correo enviado exitosamente a {usuario.email}")
        except Exception as e:
            print(f"  -> ERROR al enviar correo a {usuario.email}: {e}")

    print("Proceso de envío de resúmenes finalizado.")

if __name__ == '__main__':
    send_weekly_summary()
    ctx.pop()