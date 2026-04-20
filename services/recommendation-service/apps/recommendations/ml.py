import torch
import torch.nn as nn


class SequenceBehaviorModel(nn.Module):
    def __init__(
        self,
        *,
        model_type,
        behavior_vocab_size,
        category_vocab_size,
        product_service_vocab_size,
        source_service_vocab_size,
        embedding_dim,
        hidden_size,
        num_classes,
        dropout,
    ):
        super().__init__()
        self.model_type = model_type

        self.behavior_embedding = nn.Embedding(behavior_vocab_size, embedding_dim, padding_idx=0)
        self.category_embedding = nn.Embedding(category_vocab_size, embedding_dim, padding_idx=0)
        self.product_service_embedding = nn.Embedding(product_service_vocab_size, embedding_dim, padding_idx=0)
        self.source_service_embedding = nn.Embedding(source_service_vocab_size, embedding_dim, padding_idx=0)
        self.quantity_projection = nn.Linear(1, 4)

        input_size = embedding_dim * 4 + 4
        recurrent_cls = {
            "rnn": nn.RNN,
            "lstm": nn.LSTM,
            "bilstm": nn.LSTM,
        }[model_type]
        bidirectional = model_type == "bilstm"
        self.recurrent = recurrent_cls(
            input_size=input_size,
            hidden_size=hidden_size,
            batch_first=True,
            dropout=0.0,
            bidirectional=bidirectional,
        )
        recurrent_output_size = hidden_size * (2 if bidirectional else 1)
        self.classifier = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(recurrent_output_size, hidden_size),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size, num_classes),
        )

    def forward(
        self,
        behavior_ids,
        category_ids,
        product_service_ids,
        source_service_ids,
        quantity_values,
        sequence_length,
    ):
        behavior_emb = self.behavior_embedding(behavior_ids)
        category_emb = self.category_embedding(category_ids)
        product_service_emb = self.product_service_embedding(product_service_ids)
        source_service_emb = self.source_service_embedding(source_service_ids)
        quantity_emb = self.quantity_projection(quantity_values.unsqueeze(-1))

        features = torch.cat(
            [behavior_emb, category_emb, product_service_emb, source_service_emb, quantity_emb],
            dim=-1,
        )

        _output, hidden = self.recurrent(features)
        if isinstance(hidden, tuple):
            hidden = hidden[0]

        if self.model_type == "bilstm":
            final_hidden = torch.cat([hidden[-2], hidden[-1]], dim=1)
        else:
            final_hidden = hidden[-1]

        return self.classifier(final_hidden)
