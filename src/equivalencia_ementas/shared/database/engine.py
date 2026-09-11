from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.engine.base import Engine

from equivalencia_ementas.shared.settings.config import get_settings


def create_database_engine() -> Engine:
    settings = get_settings()

    connection_string = (
        f"DRIVER={{{settings.db_driver}}};"
        f"SERVER={settings.db_server};"
        f"DATABASE={settings.db_name};"
        f"Trusted_Connection={settings.db_trusted_connection};"
        f"TrustServerCertificate={settings.db_trust_server_certificate};"
        "Encrypt=yes;"
        "LongAsMax=yes;"
    )

    connection_url = URL.create(
        "mssql+pyodbc",
        query={"odbc_connect": connection_string},
    )

    return create_engine(
        connection_url,
        echo=settings.db_echo,
        pool_pre_ping=True,
    )


engine = create_database_engine()