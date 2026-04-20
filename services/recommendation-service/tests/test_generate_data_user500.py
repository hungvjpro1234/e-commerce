import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class GenerateDataUser500Tests(unittest.TestCase):
    def test_generator_creates_dataset_with_500_users_and_all_behaviors(self):
        repo_root = Path(__file__).resolve().parents[3]
        script_path = repo_root / "services" / "recommendation-service" / "scripts" / "generate_data_user500.py"

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "data_user500.csv"
            sample_path = Path(tmp_dir) / "data_user500_sample20.csv"

            result = subprocess.run(
                [
                    sys.executable,
                    str(script_path),
                    "--output",
                    str(output_path),
                    "--sample-output",
                    str(sample_path),
                    "--seed",
                    "20260420",
                ],
                capture_output=True,
                text=True,
                cwd=repo_root,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertTrue(output_path.exists())
            self.assertTrue(sample_path.exists())

            with output_path.open("r", newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))

            self.assertGreater(len(rows), 0)
            self.assertEqual(len({row["user_id"] for row in rows}), 500)
            self.assertEqual(
                {row["behavior_type"] for row in rows},
                {
                    "register",
                    "login",
                    "search",
                    "view_product",
                    "add_to_cart",
                    "update_cart_quantity",
                    "remove_from_cart",
                    "purchase",
                },
            )

            with sample_path.open("r", newline="", encoding="utf-8") as handle:
                sample_rows = list(csv.DictReader(handle))

            self.assertEqual(len(sample_rows), 20)


if __name__ == "__main__":
    unittest.main()
