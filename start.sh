#!/bin/bash
set -o errexit
set -o xtrace

echo "--- Iniciando script de arranque ---"

echo "-> Ejecutando migración de la base de datos..."
flask db upgrade

echo "-> Migración finalizada. Arrancando el servidor Gunicorn..."
gunicorn "mi_app:create_app()"