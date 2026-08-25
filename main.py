"""Cheesio — Explainable AI Chess Tutor (FastAPI backend).

Entrypoint for the Cheesio API server. Loads environment variables,
configures CORS for local development, and exposes the /api/v1/explain
endpoint for chess position analysis.
"""

from dotenv import load_dotenv

# Load .env BEFORE any other application imports so that
# GEMINI_API_KEY (and future secrets) are available immediately.
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from schemas import ChessEvaluationRequest, ExplanationResponse
from services.llm_engine import generate_explanation

# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

app: FastAPI = FastAPI(
    title="Cheesio — XAI Chess Tutor",
    description=(
        "An Explainable-AI chess backend that turns raw engine evaluations "
        "into pedagogical, human-readable explanations powered by Gemini."
    ),
    version="0.1.0",
)

# ---------------------------------------------------------------------------
# CORS — allow the browser extension (or any local client) to connect
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.post(
    "/api/v1/explain",
    response_model=ExplanationResponse,
    summary="Explain a chess position",
    description=(
        "Accepts a chess position with its engine evaluation and returns "
        "a natural-language explanation plus a tactical-motif tag."
    ),
)
async def explain_position(
    request: ChessEvaluationRequest,
) -> ExplanationResponse:
    """Receive a chess evaluation and return an AI-generated explanation.

    Args:
        request: The incoming evaluation payload (FEN, score, best move,
                 player level).

    Returns:
        An ExplanationResponse containing the pedagogical explanation
        and the identified tactical motif.
    """
    return generate_explanation(request)
