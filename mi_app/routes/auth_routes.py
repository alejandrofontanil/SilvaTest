from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from mi_app import db, bcrypt, oauth
from mi_app.models import Usuario
from mi_app.forms import RegistrationForm, LoginForm
import secrets

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        nuevo_usuario = Usuario(nombre=form.nombre.data, email=form.email.data)
        nuevo_usuario.set_password(form.password.data)
        db.session.add(nuevo_usuario)
        db.session.commit()
        flash('¡Tu cuenta ha sido creada! Ya puedes iniciar sesión.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('registro.html', title='Registro', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        email_o_usuario = form.email.data.lower().strip()
        password = form.password.data

        # --- CASO ESPECIAL PARA EL USUARIO INVITADO ---
        if email_o_usuario == 'invitado' and password == 'invitado':
            usuario_invitado = Usuario.query.filter_by(nombre='Invitado').first()
            if usuario_invitado:
                login_user(usuario_invitado, remember=False)
                flash('Has iniciado sesión como Invitado.', 'info')
                return redirect(url_for('main.home'))
            else:
                flash('La cuenta de invitado no está configurada. Contacta al administrador.', 'danger')
                return redirect(url_for('auth.login'))
        # --- FIN DEL CASO ESPECIAL ---

        # Lógica normal para usuarios reales
        usuario = Usuario.query.filter_by(email=email_o_usuario).first()
        if usuario and usuario.check_password(password):
            login_user(usuario, remember=form.remember.data)
            next_page = request.args.get('next')
            flash('¡Has iniciado sesión con éxito!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('main.home'))
        else:
            flash('Inicio de sesión fallido. Por favor, comprueba tu email y contraseña.', 'danger')
            
    return render_template('login.html', title='Iniciar Sesión', form=form)

@auth_bp.route('/logout')
def logout():
    logout_user()
    flash('Has cerrado la sesión con éxito.', 'success')
    return redirect(url_for('main.home'))

@auth_bp.route('/login/google')
def google_login():
    redirect_uri = url_for('auth.google_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@auth_bp.route('/login/google/callback')
def google_callback():
    try:
        token = oauth.google.authorize_access_token()
        user_info = oauth.google.userinfo(token=token)
    except Exception as e:
        print(f"Error en el callback de Google: {e}")
        flash('Hubo un error al intentar iniciar sesión con Google. Por favor, inténtalo de nuevo.', 'danger')
        return redirect(url_for('auth.login'))
        
    usuario = Usuario.query.filter_by(email=user_info['email']).first()
    if not usuario:
        usuario = Usuario(
            email=user_info['email'],
            nombre=user_info.get('name', 'Usuario de Google')
        )
        random_password = secrets.token_urlsafe(16)
        usuario.set_password(random_password)
        db.session.add(usuario)
        db.session.commit()
        flash('¡Cuenta creada con éxito a través de Google!', 'success')
        
    login_user(usuario)
    flash('¡Has iniciado sesión con éxito con tu cuenta de Google!', 'success')
    return redirect(url_for('main.home'))