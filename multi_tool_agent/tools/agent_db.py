# agent_db.py
import psycopg2
import os

# Conexión a Postgres (el host será "db" porque así lo definimos en docker-compose)
def get_connection():
    # Lee la URL de la base de datos desde una variable de entorno.
    # Si no existe, usa un valor por defecto (útil para pruebas locales fuera de Docker).
    database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/finanzas")
    return psycopg2.connect(database_url)