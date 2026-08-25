"""Pydantic schemas for the Cheesio XAI Chess Tutor API.

Defines request and response models for chess position evaluation
and natural-language explanation generation.
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
