from dotenv import load_dotenv
import os
import psycopg2

# Cargar variables de entorno
load_dotenv()

# Conectar a la base de datos
cn = psycopg2.connect(
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    database=os.getenv("DB_NAME")
)

if __name__ == "__main__":
    try:
        with cn.cursor() as cursor:
            cursor.execute("SELECT version();")
            db_version = cursor.fetchone()
            print(f"Connected to PostgreSQL. Version: {db_version}")
    except Exception as e:
        print(f"Error connecting to database: {e}")
    finally:
        if 'cn' in locals():
            cn.close()