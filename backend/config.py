import os
from dotenv import load_dotenv
from mistralai import Mistral

load_dotenv()

# Read Mistral API key from env var or fallback to secrets file
DEMO_MODE = False
MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY")
if not MISTRAL_API_KEY:
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    secrets_path = os.path.join(project_root, ".secrets", "mistral_api_key")
    try:
        with open(secrets_path, "r") as f:
            MISTRAL_API_KEY = f.read().strip()
    except FileNotFoundError:
        DEMO_MODE = True
        MISTRAL_API_KEY = "demo"

if MISTRAL_API_KEY == "demo":
    DEMO_MODE = True

AUDIO_MODEL = "voxtral-mini-latest"
TEXT_MODEL = "mistral-large-latest"
MAX_AUDIO_SIZE_MB = 25
MAX_TRANSCRIPT_LENGTH = 10000

# Verdict thresholds
THRESHOLD_SAFE = 0.30
THRESHOLD_SUSPICIOUS = 0.60
THRESHOLD_LIKELY_SCAM = 0.85

# Only create real Mistral client when not in demo mode
client = None if DEMO_MODE else Mistral(api_key=MISTRAL_API_KEY)
