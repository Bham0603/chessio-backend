import json
import re
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "deepseek-r1:8b"

def generate_explanation(fen: str, centipawn_score: int, best_move: str, player_level: str = "beginner") -> dict:
    prompt = f"""
You are an expert Chess Coach and Grandmaster.
Analyze the following chess position and the recommended best move.

Position FEN: {fen}
Best Move: {best_move}
Engine Evaluation: {centipawn_score}
Target Audience: {player_level}

Classify the tactical theme into EXACTLY ONE category from this list:
["Pin", "Fork", "Skewer", "Discovered Attack", "Deflection", "Decoy", "Checkmate", "Back-Rank Mate", "Hanging Piece", "Positional"]

Output ONLY a single raw JSON object in this exact schema without any markdown formatting:
{{"explanation": "<2 concise sentences explaining the move>", "tactical_motif": "<One category from the list above>"}}
"""

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }

    try:
        # High timeout required for reasoning models
        res = requests.post(OLLAMA_URL, json=payload, timeout=120)

        if res.status_code == 200:
            raw_text = res.json().get("response", "").strip()

            # Strip the DeepSeek <think> block
            clean_text = re.sub(r'<think>.*?</think>', '', raw_text, flags=re.DOTALL).strip()

            # Extract JSON block
            match = re.search(r'\{.*\}', clean_text, re.DOTALL)
            if match:
                return json.loads(match.group(0))

            return json.loads(clean_text)

        else:
            print(f"[Ollama Error] Status {res.status_code}: {res.text}")

    except Exception as e:
        print(f"[LLM Engine Error]: {e}")

    return {
        "explanation": f"Stockfish suggests {best_move}. Look for tactical pressure.",
        "tactical_motif": "Positional"
    }
