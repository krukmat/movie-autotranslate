from contextlib import contextmanager

from sqlmodel import Session, create_engine

from ..config import get_settings

settings = get_settings()

engine = create_engine(settings.database_url, echo=False)


@contextmanager
def get_session() -> Session:
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()
