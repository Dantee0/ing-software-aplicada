class Config:
    DEBUG = False
    TESTING = False
    OTEL_SERVICE_NAME = "FlaskApp"

class DevelopmentConfig(Config):
    DEBUG = True
    CONNECTION_STRING = "postgresql://matigol:neuquen0$@monitor-ing.postgres.database.azure.com:5432/postgres"

class ProductionConfig(Config):
    CONNECTION_STRING = "postgresql://matigol:neuquen0$@monitor-ing.postgres.database.azure.com:5432/postgres"

# Mapeo de configuraciones
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig
}

def factory(env_name):
    """
    Devuelve la configuración correspondiente al entorno especificado.
    Si no se encuentra, devuelve 'DevelopmentConfig' por defecto.
    """
    return config.get(env_name, DevelopmentConfig)
