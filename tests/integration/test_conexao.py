from sqlalchemy import text

from equivalencia_ementas.shared.database.engine import engine
from equivalencia_ementas.shared.settings.config import get_settings


def test_deve_conectar_ao_banco_configurado() -> None:
    settings = get_settings()

    with engine.connect() as connection:
        banco_atual = connection.execute(
            text("SELECT DB_NAME()")
        ).scalar_one()

    assert banco_atual == settings.db_name