from .agent_db import get_connection
import psycopg2.extras

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

