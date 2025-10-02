from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, session
from flask_login import login_user, logout_user, current_user, login_required
import os
from urllib.parse import urlparse, urljoin
from sqlalchemy import or_
import requests
from mi_app import db, bcrypt
from mi_app.models import Usuario
from mi_app.forms import RegistrationForm, LoginForm, RequestResetForm, ResetPasswordForm, ObjetivoForm
from mi_app.utils import send_reset_email

auth_bp = Blueprint('auth', __name__,
                    template_folder='../templates/auth',
                    url_prefix='/auth')

# >>> SOLUCIÓN CODESPACES: Forzamos la URL pública para el redirect de Google OAuth <<<
# ESTA URL DEBE COINCIDIR EXACTAMENTE con la que registraste en Google Cloud Console.
CODESPACE_HOST = 'https://fuzzy-space-computing-machine-wr44wjx46497f5ggp-5000.app.github.dev'


def is_safe_url(target):
    if not target:
        return True
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

@auth_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        nuevo_usuario = Usuario(
            nombre=form.nombre.data, 
            email=form.email.data.lower(),
            objetivo_principal=form.objetivo_principal.data
        )
        nuevo_usuario.password = form.password.data
        db.session.add(nuevo_usuario)
        db.session.commit()

        admin_email = os.getenv('ADMIN_EMAIL')
        if admin_email and nuevo_usuario.email == admin_email:
            nuevo_usuario.es_admin = True
            db.session.commit()
            print(f"ADMINISTRADOR AUTO-ASIGNADO a {nuevo_usuario.email}")

        login_user(nuevo_usuario)
        flash('¡Bienvenido! Hemos creado tu cuenta.', 'onboarding_trigger') 
        return redirect(url_for('main.home'))
    return render_template('registro.html', title='Registro', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        identifier = form.email.data.strip()
        password = form.password.data
        
        usuario = Usuario.query.filter(or_(Usuario.nombre == identifier, Usuario.email == identifier.lower())).first()
        if usuario and usuario.password_hash == 'OAUTH_NO_PASSWORD':
            flash('Esa cuenta fue creada con Google. Por favor, utiliza el botón "Iniciar Sesión con Google".', 'info')
            return redirect(url_for('auth.login'))
        if usuario and usuario.check_password(password):
            login_user(usuario, remember=form.remember.data)
            next_page = request.args.get('next')
            if not is_safe_url(next_page):
                return abort(400)
            flash('¡Has iniciado sesión con éxito!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('main.home'))
        else:
            flash('Inicio de sesión fallido. Comprueba tu email/usuario y contraseña.', 'danger')
    return render_template('login.html', title='Iniciar Sesión', form=form)

@auth_bp.route('/logout')
def logout():
    logout_user()
    flash('Has cerrado la sesión con éxito.', 'success')
    return redirect(url_for('main.home'))

# --- INICIO: LÓGICA MANUAL PARA GOOGLE OAUTH CORREGIDA ---

@auth_bp.route('/login/google')
def google_login():
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    
    # CONSTRUCCIÓN MANUAL de la URL de redirección con el host de Codespaces
    REDIRECT_URI = f'{CODESPACE_HOST}/auth/login/google/callback'
    
    # Guardamos el host en la sesión (por si acaso), aunque no es estrictamente necesario aquí
    # ya que CODESPACE_HOST es una constante global.
    session['codespace_host'] = CODESPACE_HOST 
    
    # Construir la URL de autorización de Google manualmente
    authorization_url = (
        'https://accounts.google.com/o/oauth2/v2/auth?'
        'response_type=code&'
        f'client_id={GOOGLE_CLIENT_ID}&'
        f'redirect_uri={REDIRECT_URI}&'
        'scope=openid%20email%20profile'
    )
    return redirect(authorization_url)

@auth_bp.route('/login/google/callback')
def google_callback():
    code = request.args.get('code')
    
    # Recuperamos la URL de redirección para usarla en el intercambio de tokens
    REDIRECT_URI = f'{CODESPACE_HOST}/auth/login/google/callback'
    
    # Limpiamos la sesión
    session.pop('codespace_host', None)
    
    if not code:
        flash('Error de autenticación. No se recibió el código de autorización.', 'danger')
        return redirect(url_for('auth.login'))

    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')

    # Intercambiar el código por un token de acceso
    token_url = 'https://oauth2.googleapis.com/token'
    token_data = {
        'code': code,
        'client_id': GOOGLE_CLIENT_ID,
        'client_secret': GOOGLE_CLIENT_SECRET,
        'redirect_uri': REDIRECT_URI, # Usamos la URI forzada
        'grant_type': 'authorization_code'
    }
    token_response = requests.post(token_url, data=token_data)
    token_json = token_response.json()

    if 'access_token' not in token_json:
        # Aquí también puede fallar si la REDIRECT_URI no coincide
        print(f"Error al obtener token: {token_json}")
        flash('No se pudo obtener el token de acceso de Google. Revisa tus claves y que la URI de redirección coincida.', 'danger')
        return redirect(url_for('auth.login'))

    # Usar el token para obtener la información del usuario
    userinfo_url = 'https://www.googleapis.com/oauth2/v1/userinfo'
    headers = {'Authorization': f'Bearer {token_json["access_token"]}'}
    userinfo_response = requests.get(userinfo_url, headers=headers)
    user_info = userinfo_response.json()

    if not user_info.get('email'):
        flash('No se pudo obtener la información del usuario de Google.', 'danger')
        return redirect(url_for('auth.login'))

    usuario = Usuario.query.filter_by(email=user_info['email']).first()
    
    if not usuario:
        usuario = Usuario(
            email=user_info['email'],
            nombre=user_info.get('name', 'Usuario de Google'),
            password_hash='OAUTH_NO_PASSWORD'   # Contraseña no necesaria
        )
        db.session.add(usuario)
        db.session.commit()
        
        admin_email = os.getenv('ADMIN_EMAIL')
        if admin_email and usuario.email == admin_email:
            usuario.es_admin = True
            db.session.commit()
            print(f"ADMINISTRADOR (vía Google) AUTO-ASIGNADO a {usuario.email}")

        login_user(usuario)
        return redirect(url_for('auth.elegir_objetivo'))

    login_user(usuario)
    if not usuario.objetivo_principal:
        return redirect(url_for('auth.elegir_objetivo'))
    
    flash('¡Has iniciado sesión con éxito con tu cuenta de Google!', 'success')
    return redirect(url_for('main.home'))

# --- FIN: LÓGICA MANUAL PARA GOOGLE OAUTH CORREGIDA ---

@auth_bp.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = Usuario.query.filter_by(email=form.email.data.lower()).first()
        if user:
            send_reset_email(user)
        flash('Si existe una cuenta con ese email, se ha enviado un correo con las instrucciones para restablecer la contraseña.', 'info')
        return redirect(url_for('auth.login'))
    return render_template('reset_request.html', title='Restablecer Contraseña', form=form)

@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    user = Usuario.verify_reset_token(token)
    if user is None:
        flash('El token no es válido o ha expirado.', 'warning')
        return redirect(url_for('auth.reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.password = form.password.data
        db.session.commit()
        flash('Tu contraseña ha sido actualizada. Ya puedes iniciar sesión.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('reset_token.html', title='Restablecer Contraseña', form=form)

@auth_bp.route('/elegir-objetivo', methods=['GET', 'POST'])
@login_required
def elegir_objetivo():
    if current_user.objetivo_principal:
        return redirect(url_for('main.home'))

    form = ObjetivoForm()
    if form.validate_on_submit():
        current_user.objetivo_principal = form.objetivo_principal.data
        db.session.commit()
        flash('¡Perfecto! Hemos guardado tu objetivo.', 'onboarding_trigger')
        return redirect(url_for('main.home'))
        
    return render_template('elegir_objetivo.html', title='Elige tu Objetivo', form=form)

@auth_bp.route('/marcar_tour_visto', methods=['POST'])
@login_required
def marcar_tour_visto():
    current_user.ha_visto_tour = True
    db.session.commit()
    return '', 204
