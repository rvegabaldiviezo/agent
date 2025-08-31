import datetime
from zoneinfo import ZoneInfo
from typing import Optional
from google.adk.agents import Agent
import psycopg2
import psycopg2.extras

# Conexión a Postgres (el host será "db" porque así lo definimos en docker-compose)
def get_connection():
    return psycopg2.connect(
        dbname="finanzas",
        user="postgres",
        password="postgres",
        host="db",
        port="5432"
    )

# ---------------- TOOLS ---------------- #

def add_transaction(tipo: str, monto: float, fecha: str, descripcion: str, contraparte: Optional[str] = None) -> dict:
    """
    Agrega una transacción a la base de datos.
    
    Args:
        tipo (str): ingreso, gasto o prestamo.
        monto (float): cantidad de dinero.
        fecha (str): fecha en formato YYYY-MM-DD.
        descripcion (str): contexto de la operación.
        contraparte (str, optional): persona o entidad relacionada.
    """
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """
            INSERT INTO transacciones (tipo, monto, fecha, descripcion, contraparte)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id;
            """,
            (tipo, monto, fecha, descripcion, contraparte)
        )
        conn.commit()
        trans_id = cur.fetchone()["id"]
        cur.close()
        conn.close()
        return {"status": "success", "message": f"Transacción registrada con ID {trans_id}"}
    except Exception as e:
        return {"status": "error", "error_message": str(e)}


def get_balance() -> dict:
    """Devuelve el balance actual (ingresos - gastos - préstamos)."""
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """
            SELECT
                SUM(CASE WHEN tipo = 'ingreso' THEN monto ELSE 0 END) -
                SUM(CASE WHEN tipo IN ('gasto','prestamo') THEN monto ELSE 0 END) AS balance
            FROM transacciones;
            """
        )
        balance = cur.fetchone()["balance"] or 0
        cur.close()
        conn.close()
        return {"status": "success", "balance": balance}
    except Exception as e:
        return {"status": "error", "error_message": str(e)}


def list_transactions(limit: int = 10) -> dict:
    """Lista las últimas transacciones."""
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT * FROM transacciones ORDER BY fecha DESC, id DESC LIMIT %s;",
            (limit,)
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return {"status": "success", "transactions": rows}
    except Exception as e:
        return {"status": "error", "error_message": str(e)}


# ---------------- AGENTE ---------------- #

root_agent = Agent(
    name="finance_agent",
    model="gemini-2.0-flash",
    description="Agente para registrar y consultar ingresos, gastos y préstamos personales.",
    instruction=(
        "Siempre que el usuario indique un movimiento de dinero (gasto, ingreso o préstamo), "
        "pregunta por el monto, fecha y descripción antes de registrar. "
        "Si es un préstamo, también pregunta a quién. "
        "El agente debe persistir todo en la base de datos."
    ),
    tools=[add_transaction, get_balance, list_transactions],
)
