from __future__ import annotations

from pathlib import Path
import json
import sys
import tempfile
import unittest

from runledger.core import RunLedgerError, record


class RunLedgerTests(unittest.TestCase):
    def test_success_and_selected_environment(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "input.txt").write_text("hello", encoding="utf-8")
            receipt, code = record(
                [sys.executable, "-c", "print('ok')"],
                cwd=root,
                env_names=["PATH", "RUNLEDGER_NOT_PRESENT"],
                input_paths=["input.txt"],
            )
            self.assertEqual(code, 0)
            self.assertEqual(receipt.exit_code, 0)
            self.assertEqual(len(receipt.inputs), 1)
            self.assertEqual(set(receipt.environment), {"PATH"})

    def test_failure_code_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            receipt, code = record(
                [sys.executable, "-c", "raise SystemExit(7)"],
                cwd=Path(raw),
            )
            self.assertEqual(code, 7)
            self.assertEqual(receipt.exit_code, 7)

    def test_output_digest_is_taken_after_command(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            receipt, code = record(
                [sys.executable, "-c", "from pathlib import Path; Path('out.txt').write_text('done')"],
                cwd=root,
                output_paths=["out.txt"],
            )
            self.assertEqual(code, 0)
            self.assertEqual(receipt.outputs[0].path, "out.txt")
            self.assertTrue(receipt.outputs[0].sha256)

    def test_path_escape_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            with self.assertRaises(RunLedgerError):
                record([sys.executable, "-c", "pass"], cwd=Path(raw), input_paths=["../outside"])

    def test_receipt_is_json_serializable(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            receipt, _ = record([sys.executable, "-c", "pass"], cwd=Path(raw))
            encoded = json.dumps(receipt.as_dict(), sort_keys=True)
            self.assertIn('"version": 1', encoded)


if __name__ == "__main__":
    unittest.main()
