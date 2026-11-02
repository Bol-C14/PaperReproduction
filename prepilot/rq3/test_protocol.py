"""Protocol-only checks with synthetic bytes, never an online VOI experiment."""
import tempfile
import unittest
from pathlib import Path
from protocol import digest, validate


class ReceiptChecks(unittest.TestCase):
    def test_delivery_and_rejections(self):
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "report.txt"
            report.write_text("synthetic receipt fixture")
            state = dict(state_id="s1", current_state_id="s1",
                         allowed_queries=["critical_paths"])
            receipt = dict(state_id="s1", query="critical_paths", started_s=2,
                           ended_s=5, report_path=str(report),
                           report_sha256=digest(report), status="ok", cache_hit=False)
            self.assertEqual(validate(receipt, state, 20)["remaining_episode_s"], 15)
            for change in ({"state_id": "s0"}, {"query": "congestion"},
                           {"ended_s": 21}, {"started_s": 6},
                           {"status": "timeout"}, {"cache_hit": None}):
                with self.subTest(change=change), self.assertRaises(ValueError):
                    validate(receipt | change, state, 20)
            with self.assertRaises(ValueError):
                validate(receipt, state | {"current_state_id": "s2"}, 20)
            report.write_text("changed")
            with self.assertRaises(ValueError):
                validate(receipt, state, 20)


if __name__ == "__main__":
    unittest.main()
