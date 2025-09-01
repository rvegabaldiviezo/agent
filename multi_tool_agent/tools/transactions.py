from typing import Optional
import psycopg2
import psycopg2.extras
import decimal
import datetime
from .agent_db import get_connection

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
    

