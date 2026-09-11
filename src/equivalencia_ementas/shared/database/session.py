from collections.abc import Generator

from sqlalchemy.orm import Session, sessionmaker

from equivalencia_ementas.shared.database.engine import engine


SessionFactory = sessionmaker(
    bind=engine,
    class_=Session,
    autoflush=False,
    expire_on_commit=False,
)


def get_session() -> Generator[Session, None, None]:
    session = SessionFactory()

    try:
        yield session
    finally:
        session.close()