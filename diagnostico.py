import os
import json
import gspread
from google.oauth2.service_account import Credentials
from mi_app import create_app, db
from mi_app.models import Tema

app = create_app()

with app.app_context():
    print("--- DIAGNÓSTICO DE IMPORTACIÓN ---")
    print("\nPASO 1: Comprobando los temas en tu base de datos...")

    todos_los_temas = Tema.query.order_by(Tema.id).all()

    if not todos_los_temas:
        print("AVISO: No se ha encontrado ningún tema en tu base de datos.")
    else:
        print("Estos son los IDs de los temas que existen AHORA MISMO en tu base de datos:")
        for tema in todos_los_temas:
            print(f"  -> ID: {tema.id}, Nombre: {tema.nombre}")

    print("\n--------------------------------------------------")
    print("\nPASO 2: Intentando leer tu Google Sheet...")

    try:
        sheet_url = input("Por favor, pega aquí la URL de tu Google Sheet y pulsa Enter: ")

        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds_json_str = os.environ.get('GOOGLE_CREDS_JSON')
        if not creds_json_str:
            print("ERROR CRÍTICO: No se ha encontrado el Secret 'GOOGLE_CREDS_JSON'.")
        else:
            creds_json = json.loads(creds_json_str)
            creds = Credentials.from_service_account_info(creds_json, scopes=scopes)
            client = gspread.authorize(creds)

            spreadsheet = client.open_by_url(sheet_url)
            sheet = spreadsheet.get_worksheet(0)

            print("\n¡Conexión con Google Sheets exitosa! Estas son las primeras 5 filas que estoy leyendo:")

            todos_los_registros = sheet.get_all_records()
            primeras_filas = todos_los_registros[:5] 

            if not primeras_filas:
                print("AVISO: La hoja parece estar vacía o no tiene encabezados en la primera fila.")
            else:
                for i, row in enumerate(primeras_filas):
                    print(f"\n  Fila {i+2} de la hoja:")
                    print(f"    - tema_id leído: {row.get('tema_id')}")
                    print(f"    - enunciado leído: {row.get('enunciado')}")

    except gspread.exceptions.SpreadsheetNotFound:
        print("\nERROR: No se ha encontrado la hoja de cálculo. Revisa la URL y asegúrate de que la has compartido.")
    except Exception as e:
        print(f"\nHa ocurrido un error inesperado: {e}")

    print("\n--- FIN DEL DIAGNÓSTICO ---")