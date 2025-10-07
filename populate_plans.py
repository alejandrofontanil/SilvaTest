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
        return float(str(valor).replace(',', '.').replace('%', '').strip())
    except (ValueError, TypeError):
        return None

def limpiar_km(valor):
    """Convierte '5.4 km' a 5.4"""
    try:
        match = re.search(r'[\d.]+', str(valor))
        return float(match.group(0)) if match else None
    except (ValueError, TypeError):
        return None

def poblar_plan(sheet_name, plan_nombre):
    print(f"--- Procesando '{plan_nombre}' desde la hoja '{sheet_name}' ---")
    
    plan_existente = PlanFisico.query.filter_by(nombre=plan_nombre).first()
    if plan_existente:
        print(f"El plan '{plan_nombre}' ya existe. Saltando...")
        return

    try:
        df = pd.read_excel(EXCEL_FILE, sheet_name=sheet_name, header=3, usecols="A:H")
        
        df.columns = [
            'progreso', 'semana', 'dia1', 'sensacion1', 'dia2', 'sensacion2', 
            'carga_semanal_km', 'zona_ritmo'
        ]

        nuevo_plan = PlanFisico(nombre=plan_nombre)
        db.session.add(nuevo_plan)
        
        for index, row in df.iterrows():
            # Si la celda de la semana está vacía, la ignoramos
            if pd.isna(row['semana']):
                continue

            # --- LÍNEA AÑADIDA ---
            # Si la celda de la semana no es un número (ej: "..."), la ignoramos
            if not str(row['semana']).replace('.0', '').isdigit():
                continue
            # --- FIN DE LA LÍNEA AÑADIDA ---

            nueva_semana = SemanaPlan(
                plan=nuevo_plan,
                numero_semana=int(row['semana']),
                progreso_pct=limpiar_progreso(row['progreso']),
                dia1_desc=str(row['dia1']),
                dia2_desc=str(row['dia2']),
                sensacion=str(row['sensacion2']),
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

