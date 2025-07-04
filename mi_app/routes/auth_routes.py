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
        # Usamos el método que creamos en el modelo para manejar la contraseña
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

    # Corregido el nombre de la variable de 'forma' a 'form'
    form = LoginForm()

    if form.validate_on_submit():
        usuario = Usuario.query.filter_by(email=form.email.data).first()

        # Usamos el método que creamos en el modelo para verificar la contraseña
        if usuario and usuario.check_password(form.password.data):
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
    """
    Redirige al usuario a la página de inicio de sesión de Google.
    """
    # Creamos la URL a la que Google debe devolver al usuario después de loguearse
    redirect_uri = url_for('auth.google_callback', _external=True)
    # Usamos authlib para generar y redirigir a la URL de autorización de Google
    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.route('/login/google/callback')
def google_callback():
    """
    Gestiona la respuesta de Google después de que el usuario se loguea.
    """
    try:
        # Obtenemos el token de acceso de Google
        token = oauth.google.authorize_access_token()
        # Usamos el token para obtener la información del perfil del usuario
        user_info = oauth.google.parse_id_token(token)
    except Exception as e:
        flash('Hubo un error al intentar iniciar sesión con Google. Por favor, inténtalo de nuevo.', 'danger')
        return redirect(url_for('auth.login'))

    # Comprobamos si el usuario ya existe en nuestra base de datos por su email
    usuario = Usuario.query.filter_by(email=user_info['email']).first()

    # Si el usuario no existe, lo creamos
    if not usuario:
        usuario = Usuario(
            email=user_info['email'],
            nombre=user_info.get('name', 'Usuario de Google')
        )
        # Como no tenemos su contraseña, le asignamos una aleatoria y segura.
        # El usuario no la necesitará, ya que siempre entrará a través de Google.
        random_password = secrets.token_urlsafe(16)
        usuario.set_password(random_password)

        db.session.add(usuario)
        db.session.commit()
        flash('¡Cuenta creada con éxito a través de Google!', 'success')

    # Iniciamos sesión con el usuario (sea el existente o el recién creado)
    login_user(usuario)
    flash('¡Has iniciado sesión con éxito con tu cuenta de Google!', 'success')
    return redirect(url_for('main.home'))