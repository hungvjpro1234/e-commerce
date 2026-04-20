import os


def get_env(name, default=None, cast=None):
    value = os.getenv(name, default)
    if cast is None or value is None:
        return value
    if cast is bool:
        return str(value).lower() in {"1", "true", "yes", "on"}
    return cast(value)
