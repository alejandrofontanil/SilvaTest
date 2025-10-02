from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, RadioField, SelectField, BooleanField, IntegerField, SelectMultipleField, DateField
from wtforms.widgets import ListWidget, CheckboxInput
from wtforms.validators import DataRequired, Length, Email, EqualTo, Optional, ValidationError
from wtforms_sqlalchemy.fields import QuerySelectField
from .models import Bloque, Tema, Usuario, Convocatoria

def bloques_query():
    return Bloque.query

def temas_query():
    return Tema.query

def convocatorias_publicas():
    return Convocatoria.query.filter_by(es_publica=True).order_by(Convocatoria.nombre)

class ConvocatoriaForm(FlaskForm):
    nombre = StringField('Nombre de la Convocatoria', validators=[DataRequired(), Length(min=5, max=200)])
    es_publica = BooleanField('¿Es una convocatoria pública?')
    es_premium = BooleanField('¿Es contenido de pago (Premium)?')
    submit = SubmitField('Guardar Convocatoria')

class BloqueForm(FlaskForm):
    nombre = StringField('Nombre del Bloque',
                         validators=[DataRequired(),
                                     Length(min=3, max=200)])
    submit = SubmitField('Guardar Bloque')

class TemaForm(FlaskForm):
    bloque = QuerySelectField('Bloque al que pertenece',
                              query_factory=bloques_query,
                              get_label='nombre',
                              allow_blank=False,
                              validators=[DataRequired()])
    nombre = StringField('Nombre del Tema/Subtema',
                       validators=[DataRequired(),
                                   Length(min=3, max=200)])
    parent = QuerySelectField(
        'Tema Padre (Opcional, para subtemas)',
        query_factory=temas_query,
        get_label='nombre',
        allow_blank=True,
        blank_text='-- Ninguno (Es un Tema Principal) --',
        validators=[Optional()])
    
    pdf_url = StringField('URL del PDF de Apoyo (Opcional)')
    
    es_simulacro = BooleanField('¿Es un Simulacro de Examen?')
    tiempo_limite_minutos = IntegerField('Tiempo Límite (en minutos)',
                                         validators=[Optional()])
    submit = SubmitField('Guardar Tema')

class PermisosForm(FlaskForm):
    convocatorias = SelectMultipleField('Convocatorias con Acceso',
                                        coerce=int,
                                        widget=ListWidget(prefix_label=False),
                                        option_widget=CheckboxInput())
    fecha_expiracion = DateField(
        'Fecha de Expiración (Opcional, dejar en blanco para acceso permanente)',
        format='%Y-%m-%d',
        validators=[Optional()])
    submit = SubmitField('Guardar Permisos')

class RegistrationForm(FlaskForm):
    nombre = StringField('Nombre',
                       validators=[DataRequired(),
                                   Length(min=2, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    
    password = PasswordField('Contraseña', validators=[DataRequired(), Length(min=8, message='La contraseña debe tener al menos 8 caracteres.')])
    
    confirm_password = PasswordField(
        'Confirmar Contraseña',
        validators=[
            DataRequired(),
            EqualTo('password', message='Las contraseñas deben coincidir.')
        ])

    objetivo_principal = QuerySelectField(
        '¿Cuál es tu objetivo principal?',
        query_factory=convocatorias_publicas,
        get_label='nombre',
        allow_blank=True,
        blank_text='-- Elige una opción --',
        validators=[DataRequired(message="Por favor, selecciona tu objetivo.")]
    )

    # recaptcha = RecaptchaField()  # <-- LÍNEA COMENTADA PARA EVITAR EL ERROR
    submit = SubmitField('Crear Cuenta')

    def validate_email(self, email):
        usuario = Usuario.query.filter_by(email=email.data.lower()).first()
        if usuario:
            raise ValidationError('Ya existe una cuenta con ese correo electrónico. Por favor, inicia sesión o utiliza otro email.')


class LoginForm(FlaskForm):
    email = StringField('Email o Nombre de Usuario', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    remember = BooleanField('Recuérdame')
    submit = SubmitField('Iniciar Sesión')

class PreguntaForm(FlaskForm):
    texto = TextAreaField('Enunciado de la Pregunta', validators=[DataRequired()])
    imagen = FileField('Subir Imagen (Opcional)', validators=[FileAllowed(['jpg', 'png', 'jpeg'], '¡Solo imágenes!')])
    dificultad = SelectField('Dificultad', choices=[('Fácil', 'Fácil'), ('Media', 'Media'), ('Difícil', 'Difícil')], validators=[DataRequired()])
    tipo_pregunta = SelectField('Tipo de Pregunta', choices=[('opcion_multiple', 'Opción Múltiple'), ('respuesta_texto', 'Respuesta de Texto (Visu)')], validators=[DataRequired()])
    respuesta_correcta_texto = StringField('Respuesta Correcta de Texto (si aplica)', validators=[Optional()])
    respuesta1_texto = StringField('Opción A', validators=[Optional(), Length(max=500)])
    respuesta2_texto = StringField('Opción B', validators=[Optional(), Length(max=500)])
    respuesta3_texto = StringField('Opción C', validators=[Optional(), Length(max=500)])
    respuesta4_texto = StringField('Opción D', validators=[Optional(), Length(max=500)])
    respuesta_correcta = RadioField('Marca la Opción Correcta', choices=[('1', 'A'), ('2', 'B'), ('3', 'C'), ('4', 'D')], validators=[Optional()])
    retroalimentacion = TextAreaField('Pista para el usuario (opcional)')
    submit = SubmitField('Guardar Pregunta')

class NotaForm(FlaskForm):
    texto = TextAreaField('Texto de la Nota', validators=[DataRequired()])
    submit_nota = SubmitField('Añadir Nota')

class GoogleSheetImportForm(FlaskForm):
    sheet_url = StringField('URL de la Hoja de Google Sheets', validators=[DataRequired()])
    submit = SubmitField('Importar Preguntas')

class FiltroCuentaForm(FlaskForm):
    convocatoria = SelectField('Filtrar por Convocatoria', coerce=int)
    submit = SubmitField('Filtrar')

class ObjetivoForm(FlaskForm):
    objetivo_principal = QuerySelectField(
        'Para personalizar tu experiencia, por favor, elige tu objetivo principal:',
        query_factory=convocatorias_publicas,
        get_label='nombre',
        allow_blank=False,
        validators=[DataRequired(message="Por favor, selecciona tu objetivo.")]
    )
    submit = SubmitField('Guardar y Continuar')


class DashboardPreferencesForm(FlaskForm):
    mostrar_grafico_evolucion = BooleanField('Mostrar gráfico de evolución de notas', default=True)
    mostrar_rendimiento_bloque = BooleanField('Mostrar gráfico de rendimiento por bloque', default=True)
    mostrar_calendario_actividad = BooleanField('Mostrar calendario de actividad', default=True)
    submit = SubmitField('Guardar Preferencias del Panel')

class UploadContextoForm(FlaskForm):
    documento = FileField('Documento de Contexto (PDF o TXT)', validators=[
        FileRequired(),
        FileAllowed(['pdf', 'txt'], '¡Solo se permiten archivos PDF y TXT!')
    ])
    submit = SubmitField('Subir y Guardar Documento')

class ObjetivoFechaForm(FlaskForm):
    objetivo_fecha = DateField('Fecha de tu Examen u Objetivo', format='%Y-%m-%d', validators=[DataRequired()])
    submit = SubmitField('Guardar Fecha')

# --- INICIO: FORMULARIOS AÑADIDOS PARA RESETEAR CONTRASEÑA ---

class RequestResetForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Solicitar Restablecimiento')

    def validate_email(self, email):
        user = Usuario.query.filter_by(email=email.data.lower()).first()
        if user is None:
            # No revelamos si el usuario existe o no por seguridad
            pass

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Nueva Contraseña', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirmar Nueva Contraseña', validators=[DataRequired(), EqualTo('password', message='Las contraseñas deben coincidir.')])
    submit = SubmitField('Restablecer Contraseña')

# --- FIN: FORMULARIOS AÑADIDOS ---

