CREATE TABLE IF NOT EXISTS transacciones (
    id SERIAL PRIMARY KEY,
    tipo VARCHAR(20) NOT NULL,
    monto NUMERIC(12,2) NOT NULL,
    fecha DATE NOT NULL,
    descripcion TEXT,
    contraparte VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);