from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


# Import domain models so Alembic metadata includes all tables.
from app.domains.assets import models as _asset_models  # noqa: E402, F401
from app.domains.generation import models as _generation_models  # noqa: E402, F401
from app.domains.projects import models as _project_models  # noqa: E402, F401
from app.domains.publish import models as _publish_models  # noqa: E402, F401
from app.domains.review import models as _review_models  # noqa: E402, F401
from app.domains.style import models as _style_models  # noqa: E402, F401
from app.domains.settings import models as _settings_models  # noqa: E402, F401


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
