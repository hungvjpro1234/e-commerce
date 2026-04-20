from collections import Counter
from pathlib import Path

import requests
import torch
from django.conf import settings
from torch import nn


class BehaviorMLP(nn.Module):
    def __init__(self, num_users, num_items, embedding_dim=16):
        super().__init__()
        self.user_embedding = nn.Embedding(num_users, embedding_dim)
        self.item_embedding = nn.Embedding(num_items, embedding_dim)
        self.layers = nn.Sequential(
            nn.Linear(embedding_dim * 2, 32),
            nn.ReLU(),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, 1),
        )

    def forward(self, user_indices, item_indices):
        user_vec = self.user_embedding(user_indices)
        item_vec = self.item_embedding(item_indices)
        joined = torch.cat([user_vec, item_vec], dim=1)
        return self.layers(joined).squeeze(1)


def fetch_behavior_training_rows():
    response = requests.get(
        f"{settings.BEHAVIOR_SERVICE_URL}/api/internal/training-data",
        headers={
            "X-Internal-Service-Token": settings.INTERNAL_SERVICE_TOKEN,
            "X-Service-Name": settings.SERVICE_NAME,
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json().get("data", [])


def train_and_save_model(epochs=40):
    rows = fetch_behavior_training_rows()
    if not rows:
        raise RuntimeError("No behavior data available for training.")

    user_keys = sorted({row["user_id"] for row in rows})
    item_keys = sorted({row["item_key"] for row in rows})
    user_to_idx = {key: idx for idx, key in enumerate(user_keys)}
    item_to_idx = {key: idx for idx, key in enumerate(item_keys)}

    user_tensor = torch.tensor([user_to_idx[row["user_id"]] for row in rows], dtype=torch.long)
    item_tensor = torch.tensor([item_to_idx[row["item_key"]] for row in rows], dtype=torch.long)
    target_tensor = torch.tensor([row["score"] for row in rows], dtype=torch.float32)

    model = BehaviorMLP(max(len(user_keys), 1), max(len(item_keys), 1))
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    loss_fn = nn.MSELoss()

    for _ in range(epochs):
        optimizer.zero_grad()
        predictions = model(user_tensor, item_tensor)
        loss = loss_fn(predictions, target_tensor)
        loss.backward()
        optimizer.step()

    artifact_path = Path(settings.MODEL_ARTIFACT_PATH)
    artifact_path.parent.mkdir(parents=True, exist_ok=True)

    popularity = Counter()
    item_catalog = {}
    for row in rows:
        popularity[row["item_key"]] += row["score"]
        item_catalog[row["item_key"]] = {"product_service": row["product_service"], "product_id": row["product_id"]}

    torch.save({
        "state_dict": model.state_dict(),
        "user_to_idx": user_to_idx,
        "item_to_idx": item_to_idx,
        "item_catalog": item_catalog,
        "popularity": dict(popularity),
    }, artifact_path)
    return {
        "artifact_path": str(artifact_path),
        "users": len(user_keys),
        "items": len(item_keys),
        "rows": len(rows),
    }
