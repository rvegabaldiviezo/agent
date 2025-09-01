from google.adk.agents import Agent
import psycopg2
import psycopg2.extras
from typing import Optional
import decimal
import datetime

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
        cur = conn.cursor()
        
        cur.execute(
            """
            INSERT INTO transacciones (tipo, monto, fecha, descripcion, contraparte)
            VALUES (%s, %s, %s, %s, %s) RETURNING id;
            """,
            (tipo, monto, fecha, descripcion, contraparte)
        )
        
        transaction_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        
        return {
            "status": "success",
            "message": f"Transacción de {tipo} registrada exitosamente",
            "transaction_id": transaction_id,
            "monto": monto,
            "fecha": fecha
        }
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


    
def list_transactions(limit: Optional[int] = None) -> dict:
    """
    Lista hasta 100 transacciones más recientes por defecto.
    Si limit es None, devuelve hasta 100 transacciones.
    Si limit > 100, devuelve solo 100 y puede avisar al usuario.
    """
    max_limit = 100
    if limit is None or limit <= 0 or limit > max_limit:
        limit = max_limit

    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT * FROM transacciones ORDER BY fecha DESC, id DESC LIMIT %s;",
            (limit,)
        )
        rows = cur.fetchall()
        # Convertir Decimal a float y date a string
        for row in rows:
            for k, v in row.items():
                if isinstance(v, decimal.Decimal):
                    row[k] = float(v)
                elif isinstance(v, (datetime.date, datetime.datetime)):
                    row[k] = v.isoformat()
        cur.close()
        conn.close()
        result = {"status": "success", "transactions": rows}
        if len(rows) == max_limit:
            result["message"] = "Se muestran solo las primeras 100 transacciones. Si necesitas ver más, indícalo."
        return result
    except Exception as e:
        return {"status": "error", "error_message": str(e)}
    


# Tool para obtener la fecha actual
def get_today_date() -> dict:
    """
    Devuelve la fecha de hoy en formato YYYY-MM-DD
    """
    today = datetime.datetime.now().date()
    return {
        "status": "success",
        "today": today.isoformat()
    }


# ---------------- AGENTE ---------------- #

root_agent = Agent(
    name="finance_agent",
    model="gemini-2.0-flash",
    description="Agente para registrar y consultar ingresos, gastos y préstamos personales.",
    instruction=(
        "Siempre que el usuario indique un movimiento de dinero (gasto, ingreso o préstamo), "
        "pregunta por el monto, fecha y descripción antes de registrar. "
        "Si es un préstamo, también pregunta a quién. "
        "El agente debe persistir todo en la base de datos. "
        "Al listar transacciones, muestra hasta 100 automáticamente sin preguntar. Si hay más de 100, pregunta si el usuario quiere ver más. "
        "El agente sabe la fecha de hoy porque tiene el tool get_today_date."
    ),
    tools=[add_transaction, get_balance, list_transactions, get_today_date],
)