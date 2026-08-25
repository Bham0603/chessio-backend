"""Lichess Opening Explorer service for Cheesio.

Fetches and processes historical chess opening statistics from the
official Lichess Masters Opening Explorer API, providing win-rate
breakdowns for top candidate continuations.
"""

import os
import logging
from typing import Any, Final

from dotenv import load_dotenv
import requests

from schemas import OpeningMoveStat, OpeningStatsResponse

load_dotenv()

logger: logging.Logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lichess API configuration
# ---------------------------------------------------------------------------

_LICHESS_MASTERS_URL: Final[str] = "https://explorer.lichess.ovh/masters"

_REQUEST_TIMEOUT: Final[float] = 10.0  # seconds


def _safe_pct(numerator: int, denominator: int) -> float:
    """Compute a percentage rounded to 1 decimal place, returning 0.0 on zero division.

    Args:
        numerator: The count for this outcome (e.g. white wins).
        denominator: The total number of games.

    Returns:
        The percentage as a float rounded to one decimal place.
    """
    if denominator == 0:
        return 0.0
    return round((numerator / denominator) * 100, 1)


def _parse_move(move: dict[str, Any]) -> OpeningMoveStat:
    """Parse a single move entry from the Lichess API response.

    Args:
        move: A dict containing keys ``uci``, ``san``, ``white``,
              ``draws``, and ``black`` as returned by the API.

    Returns:
        A fully computed OpeningMoveStat.
    """
    white: int = move.get("white", 0)
    draws: int = move.get("draws", 0)
    black: int = move.get("black", 0)
    total: int = white + draws + black

    return OpeningMoveStat(
        san=move.get("san", move.get("uci", "?")),
        total_games=total,
        white_win_pct=_safe_pct(white, total),
        draw_pct=_safe_pct(draws, total),
        black_win_pct=_safe_pct(black, total),
    )


def get_opening_stats(fen: str, top_moves: int = 4) -> OpeningStatsResponse:
    """Fetch opening statistics from the Lichess Masters database.

    Queries the Lichess Opening Explorer for the given FEN position,
    then aggregates per-move win/draw/loss percentages from the
    masters database.

    Args:
        fen: A FEN string representing the board position to query.
        top_moves: Maximum number of candidate continuations to return
                   (default: 4).

    Returns:
        An OpeningStatsResponse containing the opening name, ECO code,
        total master games, and per-move statistics. Falls back to
        safe defaults if the API is unreachable or rate-limited.
    """
    try:
        # Build headers — include Bearer token if available
        headers: dict[str, str] = {
            "Accept": "application/json",
            "User-Agent": "Cheesio-Academic-Project/1.0",
        }
        token: str | None = os.environ.get("LICHESS_API_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"

        response = requests.get(
            _LICHESS_MASTERS_URL,
            params={"fen": fen, "moves": top_moves},
            headers=headers,
            timeout=_REQUEST_TIMEOUT,
        )

        if response.status_code != 200:
            print(f"Lichess API Error: {response.status_code} - {response.text}")
            logger.error(
                "Lichess API returned HTTP %d: %s",
                response.status_code,
                response.text[:200],
            )
            return OpeningStatsResponse(
                opening_name=None,
                eco_code=None,
                total_master_games=0,
                top_continuations=[],
            )

        data: dict[str, Any] = response.json()

        # --- Aggregate totals across all outcomes ---
        total_white: int = data.get("white", 0)
        total_draws: int = data.get("draws", 0)
        total_black: int = data.get("black", 0)
        total_master_games: int = total_white + total_draws + total_black

        # --- Parse opening metadata (may be absent) ---
        opening: dict[str, str] | None = data.get("opening")
        opening_name: str | None = opening.get("name") if opening else None
        eco_code: str | None = opening.get("eco") if opening else None

        # --- Build per-move statistics ---
        raw_moves: list[dict[str, Any]] = data.get("moves", [])
        top_continuations: list[OpeningMoveStat] = [
            _parse_move(m) for m in raw_moves
        ]

        logger.info(
            "Lichess data retrieved: %d master games, %d continuations.",
            total_master_games,
            len(top_continuations),
        )

        return OpeningStatsResponse(
            opening_name=opening_name,
            eco_code=eco_code,
            total_master_games=total_master_games,
            top_continuations=top_continuations,
        )

    except Exception as e:
        print(f"Lichess Request Exception: {e}")
        logger.error("Lichess request failed: %s", e, exc_info=True)

    # --- Fallback response when API is unavailable ---
    return OpeningStatsResponse(
        opening_name=None,
        eco_code=None,
        total_master_games=0,
        top_continuations=[],
    )

