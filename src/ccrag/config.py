"""Paths, models and environment. Everything else imports from here."""
import os
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

ROOT = Path(__file__).resolve().parents[2]
CORPUS_DIR = ROOT / "corpus"            # committed: field reference + hand-written golden questions
DOCS_DIR = CORPUS_DIR / "docs"
MANUAL_GOLDEN = CORPUS_DIR / "golden_manual.csv"
DATA_DIR = ROOT / "data"                # generated, gitignored
COMPLAINTS_PATH = DATA_DIR / "complaints.jsonl"
GOLDEN_PATH = DATA_DIR / "golden.csv"
EXPERIMENTS_DIR = ROOT / "experiments"  # generated, gitignored
STEPS_PATH = EXPERIMENTS_DIR / "steps.json"
ANSWERS_PATH = EXPERIMENTS_DIR / "answers.jsonl"

DATABASE_URL = (os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL")
                or "postgresql://postgres:postgres@localhost:54329/cfpb")
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4.1-mini")
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")
EMBED_DIM = 1536  # text-embedding-3-small
TABLE = "cfpb_chunks"

REFUSAL = "I don't know based on the documents."
