from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_migrate import Migrate
from authlib.integrations.flask_client import OAuth
from sqlalchemy import inspect
import os
import cloudinary
from flask_wtf.csrf import CSRFProtect

# Inicializamos las extensiones
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
migrate = Migrate()
oauth = OAuth()
csrf = CSRFProtect()

@login_manager.user_loader
def load_user(user_id):
    from .models import Usuario
    return Usuario.query.get(int(user_id))

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # --- CONFIGURACIÓN DE LA APP ---
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_uri = os.environ.get('DATABASE_URL')
    if db_uri and db_uri.startswith("postgres://"):
        db_uri = db_uri.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri or 'sqlite:///' + os.path.join(basedir, 'site.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['RECAPTCHA_PUBLIC_KEY'] = os.environ.get('RECAPTCHA_PUBLIC_KEY')
    app.config['RECAPTCHA_PRIVATE_KEY'] = os.environ.get('RECAPTCHA_PRIVATE_KEY')

    # Conectamos las extensiones con la app
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    oauth.init_app(app)
    csrf.init_app(app)

    # --- REGISTRO DE GOOGLE OAUTH ---
    oauth.register(
        name='google',
        client_id=os.environ.get('GOOGLE_CLIENT_ID'),
        client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'}
    )

    # --- CONFIGURACIÓN DE CLOUDINARY ---
    cloudinary.config(
        cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME'),
        api_key = os.environ.get('CLOUDINARY_API_KEY'),
        api_secret = os.environ.get('CLOUDINARY_API_SECRET')
    )

    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    login_manager.login_message = "Por favor, inicia sesión para acceder a esta página."

    with app.app_context():
        # Registramos los blueprints
        from .routes.auth_routes import auth_bp
        app.register_blueprint(auth_bp)
        from .routes.main_routes import main_bp
        app.register_blueprint(main_bp)
        from .routes.admin_routes import admin_bp
        app.register_blueprint(admin_bp)

        # --- LÓGICA MEJORADA PARA CREAR/ACTUALIZAR USUARIO INVITADO ---
        try:
            db.create_all()
            from .models import Usuario
            invitado = Usuario.query.filter_by(nombre='Invitado').first()

            if not invitado:
                print("Creando usuario 'Invitado'...")
                invitado = Usuario(nombre='Invitado', email='invitado@example.com')
                invitado.password = '13579' # Usamos el @password.setter del modelo
                db.session.add(invitado)
                db.session.commit()
                print("¡Usuario 'Invitado' creado con éxito!")
            else:
                # Si ya existe, nos aseguramos de que tenga la contraseña correcta
                if not invitado.check_password('13579'):
                    print("Actualizando contraseña del usuario 'Invitado'...")
                    invitado.password = '13579'
                    db.session.commit()
                    print("¡Contraseña del invitado actualizada!")
                else:
                    print("El usuario 'Invitado' ya existe y tiene la contraseña correcta.")

        except Exception as e:
            # Esto puede pasar si la base de datos aún no está lista durante el despliegue.
            print(f"AVISO: No se pudo verificar/crear el usuario invitado al arrancar: {e}")
            db.session.rollback()
        # --- FIN DE LA LÓGICA MEJORADA ---
            
    # Manejadores de Errores
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    return app