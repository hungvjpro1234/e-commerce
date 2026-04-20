import argparse
import json
import math
import random
import sys
from copy import deepcopy
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, precision_recall_fscore_support
from torch.utils.data import DataLoader, Dataset


ROOT_DIR = Path(__file__).resolve().parents[3]
SERVICE_DIR = Path(__file__).resolve().parents[1]
for path in (ROOT_DIR, SERVICE_DIR):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from apps.recommendations.ml import SequenceBehaviorModel
DEFAULT_PREPROCESSED_DIR = ROOT_DIR / "services" / "recommendation-service" / "artifacts" / "preprocessed"
DEFAULT_OUTPUT_DIR = ROOT_DIR / "services" / "recommendation-service" / "artifacts" / "trained_models"
MODEL_OUTPUT_NAMES = {
    "rnn": "model_rnn.pt",
    "lstm": "model_lstm.pt",
    "bilstm": "model_bilstm.pt",
}


def parse_args():
    parser = argparse.ArgumentParser(description="Train RNN/LSTM/biLSTM models for next-behavior prediction.")
    parser.add_argument("--preprocessed-dir", default=str(DEFAULT_PREPROCESSED_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--epochs", type=int, default=14)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--learning-rate", type=float, default=0.002)
    parser.add_argument("--hidden-size", type=int, default=64)
    parser.add_argument("--embedding-dim", type=int, default=16)
    parser.add_argument("--dropout", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=20260420)
    return parser.parse_args()


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


class BehaviorSequenceDataset(Dataset):
    def __init__(self, jsonl_path):
        self.rows = []
        with Path(jsonl_path).open("r", encoding="utf-8") as handle:
            for line in handle:
                self.rows.append(json.loads(line))

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, index):
        row = self.rows[index]
        return {
            "behavior_ids": torch.tensor(row["input_behavior_ids"], dtype=torch.long),
            "category_ids": torch.tensor(row["input_category_ids"], dtype=torch.long),
            "product_service_ids": torch.tensor(row["input_product_service_ids"], dtype=torch.long),
            "source_service_ids": torch.tensor(row["input_source_service_ids"], dtype=torch.long),
            "quantity_values": torch.tensor(row["input_quantity_values"], dtype=torch.float32),
            "sequence_length": torch.tensor(row["sequence_actual_length"], dtype=torch.long),
            "target_id": torch.tensor(row["target_behavior_id"] - 1, dtype=torch.long),
        }


def load_training_context(preprocessed_dir):
    directory = Path(preprocessed_dir)
    encoders = json.loads((directory / "encoders.json").read_text(encoding="utf-8"))
    summary = json.loads((directory / "summary.json").read_text(encoding="utf-8"))
    datasets = {
        "train": BehaviorSequenceDataset(directory / "train.jsonl"),
        "val": BehaviorSequenceDataset(directory / "val.jsonl"),
        "test": BehaviorSequenceDataset(directory / "test.jsonl"),
    }
    return datasets, encoders, summary


def create_dataloaders(datasets, batch_size):
    return {
        "train": DataLoader(datasets["train"], batch_size=batch_size, shuffle=True),
        "val": DataLoader(datasets["val"], batch_size=batch_size, shuffle=False),
        "test": DataLoader(datasets["test"], batch_size=batch_size, shuffle=False),
    }


def run_epoch(model, data_loader, optimizer, criterion, device):
    training = optimizer is not None
    model.train(training)

    epoch_loss = 0.0
    all_targets = []
    all_predictions = []

    for batch in data_loader:
        batch = {key: value.to(device) for key, value in batch.items()}
        logits = model(
            batch["behavior_ids"],
            batch["category_ids"],
            batch["product_service_ids"],
            batch["source_service_ids"],
            batch["quantity_values"],
            batch["sequence_length"],
        )
        loss = criterion(logits, batch["target_id"])

        if training:
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

        predictions = torch.argmax(logits, dim=1)
        epoch_loss += loss.item() * batch["target_id"].size(0)
        all_targets.extend(batch["target_id"].detach().cpu().tolist())
        all_predictions.extend(predictions.detach().cpu().tolist())

    avg_loss = epoch_loss / len(data_loader.dataset)
    accuracy = accuracy_score(all_targets, all_predictions)
    return {
        "loss": avg_loss,
        "accuracy": accuracy,
        "targets": all_targets,
        "predictions": all_predictions,
    }


def evaluate_predictions(targets, predictions, label_names):
    precision, recall, f1, support = precision_recall_fscore_support(
        targets,
        predictions,
        labels=list(range(len(label_names))),
        zero_division=0,
    )
    report = classification_report(
        targets,
        predictions,
        labels=list(range(len(label_names))),
        target_names=label_names,
        output_dict=True,
        zero_division=0,
    )
    return {
        "accuracy": accuracy_score(targets, predictions),
        "macro_precision": float(np.mean(precision)),
        "macro_recall": float(np.mean(recall)),
        "macro_f1": float(np.mean(f1)),
        "weighted_precision": report["weighted avg"]["precision"],
        "weighted_recall": report["weighted avg"]["recall"],
        "weighted_f1": report["weighted avg"]["f1-score"],
        "per_class": {
            label_names[index]: {
                "precision": precision[index],
                "recall": recall[index],
                "f1": f1[index],
                "support": int(support[index]),
            }
            for index in range(len(label_names))
        },
        "confusion_matrix": confusion_matrix(
            targets,
            predictions,
            labels=list(range(len(label_names))),
        ).tolist(),
    }


def plot_training_history(history, output_dir):
    output_path = Path(output_dir)
    epochs = list(range(1, len(history["train_loss"]) + 1))

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    axes[0].plot(epochs, history["train_loss"], label="Train Loss")
    axes[0].plot(epochs, history["val_loss"], label="Validation Loss")
    axes[0].set_title("Loss")
    axes[0].set_xlabel("Epoch")
    axes[0].set_ylabel("Loss")
    axes[0].legend()

    axes[1].plot(epochs, history["train_accuracy"], label="Train Accuracy")
    axes[1].plot(epochs, history["val_accuracy"], label="Validation Accuracy")
    axes[1].set_title("Accuracy")
    axes[1].set_xlabel("Epoch")
    axes[1].set_ylabel("Accuracy")
    axes[1].legend()

    fig.tight_layout()
    fig.savefig(output_path / "training_curves.png", dpi=150)
    plt.close(fig)


def plot_model_comparison(comparison_rows, output_dir):
    output_path = Path(output_dir)
    model_names = [row["model"] for row in comparison_rows]
    weighted_f1 = [row["weighted_f1"] for row in comparison_rows]
    accuracy = [row["accuracy"] for row in comparison_rows]

    x = np.arange(len(model_names))
    width = 0.35

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(x - width / 2, accuracy, width, label="Accuracy")
    ax.bar(x + width / 2, weighted_f1, width, label="Weighted F1")
    ax.set_xticks(x)
    ax.set_xticklabels(model_names)
    ax.set_ylim(0, 1)
    ax.set_title("Model Comparison")
    ax.legend()

    fig.tight_layout()
    fig.savefig(output_path / "model_comparison.png", dpi=150)
    plt.close(fig)


def save_json(path, payload):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def train_one_model(model_name, datasets, encoders, args, device):
    loaders = create_dataloaders(datasets, args.batch_size)
    label_names = [name for name, index in sorted(encoders["label_to_id"].items(), key=lambda item: item[1]) if name != "<PAD>"]

    model = SequenceBehaviorModel(
        model_type=model_name,
        behavior_vocab_size=len(encoders["behavior_to_id"]),
        category_vocab_size=len(encoders["category_to_id"]),
        product_service_vocab_size=len(encoders["product_service_to_id"]),
        source_service_vocab_size=len(encoders["source_service_to_id"]),
        embedding_dim=args.embedding_dim,
        hidden_size=args.hidden_size,
        num_classes=len(label_names),
        dropout=args.dropout,
    ).to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=args.learning_rate)

    history = {
        "train_loss": [],
        "val_loss": [],
        "train_accuracy": [],
        "val_accuracy": [],
    }
    best_state = None
    best_val_f1 = -math.inf
    best_epoch = 0

    for epoch in range(1, args.epochs + 1):
        train_result = run_epoch(model, loaders["train"], optimizer, criterion, device)
        val_result = run_epoch(model, loaders["val"], None, criterion, device)
        val_metrics = evaluate_predictions(val_result["targets"], val_result["predictions"], label_names)

        history["train_loss"].append(train_result["loss"])
        history["val_loss"].append(val_result["loss"])
        history["train_accuracy"].append(train_result["accuracy"])
        history["val_accuracy"].append(val_result["accuracy"])

        if val_metrics["weighted_f1"] > best_val_f1:
            best_val_f1 = val_metrics["weighted_f1"]
            best_state = deepcopy(model.state_dict())
            best_epoch = epoch

    model.load_state_dict(best_state)
    test_result = run_epoch(model, loaders["test"], None, criterion, device)
    test_metrics = evaluate_predictions(test_result["targets"], test_result["predictions"], label_names)

    return {
        "model": model,
        "history": history,
        "best_epoch": best_epoch,
        "val_weighted_f1": best_val_f1,
        "test_metrics": test_metrics,
        "label_names": label_names,
    }


def export_model_artifact(model_name, result, args, encoders, output_dir):
    model_output_path = Path(output_dir) / MODEL_OUTPUT_NAMES[model_name]
    torch.save(
        {
            "model_type": model_name,
            "state_dict": result["model"].state_dict(),
            "encoders": encoders,
            "hyperparameters": {
                "embedding_dim": args.embedding_dim,
                "hidden_size": args.hidden_size,
                "dropout": args.dropout,
                "sequence_length": json.loads((Path(args.preprocessed_dir) / "summary.json").read_text(encoding="utf-8"))["sequence_length"],
            },
        },
        model_output_path,
    )

    save_json(
        Path(output_dir) / f"{model_name}_metrics.json",
        {
            "best_epoch": result["best_epoch"],
            "validation_weighted_f1": result["val_weighted_f1"],
            "test_metrics": result["test_metrics"],
            "training_history": result["history"],
        },
    )


def train_all_models(args):
    set_seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    datasets, encoders, summary = load_training_context(args.preprocessed_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    comparison_rows = []
    all_results = {}

    for model_name in ("rnn", "lstm", "bilstm"):
        result = train_one_model(model_name, datasets, encoders, args, device)
        all_results[model_name] = result
        export_model_artifact(model_name, result, args, encoders, output_dir)
        comparison_rows.append(
            {
                "model": model_name,
                "accuracy": result["test_metrics"]["accuracy"],
                "weighted_f1": result["test_metrics"]["weighted_f1"],
                "macro_f1": result["test_metrics"]["macro_f1"],
                "best_epoch": result["best_epoch"],
            }
        )

    best_model_row = max(comparison_rows, key=lambda row: (row["weighted_f1"], row["accuracy"]))
    best_model_name = best_model_row["model"]
    best_model_path = output_dir / MODEL_OUTPUT_NAMES[best_model_name]
    best_export_path = output_dir / "model_best.pt"
    best_export_path.write_bytes(best_model_path.read_bytes())

    save_json(output_dir / "model_comparison.json", comparison_rows)
    save_json(
        output_dir / "training_report.json",
        {
            "device": str(device),
            "preprocessed_summary": summary,
            "models": {
                model_name: {
                    "best_epoch": result["best_epoch"],
                    "history": result["history"],
                    "test_metrics": result["test_metrics"],
                }
                for model_name, result in all_results.items()
            },
            "best_model": {
                "name": best_model_name,
                "selection_rule": "highest weighted_f1, then accuracy",
                "artifact": str(best_export_path),
            },
        },
    )

    for model_name, result in all_results.items():
        model_plot_dir = output_dir / f"plots_{model_name}"
        model_plot_dir.mkdir(parents=True, exist_ok=True)
        plot_training_history(result["history"], model_plot_dir)

    plot_model_comparison(comparison_rows, output_dir)

    return {
        "comparison_rows": comparison_rows,
        "best_model_name": best_model_name,
        "output_dir": str(output_dir),
    }


def main():
    args = parse_args()
    report = train_all_models(args)
    print(f"Training artifacts written to: {report['output_dir']}")
    print(f"Best model: {report['best_model_name']}")
    for row in report["comparison_rows"]:
        print(
            f"{row['model']}: accuracy={row['accuracy']:.4f}, "
            f"weighted_f1={row['weighted_f1']:.4f}, macro_f1={row['macro_f1']:.4f}"
        )


if __name__ == "__main__":
    main()
