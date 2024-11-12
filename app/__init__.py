import logging
from flask import Flask
from flask_marshmallow import Marshmallow
import os
from app.config import factory
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry._logs import set_logger_provider
from azure.monitor.opentelemetry.exporter import AzureMonitorLogExporter
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor

from opentelemetry import trace
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter

import psycopg2  # Librería para PostgreSQL
from dotenv import load_dotenv  # Librería para cargar variables de entorno

# Inicializar Marshmallow
ma = Marshmallow()

# Cargar el archivo .env
load_dotenv()

# Depuración: Verificar si las variables de entorno están cargadas correctamente
print("Depuración de variables de entorno:")
for key, value in os.environ.items():
    if "INSTRUMENTATION" in key or "CONNECTION" in key or "DB" in key:
        print(f"{key}: {value}")

# Configuración de logs y trazas (OpenTelemetry)
logger_provider = LoggerProvider()
set_logger_provider(logger_provider)

# Obtener la clave de instrumentación
instrumentation_key = os.getenv("INSTRUMENTATION_KEY")
if not instrumentation_key:
    raise ValueError("La clave de instrumentación no está configurada. Verifica las variables de entorno.")

# Configurar el exportador de logs con Azure Monitor
exporter = AzureMonitorLogExporter(connection_string=f"InstrumentationKey={instrumentation_key}")
logger_provider.add_log_record_processor(BatchLogRecordProcessor(exporter))

handler = LoggingHandler()
logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.NOTSET)

def create_app():
    # Crear la app de Flask
    app_context = os.getenv('FLASK_CONTEXT')
    app = Flask(__name__)

    # Configuración del entorno
    f = factory(app_context if app_context else 'development')
    app.config.from_object(f)

    # Configurar la conexión a PostgreSQL
    try:
        app.db_connection = psycopg2.connect(
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            database=os.getenv("DB_NAME"),
            sslmode=os.getenv("DB_SSLMODE", "require")
        )
        logger.info("Conexión a la base de datos establecida.")
    except Exception as e:
        logger.error(f"Error conectando a la base de datos: {e}")
        app.db_connection = None

    # Cerrar la conexión al finalizar la aplicación
    @app.teardown_appcontext
    def close_db_connection(exception):
        if app.db_connection:
            app.db_connection.close()
            logger.info("Conexión a la base de datos cerrada.")

    # Configurar el proveedor de trazas para OpenTelemetry
    otel_service_name = os.getenv("OTEL_SERVICE_NAME", "default-service")
    tracer_provider = TracerProvider(
        resource=Resource.create({SERVICE_NAME: otel_service_name})
    )
    trace.set_tracer_provider(tracer_provider)
    FlaskInstrumentor().instrument_app(app)
    RequestsInstrumentor().instrument()
    trace_exporter = AzureMonitorTraceExporter(
        connection_string=f"InstrumentationKey={instrumentation_key}"
    )
    trace.get_tracer_provider().add_span_processor(
        BatchSpanProcessor(trace_exporter)
    )

    # Inicializar Marshmallow
    ma.init_app(app)

    # Ruta de prueba
    @app.route("/")
    def index():
        return "Hola, Flask está conectado a PostgreSQL y configurado con Azure Monitor."

    return app

