import csv
import tempfile
import unittest
from pathlib import Path

from scripts.import_kb_graph import build_graph_documents, load_behavior_rows, write_sample_queries


class ImportKbGraphTests(unittest.TestCase):
    def test_build_graph_documents_creates_expected_nodes_and_relationship_inputs(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            dataset_path = Path(tmp_dir) / "data_user500.csv"
            with dataset_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "user_id",
                        "session_id",
                        "timestamp",
                        "behavior_type",
                        "product_service",
                        "product_id",
                        "category",
                        "search_keyword",
                        "quantity",
                        "step_in_session",
                        "label_next_behavior",
                        "source_service",
                        "is_synthetic",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "user_id": "user-1",
                        "session_id": "session-1",
                        "timestamp": "2026-01-01T08:00:00+00:00",
                        "behavior_type": "search",
                        "product_service": "",
                        "product_id": "",
                        "category": "Cloth",
                        "search_keyword": "hoodie",
                        "quantity": "",
                        "step_in_session": "1",
                        "label_next_behavior": "view_product",
                        "source_service": "web-service",
                        "is_synthetic": "1",
                    }
                )
                writer.writerow(
                    {
                        "user_id": "user-1",
                        "session_id": "session-1",
                        "timestamp": "2026-01-01T08:05:00+00:00",
                        "behavior_type": "view_product",
                        "product_service": "cloth",
                        "product_id": "product-1",
                        "category": "Cloth",
                        "search_keyword": "",
                        "quantity": "",
                        "step_in_session": "2",
                        "label_next_behavior": "add_to_cart",
                        "source_service": "web-service",
                        "is_synthetic": "1",
                    }
                )

            rows = load_behavior_rows(dataset_path)
            documents = build_graph_documents(
                rows,
                {
                    "product-1": {
                        "product_id": "product-1",
                        "name": "Demo Hoodie",
                        "description": "Warm hoodie",
                        "price": "39.99",
                        "stock": 10,
                        "image_url": "",
                        "domain": "cloth",
                        "domain_label": "Cloth",
                    }
                },
            )

            self.assertEqual(len(documents["users"]), 1)
            self.assertEqual(len(documents["categories"]), 1)
            self.assertEqual(len(documents["products"]), 1)
            self.assertEqual(len(documents["behaviors"]), 2)
            self.assertEqual(len(documents["interests"]), 1)
            self.assertEqual(documents["products"][0]["name"], "Demo Hoodie")
            self.assertEqual(documents["behaviors"][1]["behavior_id"], "session-1:2")

    def test_write_sample_queries_creates_cypher_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "kb_graph_queries.cypher"
            write_sample_queries(path)
            self.assertTrue(path.exists())
            self.assertIn("MATCH (p:Product)", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
