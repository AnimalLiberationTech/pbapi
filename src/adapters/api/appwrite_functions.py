import os
import sys

# in the Appwrite environment, the code is under /usr/local/server/src/function/
# root 'path' in appwrite.json is 'appwrite_functions', so
# the entrypoint is 'src/adapters/api/appwrite_functions.py'
current_dir = os.path.dirname(__file__)  # src/adapters/api/
base_dir = os.path.abspath(os.path.join(current_dir, "../../../"))
if base_dir not in sys.path:
    sys.path.append(base_dir)


from src.adapters.doppler import load_doppler_secrets

load_doppler_secrets()

from src.adapters.api.fastapi_app import app
from src.adapters.api.appwrite_fastapi_adapter import run_fastapi_on_appwrite


async def main(context):
    return await run_fastapi_on_appwrite(app, context)
