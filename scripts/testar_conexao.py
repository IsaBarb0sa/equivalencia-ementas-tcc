from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from equivalencia_ementas.shared.database.engine import engine


def main() -> None:
    try:
        with engine.connect() as connection:
            result = connection.execute(
                text(
                    """
                    SELECT
                        DB_NAME() AS banco,
                        SERVERPROPERTY('ProductVersion') AS versao,
                        SERVERPROPERTY('Edition') AS edicao
                    """
                )
            ).one()

        print("Conexão realizada com sucesso!")
        print(f"Banco: {result.banco}")
        print(f"Versão: {result.versao}")
        print(f"Edição: {result.edicao}")

    except SQLAlchemyError as error:
        print("Não foi possível conectar ao SQL Server.")
        print(f"Detalhes: {error}")
        raise


if __name__ == "__main__":
    main()