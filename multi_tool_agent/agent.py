from google.adk.agents import Agent
from .tools.transactions import add_transaction, list_transactions
from .tools.balance import get_balance
from .tools.date_tools import get_today_date
from .tools.date_tools import get_weather_and_time

    
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
        "El agente sabe la fecha de hoy porque tiene el tool get_today_date."
        "El agente puede obtener el clima y la hora local usando el tool get_weather_and_time."

        "Puede calcular balances, listar transacciones, registrar ingresos/gastos/préstamos, mostrar la fecha de hoy y generar una imagen de la tabla de transacciones. "
        
        "Cuando le respondas la primera vez al user, ademas le vas a informar al usuario sobre tus capacidades de agente. Ejemplo (Recuerda agregar antes un salto de linea): '\n Recuerda que puedo:\n - registrar tus ingresos, gastos y préstamos.\n - calcular el balance actual.\n - listar las transacciones recientes (por defecto texto). También puedo generar una imagen de la tabla de transacciones agrupadas por categoría.\n - mostrar la fecha de hoy.\n\n¿En qué te puedo ayudar?'"
    ),
    tools=[
        add_transaction, 
        get_balance, 
        list_transactions, 
        get_today_date, 
        get_weather_and_time,
    ],
)