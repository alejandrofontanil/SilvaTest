from flask_wtf import FlaskForm, RecaptchaField
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, RadioField, SelectField, BooleanField, IntegerField, SelectMultipleField, DateField
from wtforms.widgets import ListWidget, CheckboxInput
from wtforms.validators import DataRequired, Length, Email, EqualTo, Optional, ValidationError
from wtforms_sqlalchemy.fields import QuerySelectField
from .models import Bloque, Tema

def bloques_query():
    return Bloque.query

def temas_query():
    return Tema.query

class ConvocatoriaForm(FlaskForm):
    nombre = StringField('Nombre de la Convocatoria', validators=[DataRequired(), Length(min=5, max=200)])
    es_publica = BooleanField('¿Es una convocatoria pública? (Si no se marca, solo será visible para administradores)', default=True)
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
                                   Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    
    # --- LÍNEA MODIFICADA CON LA MEJORA ---
    password = PasswordField('Contraseña', validators=[DataRequired(), Length(min=8, message='La contraseña debe tener al menos 8 caracteres.')])
    
    confirm_password = PasswordField(
        'Confirmar Contraseña',
        validators=[
            DataRequired(),
            EqualTo('password', message='Las contraseñas deben coincidir.')
        ])
    recaptcha = RecaptchaField()
    submit = SubmitField('Crear Cuenta')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    remember = BooleanField('Recuérdame')
    submit = SubmitField('Iniciar Sesión')

class PreguntaForm(FlaskForm):
    texto = TextAreaField('Enunciado de la Pregunta',
                          validators=[DataRequired()])
    imagen = FileField(
        'Subir Imagen (Opcional)',
        validators=[FileAllowed(['jpg', 'png', 'jpeg'], '¡Solo imágenes!')])
    dificultad = SelectField('Dificultad',
                             choices=[('Fácil', 'Fácil'), ('Media', 'Media'),
                                      ('Difícil', 'Difícil')],
                             validators=[DataRequired()])
    tipo_pregunta = SelectField('Tipo de Pregunta',
                                  choices=[('opcion_multiple',
                                            'Opción Múltiple'),
                                           ('respuesta_texto',
                                            'Respuesta de Texto (Visu)')],
                                  validators=[DataRequired()])
    respuesta_correcta_texto = StringField(
        'Respuesta Correcta de Texto (si aplica)', validators=[Optional()])
    respuesta1_texto = StringField('Opción A',
                                 validators=[Optional(),
                                             Length(max=500)])
    respuesta2_texto = StringField('Opción B',
                                 validators=[Optional(),
                                             Length(max=500)])
    respuesta3_texto = StringField('Opción C',
                                 validators=[Optional(),
                                             Length(max=500)])
    respuesta4_texto = StringField('Opción D',
                                 validators=[Optional(),
                                             Length(max=500)])
    respuesta_correcta = RadioField('Marca la Opción Correcta',
                                  choices=[('1', 'A'), ('2', 'B'),
                                           ('3', 'C'), ('4', 'D')],
                                  validators=[Optional()])
    retroalimentacion = TextAreaField('Pista para el usuario (opcional)')
    submit = SubmitField('Guardar Pregunta')

class NotaForm(FlaskForm):
    texto = TextAreaField('Texto de la Nota', validators=[DataRequired()])
    submit_nota = SubmitField('Añadir Nota')

class GoogleSheetImportForm(FlaskForm):
    sheet_url = StringField('URL de la Hoja de Google Sheets',
                              validators=[DataRequired()])
    submit = SubmitField('Importar Preguntas')

class FiltroCuentaForm(FlaskForm):
    convocatoria = SelectField('Filtrar por Convocatoria', coerce=int)
    submit = SubmitField('Filtrar')