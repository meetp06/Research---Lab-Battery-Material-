import os
from pathlib import Path
from dotenv import load_dotenv

# Find .env in the parent project directory
dotenv_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=dotenv_path)

# Retrieve API key from environment variable
MP_API_KEY = os.getenv("MP_API_KEY")

def get_api_key():
    """Retrieve and validate the Materials Project API key."""
    if not MP_API_KEY or MP_API_KEY == "your_materials_project_api_key_here":
        raise ValueError(
            "Materials Project API Key (MP_API_KEY) is missing or unconfigured. "
            "Please create a `.env` file in the project root directory and set "
            "MP_API_KEY=your_key_here, or set the environment variable."
        )
    return MP_API_KEY
