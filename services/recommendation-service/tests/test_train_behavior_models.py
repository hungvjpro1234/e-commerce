import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class TrainBehaviorModelsTests(unittest.TestCase):
    def test_training_script_produces_model_artifacts_and_report(self):
        repo_root = Path(__file__).resolve().parents[3]
        script_path = repo_root / "services" / "recommendation-service" / "scripts" / "train_behavior_models.py"
        preprocessed_dir = repo_root / "services" / "recommendation-service" / "artifacts" / "preprocessed"

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir) / "trained_models"
            result = subprocess.run(
                [
                    sys.executable,
                    str(script_path),
                    "--preprocessed-dir",
                    str(preprocessed_dir),
                    "--output-dir",
                    str(output_dir),
                    "--epochs",
                    "2",
                    "--batch-size",
                    "128",
                ],
                capture_output=True,
                text=True,
                cwd=repo_root,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertTrue((output_dir / "model_rnn.pt").exists())
            self.assertTrue((output_dir / "model_lstm.pt").exists())
            self.assertTrue((output_dir / "model_bilstm.pt").exists())
            self.assertTrue((output_dir / "model_best.pt").exists())
            self.assertTrue((output_dir / "training_report.json").exists())
            self.assertTrue((output_dir / "model_comparison.json").exists())
            self.assertTrue((output_dir / "model_comparison.png").exists())

            training_report = json.loads((output_dir / "training_report.json").read_text(encoding="utf-8"))
            self.assertIn(training_report["best_model"]["name"], {"rnn", "lstm", "bilstm"})
            self.assertEqual(set(training_report["models"].keys()), {"rnn", "lstm", "bilstm"})


if __name__ == "__main__":
    unittest.main()
