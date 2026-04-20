import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class PreprocessBehaviorSequencesTests(unittest.TestCase):
    def test_preprocess_creates_splits_and_encoders(self):
        repo_root = Path(__file__).resolve().parents[3]
        script_path = repo_root / "services" / "recommendation-service" / "scripts" / "preprocess_behavior_sequences.py"
        input_csv = repo_root / "docs" / "sample-data" / "data_user500.csv"

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir) / "preprocessed"
            result = subprocess.run(
                [
                    sys.executable,
                    str(script_path),
                    "--input",
                    str(input_csv),
                    "--output-dir",
                    str(output_dir),
                    "--sequence-length",
                    "5",
                ],
                capture_output=True,
                text=True,
                cwd=repo_root,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)

            train_path = output_dir / "train.jsonl"
            val_path = output_dir / "val.jsonl"
            test_path = output_dir / "test.jsonl"
            summary_path = output_dir / "summary.json"
            encoders_path = output_dir / "encoders.json"

            self.assertTrue(train_path.exists())
            self.assertTrue(val_path.exists())
            self.assertTrue(test_path.exists())
            self.assertTrue(summary_path.exists())
            self.assertTrue(encoders_path.exists())

            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            encoders = json.loads(encoders_path.read_text(encoding="utf-8"))
            first_train_row = json.loads(train_path.read_text(encoding="utf-8").splitlines()[0])

            self.assertGreater(summary["total_samples"], 0)
            self.assertEqual(summary["sequence_length"], 5)
            self.assertEqual(summary["num_classes"], 8)
            self.assertIn("behavior_to_id", encoders)
            self.assertEqual(len(first_train_row["input_behavior_ids"]), 5)
            self.assertEqual(len(first_train_row["input_category_ids"]), 5)
            self.assertEqual(len(first_train_row["input_product_service_ids"]), 5)
            self.assertEqual(len(first_train_row["input_quantity_values"]), 5)


if __name__ == "__main__":
    unittest.main()
