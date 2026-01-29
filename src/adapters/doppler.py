import os

from dopplersdk import DopplerSDK
from dotenv import load_dotenv

from src import constants as c


def load_doppler_secrets():
    load_dotenv()

    # if secrets are in .env, don't fetch them from Doppler
    if all(k in os.environ for k in c.REQUIRED_ENV_VAR_NAMES):
        return

    token = os.environ.get(c.DOPPLER_TOKEN_NAME)
    if not token:
        raise EnvironmentError(f"{c.DOPPLER_TOKEN_NAME} is not set")

    config = os.environ.get("DOPPLER_ENVIRONMENT", os.environ.get("ENV_NAME"))
    if not config:
        raise EnvironmentError("DOPPLER_ENVIRONMENT is not set")

    sdk = DopplerSDK()
    sdk.set_access_token(token)
    response = sdk.secrets.list(project=c.DOPPLER_PROJECT_NAME, config=config)
    if response and response.secrets:
        for key, value in response.secrets.items():
            if key in os.environ:
                continue
            secret_value = getattr(value, "raw", None)
            if secret_value is None and isinstance(value, dict):
                secret_value = (
                    value.get("raw") or value.get("value") or value.get("secret")
                )
            elif secret_value is None and isinstance(value, str):
                secret_value = value

            if secret_value is not None:
                os.environ[key] = secret_value
