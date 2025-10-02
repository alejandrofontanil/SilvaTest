from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, current_user, login_required
import os
from mi_app import db, bcrypt
from mi_app.models import Usuario
from mi_app.forms import RegistrationForm, LoginForm, RequestResetForm, ResetPasswordForm, ObjetivoForm
from mi_app.utils import send_reset_email
from sqlalchemy import or_

# --- NUEVAS IMPORTACIONES PARA LOGIN MANUAL CON GOOGLE ---
import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
# ---------------------------------------------------------

auth_bp = Blueprint('auth', __name__, template_folder='../templates/auth')


# --- CONFIGURACIÓN PARA EL FLUJO DE GOOGLE ---
# Define los permisos que solicitaremos
SCOPES = ['https://www.googleapis.com/auth/userinfo.profile', 'https://www.googleapis.com/auth/userinfo.email', 'openid']

def get_client_config():
    """Genera la configuración del cliente OAuth a partir de las variables de entorno."""
    return {
        "web": {
            "client_id": os.environ.get('GOOGLE_CLIENT_ID'),
            "project_id": os.environ.get('GCP_PROJECT_ID'), # Asegúrate de tener esta variable en .env si la necesitas
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": os.environ.get('GOOGLE_CLIENT_SECRET'),
        }
    }
# --- FIN DE LA CONFIGURACIÓN ---


@auth_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = Usuario(nombre=form.nombre.data, email=form.email.data.lower(), password_hash=hashed_password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        # Redirigimos a elegir objetivo después del registro
        return redirect(url_for('auth.elegir_objetivo'))
    return render_template('registro.html', title='Registro', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = Usuario.query.filter_by(email=form.email.data.lower()).first()
        if user and user.password_hash == 'OAUTH_NO_PASSWORD':
            flash('Esa cuenta fue creada con Google. Por favor, utiliza el botón "Iniciar Sesión con Google".', 'info')
            return redirect(url_for('auth.login'))
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash('¡Has iniciado sesión con éxito!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('main.home'))
        else:
            flash('Inicio de sesión fallido. Comprueba tu email y contraseña.', 'danger')
    return render_template('login.html', title='Iniciar Sesión', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado la sesión.', 'info')
    return redirect(url_for('main.home'))


# --- NUEVA LÓGICA PARA EL LOGIN CON GOOGLE ---

@auth_bp.route('/google/login')
def login_google():
    """Inicia el proceso de autenticación con Google."""
    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        client_config=get_client_config(),
        scopes=SCOPES
    )
    flow.redirect_uri = url_for('auth.authorize_google', _external=True)
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    session['google_oauth_state'] = state
    return redirect(authorization_url)


@auth_bp.route('/google/auth')
def authorize_google():
    """Recibe la respuesta de Google y finaliza el proceso."""
    state = session.pop('google_oauth_state', None)
    if not state or state != request.args.get('state'):
        flash('Error de validación de estado. Inténtalo de nuevo.', 'danger')
        return redirect(url_for('auth.login'))

    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        client_config=get_client_config(),
        scopes=SCOPES,
        state=state
    )
    flow.redirect_uri = url_for('auth.authorize_google', _external=True)

    try:
        flow.fetch_token(authorization_response=request.url)
        credentials = flow.credentials
        
        user_info_service = build('oauth2', 'v2', credentials=credentials)
        user_info = user_info_service.userinfo().get().execute()
        
        email = user_info.get('email').lower()
        nombre = user_info.get('name')

        usuario = Usuario.query.filter_by(email=email).first()
        if not usuario:
            usuario = Usuario(
                email=email,
                nombre=nombre,
                password_hash='OAUTH_NO_PASSWORD' # Marcamos que no tiene contraseña
            )
            db.session.add(usuario)
            db.session.commit()
            login_user(usuario, remember=True)
            # Si es nuevo, va a elegir objetivo
            return redirect(url_for('auth.elegir_objetivo'))
        
        login_user(usuario, remember=True)
        flash('Has iniciado sesión con Google.', 'info')
        
        # Si ya tiene objetivo, va al home, si no, a elegirlo
        if not usuario.objetivo_principal:
            return redirect(url_for('auth.elegir_objetivo'))
        
        return redirect(url_for('main.home'))

    except Exception as e:
        print(f"Error durante la autenticación de Google: {e}")
        flash('Hubo un error al intentar iniciar sesión con Google. Por favor, inténtalo de nuevo.', 'danger')
        return redirect(url_for('auth.login'))

# --- FIN DE LA NUEVA LÓGICA ---


@auth_bp.route('/elegir-objetivo', methods=['GET', 'POST'])
@login_required
def elegir_objetivo():
    if current_user.objetivo_principal and not request.args.get('cambiar'):
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


@auth_bp.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = Usuario.query.filter_by(email=form.email.data).first()
        if user:
            send_reset_email(user)
        flash('Se ha enviado un correo con las instrucciones para restablecer tu contraseña, si la cuenta existe.', 'info')
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
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password_hash = hashed_password
        db.session.commit()
        flash('¡Tu contraseña ha sido actualizada! Ya puedes iniciar sesión.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('reset_token.html', title='Restablecer Contraseña', form=form)

