import os


def _clean_env_value(value):
    if not value:
        return value

    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]

    return value


class Config:
    SECRET_KEY = _clean_env_value(os.getenv('SECRET_KEY')) or 'dev-secret-key-change-me'
    SQLALCHEMY_DATABASE_URI = _clean_env_value(os.getenv('DATABASE_URL')) or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
   
