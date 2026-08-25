"""LLM engine service for generating chess position explanations.

Uses the Gemini 1.5 Flash model to produce pedagogical explanations
of chess positions, tailored to the student's skill level.
"""

import os
import logging
from typing import Final

import google.generativeai as genai

from schemas import ChessEvaluationRequest, ExplanationResponse

logger: logging.Logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Gemini configuration
# ---------------------------------------------------------------------------

_MODEL_NAME: Final[str] = "gemini-1.5-flash"

_SYSTEM_PROMPT: Final[str] = """\
You are a chess Grandmaster and world-class pedagogical coach.
Your job is to explain a chess position to a student so they genuinely
understand the ideas behind the engine's recommendation.

You will receive:
  • A FEN string describing the board.
  • A centipawn evaluation (positive = White is better).
  • The engine's best move in UCI notation.
  • The student's level (beginner / intermediate / advanced).

Guidelines:
  1. Describe the position in plain language appropriate for the student's level.
  2. Explain *why* the suggested move is strong — what tactical or strategic
     idea does it serve? Mention concrete piece placements, threats, and
     defensive weaknesses.
  3. If the position contains a tactical motif (Pin, Fork, Skewer,
     Discovered Attack, Deflection, Decoy, Zwischenzug, etc.), name it.
     If the position is primarily strategic, use the tag "Positional".
  4. Keep the explanation between 3 and 6 sentences.

Output format (follow EXACTLY):
EXPLANATION: <your explanation here>
MOTIF: <single motif tag>

Do NOT include any other text outside this format.\
"""


def _build_user_prompt(data: ChessEvaluationRequest) -> str:
    """Build the user-turn prompt from the evaluation request.

    Args:
        data: The incoming chess evaluation request.

    Returns:
        A formatted prompt string containing the FEN, score, best move,
        and player level.
    """
    return (
        f"FEN: {data.fen}\n"
        f"Centipawn Score: {data.centipawn_score}\n"
        f"Best Move: {data.best_move}\n"
        f"Student Level: {data.player_level}"
    )


def _parse_llm_response(raw_text: str) -> ExplanationResponse:
    """Parse the structured LLM output into an ExplanationResponse.

    Expects the format:
        EXPLANATION: <text>
        MOTIF: <tag>

    Falls back to sensible defaults when the format is unexpected.

    Args:
        raw_text: The raw text returned by the Gemini model.

    Returns:
        A validated ExplanationResponse.
    """
    explanation: str = raw_text.strip()
    motif: str = "Positional"

    if "EXPLANATION:" in raw_text and "MOTIF:" in raw_text:
        parts = raw_text.split("MOTIF:")
        explanation = parts[0].replace("EXPLANATION:", "").strip()
        motif = parts[1].strip()

    return ExplanationResponse(explanation=explanation, tactical_motif=motif)


def generate_explanation(data: ChessEvaluationRequest) -> ExplanationResponse:
    """Generate a natural-language explanation for a chess position.

    Calls the Gemini 1.5 Flash model with a Grandmaster-coach system
    prompt. If the API key is missing or the call fails for any reason,
    a mock response is returned so the server remains available.

    Args:
        data: A validated ChessEvaluationRequest containing the position,
              evaluation, best move, and student level.

    Returns:
        An ExplanationResponse with a pedagogical explanation and a
        tactical-motif tag.
    """
    api_key: str | None = os.getenv("GEMINI_API_KEY")

    if not api_key:
        logger.warning(
            "GEMINI_API_KEY is not set — returning mock explanation."
        )
        return ExplanationResponse(
            explanation=(
                f"[Mock] The position (FEN: {data.fen}) is evaluated at "
                f"{data.centipawn_score} centipawns. The engine recommends "
                f"{data.best_move}. Set GEMINI_API_KEY to get real analysis."
            ),
            tactical_motif="Positional",
        )

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name=_MODEL_NAME,
            system_instruction=_SYSTEM_PROMPT,
        )

        user_prompt: str = _build_user_prompt(data)
        response = model.generate_content(user_prompt)
        raw_text: str = response.text

        logger.info("Gemini response received (%d chars).", len(raw_text))
        return _parse_llm_response(raw_text)

    except Exception as exc:
        logger.error("Gemini API call failed: %s", exc, exc_info=True)
        return ExplanationResponse(
            explanation=(
                f"[Fallback] Unable to reach the AI engine. The engine "
                f"recommends {data.best_move} with a score of "
                f"{data.centipawn_score} centipawns for FEN: {data.fen}."
            ),
            tactical_motif="Positional",
        )
