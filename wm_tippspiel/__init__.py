try:
    from flask_sqlalchemy import SQLAlchemy
    db = SQLAlchemy()
except ImportError:  # allows engine-only tests without web dependencies
    db = None
