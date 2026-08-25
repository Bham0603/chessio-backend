"""Pydantic schemas for the Cheesio XAI Chess Tutor API.

Defines request and response models for chess position evaluation,
natural-language explanation generation, and opening statistics.
"""

from pydantic import BaseModel, Field


class ChessEvaluationRequest(BaseModel):
    """Incoming request containing a chess position and its engine evaluation.

    Attributes:
        fen: A FEN (Forsyth-Edwards Notation) string describing the board state.
        centipawn_score: The engine evaluation in centipawns (positive = White advantage).
        best_move: The engine's recommended move in UCI notation (e.g. "e2e4").
        player_level: The student's skill level, used to tailor explanation depth.
    """

    fen: str = Field(
        ...,
        description="FEN string representing the current board position.",
        examples=["rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"],
    )
    centipawn_score: float = Field(
        ...,
        description="Engine evaluation in centipawns. Positive favours White.",
        examples=[150.0],
    )
    best_move: str = Field(
        ...,
        description="Best move in UCI notation (e.g. 'e2e4', 'g1f3').",
        examples=["d7d5"],
    )
    player_level: str = Field(
        default="beginner",
        description="Student skill level: 'beginner', 'intermediate', or 'advanced'.",
        examples=["beginner"],
    )


class ExplanationResponse(BaseModel):
    """Response containing a human-readable explanation and a tactical motif tag.

    Attributes:
        explanation: A pedagogical, plain-language breakdown of the position
                     and the recommended move.
        tactical_motif: A single tag classifying the dominant motif
                        (e.g. "Pin", "Fork", "Positional", "Skewer").
    """

    explanation: str = Field(
        ...,
        description="Natural-language explanation of the position and best move.",
    )
    tactical_motif: str = Field(
        ...,
        description="Single tactical/strategic motif tag (e.g. 'Fork', 'Pin', 'Positional').",
    )


# ---------------------------------------------------------------------------
# Phase 2 — Opening Statistics (Data Science Engine)
# ---------------------------------------------------------------------------


class OpeningMoveStat(BaseModel):
    """Win-rate statistics for a single candidate continuation move.

    Attributes:
        san: The move in Standard Algebraic Notation (e.g. "e4", "Nf3").
        total_games: Number of master games featuring this continuation.
        white_win_pct: White's win percentage (0.0–100.0, 1 d.p.).
        draw_pct: Draw percentage (0.0–100.0, 1 d.p.).
        black_win_pct: Black's win percentage (0.0–100.0, 1 d.p.).
    """

    san: str = Field(
        ...,
        description="Move in Standard Algebraic Notation.",
        examples=["e4"],
    )
    total_games: int = Field(
        ...,
        description="Total master games featuring this continuation.",
        examples=[24356],
    )
    white_win_pct: float = Field(
        ...,
        description="White win percentage (0.0–100.0).",
        examples=[38.2],
    )
    draw_pct: float = Field(
        ...,
        description="Draw percentage (0.0–100.0).",
        examples=[35.1],
    )
    black_win_pct: float = Field(
        ...,
        description="Black win percentage (0.0–100.0).",
        examples=[26.7],
    )


class OpeningStatsResponse(BaseModel):
    """Aggregated opening statistics from the Lichess Masters database.

    Attributes:
        opening_name: Name of the opening (e.g. "Sicilian Defense"), or None
                      if unrecognised.
        eco_code: ECO classification code (e.g. "B20"), or None if unavailable.
        total_master_games: Total number of master games for this position.
        top_continuations: Per-move win/draw/loss breakdowns for the top
                           candidate continuations.
    """

    opening_name: str | None = Field(
        default=None,
        description="Opening name (e.g. 'Sicilian Defense').",
        examples=["Sicilian Defense"],
    )
    eco_code: str | None = Field(
        default=None,
        description="ECO classification code (e.g. 'B20').",
        examples=["B20"],
    )
    total_master_games: int = Field(
        ...,
        description="Total master games evaluated for this position.",
        examples=[87432],
    )
    top_continuations: list[OpeningMoveStat] = Field(
        default_factory=list,
        description="Win-rate statistics for the top candidate continuations.",
    )
