from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_migrate import Migrate
import os
import cloudinary
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
from sqlalchemy import MetaData
from dotenv import load_dotenv

# Cargar las variables de entorno desde .env
load_dotenv()

# Configuración para los nombres de las constraints de la BBDD
naming_convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
metadata = MetaData(naming_convention=naming_convention)

# Inicialización de las extensiones de Flask (SIN OAUTH)
db = SQLAlchemy(metadata=metadata)
bcrypt = Bcrypt()
login_manager = LoginManager()
mail = Mail()
migrate = Migrate()
csrf = CSRFProtect()

@login_manager.user_loader
def load_user(user_id):
    from .models import Usuario
    return Usuario.query.get(int(user_id))

# --- CAMBIO REALIZADO AQUÍ: Aceptar argumentos opcionales ---
def create_app(*args, **kwargs): 
    app = Flask(__name__, instance_relative_config=True)

    # --- CONFIGURACIÓN DE LA APP ---
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Configuración de la Base de Datos
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_uri = os.environ.get('DATABASE_URL')
    if db_uri and db_uri.startswith("postgres://"):
        db_uri = db_uri.replace("postgres://", "postgresql://", 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri or 'sqlite:///' + os.path.join(basedir, 'site.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Configuración de Flask-Mail
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')

    # Conectar las extensiones con la app
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db, render_as_batch=True)
    csrf.init_app(app)
    
    # --- CONFIGURACIÓN DE CLOUDINARY ---
    cloudinary.config(
        cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
        api_key=os.environ.get('CLOUDINARY_API_KEY'),
        api_secret=os.environ.get('CLOUDINARY_API_SECRET')
    )
    
    # Configuración de Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    login_manager.login_message = "Por favor, inicia sesión para acceder a esta página."

    with app.app_context():
        # --- REGISTRO DE BLUEPRINTS (RUTAS) ---
        from .routes.auth_routes import auth_bp
        app.register_blueprint(auth_bp)
        
        from .routes.main_routes import main_bp
        app.register_blueprint(main_bp)
        
        from .routes.admin_routes import admin_bp
        app.register_blueprint(admin_bp)

        # --- MANEJADORES DE ERRORES ---
        @app.errorhandler(404)
        def not_found_error(error):
            return render_template('errors/404.html'), 404

        @app.errorhandler(500)
        def internal_error(error):
            db.session.rollback()
            return render_template('errors/500.html'), 500
            
    return app
