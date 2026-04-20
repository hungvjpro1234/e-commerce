import argparse
import csv
import json
import random
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[3]
DEFAULT_INPUT = ROOT_DIR / "docs" / "sample-data" / "data_user500.csv"
DEFAULT_OUTPUT_DIR = ROOT_DIR / "services" / "recommendation-service" / "artifacts" / "preprocessed"
PAD_TOKEN = "<PAD>"
UNKNOWN_TOKEN = "<UNK>"
CANONICAL_BEHAVIORS = (
    "register",
    "login",
    "search",
    "view_product",
    "add_to_cart",
    "update_cart_quantity",
    "remove_from_cart",
    "purchase",
)


def parse_args():
    parser = argparse.ArgumentParser(description="Preprocess behavior sequences for next-behavior prediction.")
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--sequence-length", type=int, default=5)
    parser.add_argument("--seed", type=int, default=20260420)
    return parser.parse_args()


def parse_timestamp(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def load_rows(csv_path):
    path = Path(csv_path)
    with path.open("r", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return rows


def build_encoder(values, *, include_unknown=False):
    tokens = [PAD_TOKEN]
    if include_unknown:
        tokens.append(UNKNOWN_TOKEN)

    seen = set(tokens)
    for value in values:
        cleaned = (value or "").strip()
        if not cleaned:
            continue
        if cleaned not in seen:
            tokens.append(cleaned)
            seen.add(cleaned)

    return {token: index for index, token in enumerate(tokens)}


def build_label_encoder():
    tokens = [PAD_TOKEN, *CANONICAL_BEHAVIORS]
    return {token: index for index, token in enumerate(tokens)}


def encode_value(value, encoder, *, allow_unknown=False):
    cleaned = (value or "").strip()
    if not cleaned:
        return encoder[PAD_TOKEN]
    if cleaned in encoder:
        return encoder[cleaned]
    if allow_unknown and UNKNOWN_TOKEN in encoder:
        return encoder[UNKNOWN_TOKEN]
    raise KeyError(f"Value '{cleaned}' not found in encoder.")


def build_sequence(values, encoder, sequence_length, *, allow_unknown=False):
    encoded = [encode_value(value, encoder, allow_unknown=allow_unknown) for value in values[-sequence_length:]]
    padding = [encoder[PAD_TOKEN]] * (sequence_length - len(encoded))
    return padding + encoded


def group_sessions(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["session_id"]].append(row)

    for session_rows in grouped.values():
        session_rows.sort(key=lambda row: (parse_timestamp(row["timestamp"]), int(row["step_in_session"])))
    return grouped


def split_users(user_ids, seed):
    rng = random.Random(seed)
    shuffled = sorted(user_ids)
    rng.shuffle(shuffled)

    total = len(shuffled)
    train_cutoff = int(total * 0.7)
    val_cutoff = train_cutoff + int(total * 0.15)

    train_users = set(shuffled[:train_cutoff])
    val_users = set(shuffled[train_cutoff:val_cutoff])
    test_users = set(shuffled[val_cutoff:])

    return {
        "train": train_users,
        "val": val_users,
        "test": test_users,
    }


def determine_split(user_id, split_map):
    for split_name, users in split_map.items():
        if user_id in users:
            return split_name
    raise KeyError(f"User {user_id} not found in split map.")


def create_samples(rows, sequence_length, seed):
    behavior_encoder = build_encoder((row["behavior_type"] for row in rows))
    label_encoder = build_label_encoder()
    category_encoder = build_encoder((row["category"] for row in rows), include_unknown=True)
    product_service_encoder = build_encoder((row["product_service"] for row in rows), include_unknown=True)
    source_service_encoder = build_encoder((row["source_service"] for row in rows), include_unknown=True)

    session_groups = group_sessions(rows)
    split_map = split_users({row["user_id"] for row in rows}, seed=seed)

    samples = []
    for session_id, session_rows in session_groups.items():
        for index, row in enumerate(session_rows):
            label = row["label_next_behavior"].strip()
            if not label:
                continue

            context_rows = session_rows[max(0, index - sequence_length + 1): index + 1]
            behavior_values = [item["behavior_type"] for item in context_rows]
            category_values = [item["category"] for item in context_rows]
            product_service_values = [item["product_service"] for item in context_rows]
            source_service_values = [item["source_service"] for item in context_rows]
            quantity_values = [
                int(item["quantity"]) if (item["quantity"] or "").strip() else 0
                for item in context_rows
            ]

            padded_quantities = [0] * (sequence_length - len(quantity_values)) + quantity_values[-sequence_length:]

            samples.append(
                {
                    "sample_id": f"{session_id}:{row['step_in_session']}",
                    "user_id": row["user_id"],
                    "session_id": session_id,
                    "target_behavior": label,
                    "target_behavior_id": label_encoder[label],
                    "input_behavior_ids": build_sequence(behavior_values, behavior_encoder, sequence_length),
                    "input_category_ids": build_sequence(
                        category_values,
                        category_encoder,
                        sequence_length,
                        allow_unknown=True,
                    ),
                    "input_product_service_ids": build_sequence(
                        product_service_values,
                        product_service_encoder,
                        sequence_length,
                        allow_unknown=True,
                    ),
                    "input_source_service_ids": build_sequence(
                        source_service_values,
                        source_service_encoder,
                        sequence_length,
                        allow_unknown=True,
                    ),
                    "input_quantity_values": padded_quantities,
                    "sequence_actual_length": min(len(context_rows), sequence_length),
                    "split": determine_split(row["user_id"], split_map),
                }
            )

    encoders = {
        "behavior_to_id": behavior_encoder,
        "label_to_id": label_encoder,
        "category_to_id": category_encoder,
        "product_service_to_id": product_service_encoder,
        "source_service_to_id": source_service_encoder,
    }
    return samples, encoders, split_map


def summarize_dataset(rows, samples, split_map, encoders, sequence_length, input_path):
    split_counts = Counter(sample["split"] for sample in samples)
    class_distribution = Counter(sample["target_behavior"] for sample in samples)
    split_class_distribution = {}
    for split_name in ("train", "val", "test"):
        split_class_distribution[split_name] = dict(
            sorted(Counter(sample["target_behavior"] for sample in samples if sample["split"] == split_name).items())
        )
    return {
        "input_csv": str(input_path),
        "sequence_length": sequence_length,
        "total_rows": len(rows),
        "total_users": len({row["user_id"] for row in rows}),
        "total_sessions": len({row["session_id"] for row in rows}),
        "total_samples": len(samples),
        "split_user_counts": {name: len(users) for name, users in split_map.items()},
        "split_sample_counts": dict(sorted(split_counts.items())),
        "class_distribution": dict(sorted(class_distribution.items())),
        "split_class_distribution": split_class_distribution,
        "num_classes": len(encoders["label_to_id"]) - 1,
    }


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


def preprocess_dataset(input_path, output_dir, sequence_length, seed):
    rows = load_rows(input_path)
    samples, encoders, split_map = create_samples(rows, sequence_length, seed)

    output_path = Path(output_dir)
    split_rows = {
        "train": [sample for sample in samples if sample["split"] == "train"],
        "val": [sample for sample in samples if sample["split"] == "val"],
        "test": [sample for sample in samples if sample["split"] == "test"],
    }

    for split_name, split_samples in split_rows.items():
        write_jsonl(output_path / f"{split_name}.jsonl", split_samples)

    summary = summarize_dataset(rows, samples, split_map, encoders, sequence_length, input_path)
    write_json(output_path / "encoders.json", encoders)
    write_json(output_path / "split_users.json", {name: sorted(users) for name, users in split_map.items()})
    write_json(output_path / "summary.json", summary)

    return summary


def main():
    args = parse_args()
    summary = preprocess_dataset(args.input, args.output_dir, args.sequence_length, args.seed)
    print(f"Preprocessed dataset written to: {args.output_dir}")
    print(f"Total samples: {summary['total_samples']}")
    print(f"Split sample counts: {summary['split_sample_counts']}")
    print(f"Class distribution: {summary['class_distribution']}")


if __name__ == "__main__":
    main()
