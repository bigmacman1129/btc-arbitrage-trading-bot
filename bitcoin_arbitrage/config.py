import os

basedir = os.path.abspath(os.path.dirname(__file__))
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'database.db')


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.lower() in ('1', 'true', 'yes', 'on')


SECRET_KEY = os.environ.get('FLASK_SECRET_KEY')
if not SECRET_KEY:
    # Keep local development usable without shipping an insecure static key.
    SECRET_KEY = os.urandom(32).hex()

DEBUG = _env_flag('FLASK_DEBUG', default=False)

LAST_SPREADS_FILENAME = 'last_spreads.csv'
SPREAD_HISTORY_FILENAME = 'spread_history.csv'
