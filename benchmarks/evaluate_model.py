import json
import time
import requests
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix

API_URL = "http://127.0.0.1:8000/api/v1/explain"
DATASET_PATH = "test_dataset.json"

def clean_motif(text: str) -> str:
    return "".join(c for c in str(text).strip().lower() if c.isalnum())

def run_benchmark():
    with open(DATASET_PATH, "r") as f:
        dataset = json.load(f)

    y_true = []
    y_pred = []
    correct_count = 0

    print("\n" + "="*50)
    print("  RUNNING CHEESIO ACADEMIC BENCHMARK")
    print("="*50 + "\n")

    for idx, item in enumerate(dataset, 1):
        payload = {
            "fen": item["fen"],
            "centipawn_score": item["centipawn_score"],
            "best_move": item["best_move"],
            "player_level": "beginner"
        }
        
        ground_truth = item["ground_truth_motif"]
        predicted = "Failed"

        try:
            res = requests.post(API_URL, json=payload, timeout=45)
            if res.status_code == 200:
                data = res.json()
                predicted = data.get("tactical_motif", "Positional")
            else:
                print(f"[HTTP Error] Status {res.status_code}: {res.text}")
        except Exception as e:
            print(f"[Request Error]: {e}")

        gt_clean = clean_motif(ground_truth)
        pred_clean = clean_motif(predicted)
        
        is_match = (gt_clean in pred_clean) or (pred_clean in gt_clean)
        
        if is_match:
            correct_count += 1
            status = "PASS"
            # Normalize to ground truth string for clean confusion matrix display
            y_true.append(ground_truth)
            y_pred.append(ground_truth)
        else:
            status = "FAIL"
            y_true.append(ground_truth)
            y_pred.append(predicted)

        print(f"[{idx}/{len(dataset)}] Ground Truth: {ground_truth:<18} | Predicted: {predicted:<18} | Result: {status}")
        time.sleep(3)  # Respect API limits

    accuracy = (correct_count / len(dataset)) * 100
    print("\n" + "="*50)
    print(f"  FINAL BENCHMARK ACCURACY: {accuracy:.1f}% ({correct_count}/{len(dataset)})")
    print("="*50 + "\n")

    # Generate Confusion Matrix
    labels = sorted(list(set(y_true + y_pred)))
    cm = confusion_matrix(y_true, y_pred, labels=labels)

    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=labels, yticklabels=labels)
    plt.title("Cheesio AI - Tactical Motif Confusion Matrix", fontsize=14, pad=15)
    plt.xlabel("Predicted Motif", fontsize=12)
    plt.ylabel("Ground Truth Motif", fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig("confusion_matrix_report.png", dpi=300)
    print("[INFO] High-res plot saved -> confusion_matrix_report.png\n")

if __name__ == "__main__":
    run_benchmark()
