#!/bin/bash
# Navega al directorio donde se encuentra el script
cd "$(dirname "$0")"

# Instala las dependencias
echo "Instalando dependencias..."
pip3 install -r requirements.txt

# Inicia la aplicación
echo "Iniciando servidor Flask... Puedes acceder en http://127.0.0.1:5000"
python3 app.py
