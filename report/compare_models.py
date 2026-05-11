"""Train SVM, KNN, Random Forest, and MLP on the IMU gesture dataset.
Produces per-model confusion matrices and an accuracy comparison bar chart.
Run from the report/ folder:
    python compare_models.py
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import ConfusionMatrixDisplay, confusion_matrix
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.svm import LinearSVC

sys.path.insert(0, str(Path(__file__).parent.parent / "data" / "gesture_recognition"))
from imu_gesture_classifier import extract_features, load_dataset

DATA_DIR = Path(__file__).parent.parent / "data" / "gesture_recognition" / "imu_samples"
EXTRA_NONE_DIR = Path(__file__).parent.parent.parent / "demo" / "imu-gesture-drone-control" / "rough" / "none-myrecord"

MODELS = {
    "Linear SVM": Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LinearSVC(C=1.0, dual="auto", max_iter=10000)),
    ]),
    "k-Nearest Neighbors": Pipeline([
        ("scaler", StandardScaler()),
        ("clf", KNeighborsClassifier(n_neighbors=5)),
    ]),
    "Random Forest": Pipeline([
        ("clf", RandomForestClassifier(n_estimators=200, random_state=42)),
    ]),
    "MLP (Neural Net)": Pipeline([
        ("scaler", StandardScaler()),
        ("clf", MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=500, random_state=42)),
    ]),
}


def load_extra_none(extra_dir: Path) -> np.ndarray:
    import pandas as pd
    rows = []
    for path in sorted(extra_dir.glob("*.txt")):
        df = pd.read_csv(path)
        rows.append(extract_features(df))
    return np.vstack(rows) if rows else np.empty((0, 60))


def main() -> None:
    X, y_raw, _ = load_dataset(DATA_DIR)

    # Pad "none" class to 30 samples using extra recordings from demo/rough
    extra_X = load_extra_none(EXTRA_NONE_DIR)
    extra_y = np.array(["none"] * len(extra_X))
    X = np.vstack([X, extra_X])
    y_raw = np.concatenate([y_raw, extra_y])
    print(f"[INFO] Added {len(extra_X)} extra 'none' samples — none class now {(y_raw == 'none').sum()}")

    le = LabelEncoder()
    y = le.fit_transform(y_raw)
    class_names = le.classes_.tolist()

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    accuracies = {}

    for name, pipeline in MODELS.items():
        y_pred = cross_val_predict(pipeline, X, y, cv=cv)
        acc = float(np.mean(y_pred == y))
        accuracies[name] = acc

        cm = confusion_matrix(y, y_pred)
        fig, ax = plt.subplots(figsize=(7, 6))
        disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=class_names)
        disp.plot(ax=ax, colorbar=False, xticks_rotation=45, cmap="Blues")
        ax.set_title(f"{name} — Accuracy: {acc:.1%}")
        ax.set_xlabel("")
        ax.set_ylabel("")
        fig.tight_layout()
        fname = f"figures/cm_{name.lower().replace(' ', '_').replace('(', '').replace(')', '')}.png"
        fig.savefig(fname, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"Saved {fname}")

    # Accuracy bar chart
    fig_bar, ax_bar = plt.subplots(figsize=(8, 4))
    names = list(accuracies.keys())
    vals = [accuracies[n] for n in names]
    colors = ["#2196F3", "#4CAF50", "#FF9800", "#00BCD4"]
    bars = ax_bar.bar(names, vals, color=colors, edgecolor="white", linewidth=0.8)
    ax_bar.set_ylim(0, 1.05)
    ax_bar.set_ylabel("5-Fold CV Accuracy")
    ax_bar.set_title("Model Accuracy Comparison")
    ax_bar.set_xticks(range(len(names)))
    ax_bar.set_xticklabels(names, rotation=15, ha="right")
    for bar, val in zip(bars, vals):
        ax_bar.text(bar.get_x() + bar.get_width() / 2, val + 0.01,
                    f"{val:.1%}", ha="center", va="bottom", fontsize=10)
    fig_bar.tight_layout()
    fig_bar.savefig("figures/accuracy_comparison.png", dpi=150, bbox_inches="tight")
    print("Saved figures/accuracy_comparison.png")

    print("\nModel Accuracies:")
    for name, acc in accuracies.items():
        print(f"  {name:<30} {acc:.1%}")

    plt.close("all")


if __name__ == "__main__":
    Path("figures").mkdir(exist_ok=True)
    main()
