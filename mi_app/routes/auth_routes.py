from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_user, logout_user, current_user, login_required
from mi_app import db, bcrypt, oauth
from mi_app.models import Usuario
from mi_app.forms import RegistrationForm, LoginForm, ObjetivoForm # Asumiendo que crearás este formulario
from urllib.parse import urlparse, urljoin
from sqlalchemy import or_

auth_bp = Blueprint('auth', __name__,
                    template_folder='../templates/auth',
                    url_prefix='/auth')

def is_safe_url(target):
    # ... (sin cambios)
    if not target:
        return True
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

@auth_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    # ... (sin cambios)
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
        login_user(nuevo_usuario)
        flash('¡Bienvenido! Hemos creado tu cuenta.', 'onboarding_trigger') 
        return redirect(url_for('main.home'))
    return render_template('registro.html', title='Registro', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # ... (sin cambios)
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        identifier = form.email.data.strip()
        password = form.password.data
        if identifier.lower() == 'invitado' and password == '13579':
            usuario_invitado = Usuario.query.filter_by(nombre='Invitado').first()
            if usuario_invitado:
                login_user(usuario_invitado, remember=False)
                flash('Has iniciado sesión como Invitado.', 'info')
                return redirect(url_for('main.home'))
            else:
                flash('La cuenta de invitado no está configurada.', 'danger')
                return redirect(url_for('auth.login'))
        
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
    # ... (sin cambios)
    logout_user()
    flash('Has cerrado la sesión con éxito.', 'success')
    return redirect(url_for('main.home'))

@auth_bp.route('/login/google')
def google_login():
    # ... (sin cambios)
    redirect_uri = url_for('auth.google_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@auth_bp.route('/login/google/callback')
def google_callback():
    try:
        token = oauth.google.authorize_access_token()
        user_info = token.get('userinfo')
        if not user_info:
            user_info = oauth.google.userinfo(token=token)
    except Exception as e:
        flash('Hubo un error al intentar iniciar sesión con Google.', 'danger')
        return redirect(url_for('auth.login'))
        
    usuario = Usuario.query.filter_by(email=user_info['email']).first()
    
    # --- LÓGICA MODIFICADA PARA USUARIOS DE GOOGLE ---
    if not usuario:
        # Si el usuario NO existe, lo creamos
        usuario = Usuario(
            email=user_info['email'],
            nombre=user_info.get('name', 'Usuario de Google'),
            password_hash = 'OAUTH_NO_PASSWORD'
        )
        db.session.add(usuario)
        db.session.commit()
        login_user(usuario)
        # Lo redirigimos para que elija su objetivo
        return redirect(url_for('auth.elegir_objetivo'))

    # Si el usuario ya existe, comprobamos si tiene un objetivo
    login_user(usuario)
    if not usuario.objetivo_principal:
        # Si no tiene objetivo, también lo mandamos a elegirlo
        return redirect(url_for('auth.elegir_objetivo'))
    
    flash('¡Has iniciado sesión con éxito con tu cuenta de Google!', 'success')
    return redirect(url_for('main.home'))

# --- NUEVA RUTA PARA QUE USUARIOS DE GOOGLE ELIJAN SU OBJETIVO ---
@auth_bp.route('/elegir-objetivo', methods=['GET', 'POST'])
@login_required
def elegir_objetivo():
    # Si el usuario ya tiene un objetivo, no debería estar aquí
    if current_user.objetivo_principal:
        return redirect(url_for('main.home'))

    from mi_app.forms import ObjetivoForm # Necesitaremos crear este formulario
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
    # ... (sin cambios)
    current_user.ha_visto_tour = True
    db.session.commit()
    return '', 204