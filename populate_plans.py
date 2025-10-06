# populate_plans.py
import pandas as pd
from mi_app import create_app, db
from mi_app.models import PlanFisico, SemanaPlan
import re

app = create_app()
app.app_context().push()

# --- CONFIGURACIÓN ---
EXCEL_FILE = 'planes.xlsx'
PLAN_BASE_SHEET = 'Plan Base'
PLAN_EXIGENTE_SHEET = 'Plan Exigente'

def limpiar_progreso(valor):
    """Convierte '6,25%' a 6.25"""
    try:
        # Convierte comas a puntos y quita el '%'
        return float(str(valor).replace(',', '.').replace('%', '').strip())
    except (ValueError, TypeError):
        return None

def limpiar_km(valor):
    """Convierte '5.4 km' a 5.4"""
    try:
        # Usa una expresión regular para encontrar el número
        match = re.search(r'[\d.]+', str(valor))
        return float(match.group(0)) if match else None
    except (ValueError, TypeError):
        return None


def poblar_plan(sheet_name, plan_nombre):
    print(f"--- Procesando '{plan_nombre}' desde la hoja '{sheet_name}' ---")
    
    # Comprueba si el plan ya existe para no duplicarlo
    plan_existente = PlanFisico.query.filter_by(nombre=plan_nombre).first()
    if plan_existente:
        print(f"El plan '{plan_nombre}' ya existe. Saltando...")
        return

    try:
        df = pd.read_excel(EXCEL_FILE, sheet_name=sheet_name, header=3) # Asume que los datos empiezan en la fila 4
        
        # Renombramos las columnas para que sea más fácil trabajar
        df.columns = [
            'progreso', 'semana', 'dia1', 'sensacion1', 'dia2', 'sensacion2', 
            'carga_semanal_km', 'zona_ritmo'
        ]

        # Creamos el objeto del plan
        nuevo_plan = PlanFisico(nombre=plan_nombre)
        db.session.add(nuevo_plan)
        
        # Iteramos sobre cada fila (cada semana) del Excel
        for index, row in df.iterrows():
            if pd.isna(row['semana']):
                continue

            nueva_semana = SemanaPlan(
                plan=nuevo_plan,
                numero_semana=int(row['semana']),
                progreso_pct=limpiar_progreso(row['progreso']),
                dia1_desc=str(row['dia1']),
                dia2_desc=str(row['dia2']),
                sensacion=str(row['sensacion2']), # Usamos la sensación del día 2 como la general
                carga_semanal_km=limpiar_km(row['carga_semanal_km']),
                zona_ritmo=str(row['zona_ritmo'])
            )
            db.session.add(nueva_semana)
            print(f"  -> Añadida semana {int(row['semana'])} al plan '{plan_nombre}'")

        db.session.commit()
        print(f"✅ Plan '{plan_nombre}' guardado en la base de datos.")

    except Exception as e:
        print(f"❌ ERROR al procesar la hoja '{sheet_name}': {e}")
        db.session.rollback()


if __name__ == '__main__':
    with app.app_context():
        poblar_plan(PLAN_BASE_SHEET, "Plan Base")
        poblar_plan(PLAN_EXIGENTE_SHEET, "Plan Exigente")
        print("\n--- Proceso de población de datos finalizado ---")