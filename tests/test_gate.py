import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from gate import assess


class GateTests(unittest.TestCase):
    def test_accepts_maintainer_confirmed_funding_without_competition(self):
        result = assess(
            {
                "evidence": {
                    "state": "open",
                    "issue_amounts_usd": [100.0],
                    "comment_amounts_usd": [],
                    "policy_amounts_usd": [],
                    "assignees": [],
                    "claimers": [],
                    "open_pull_requests": [],
                    "report_only_policy_detected": False,
                    "repository_archived": False,
                    "maintainer_statements": [
                        {
                            "association": "MEMBER",
                            "body": "This $100 bounty is funded and paid after an accepted patch.",
                        }
                    ],
                    "urls": ["https://example.test/payout-terms"],
                }
            }
        )
        self.assertTrue(result["eligible"])
        self.assertEqual(result["blockers"], [])
        self.assertEqual(result["payout_route_urls"], ["https://example.test/payout-terms"])
        self.assertEqual(result["next_step"], "recheck_original_source_then_claim_once")

    def test_cli_writes_a_json_decision_and_nonzero_for_rejection(self):
        report = {
            "evidence": {
                "state": "open",
                "issue_amounts_usd": [],
                "comment_amounts_usd": [],
                "policy_amounts_usd": [],
                "assignees": [],
                "claimers": [],
                "open_pull_requests": [],
                "report_only_policy_detected": False,
                "repository_archived": False,
                "maintainer_statements": [],
                "urls": [],
            }
        }
        with tempfile.TemporaryDirectory() as directory:
            report_path = Path(directory) / "report.json"
            report_path.write_text(json.dumps(report), encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, "gate.py", str(report_path)],
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(completed.returncode, 1)
        self.assertFalse(json.loads(completed.stdout)["eligible"])

    def test_rejects_zero_amount_even_when_maintainer_says_funded(self):
        result = assess(
            {
                "evidence": {
                    "state": "open",
                    "issue_amounts_usd": [0.0],
                    "comment_amounts_usd": [],
                    "policy_amounts_usd": [],
                    "assignees": [],
                    "claimers": [],
                    "open_pull_requests": [],
                    "report_only_policy_detected": False,
                    "repository_archived": False,
                    "maintainer_statements": [
                        {
                            "association": "OWNER",
                            "body": "This bounty is funded and payment is available.",
                        }
                    ],
                    "urls": ["https://example.test/payment"],
                }
            }
        )
        self.assertFalse(result["eligible"])
        self.assertIn("unverified_funding", result["blockers"])
        self.assertEqual(result["next_step"], "do_not_claim")

    def test_rejects_irrelevant_url_without_trusted_payout_route(self):
        result = assess(
            {
                "evidence": {
                    "state": "open",
                    "issue_amounts_usd": [100.0],
                    "comment_amounts_usd": [],
                    "policy_amounts_usd": [],
                    "assignees": [],
                    "claimers": [],
                    "open_pull_requests": [],
                    "report_only_policy_detected": False,
                    "repository_archived": False,
                    "maintainer_statements": [
                        {
                            "association": "OWNER",
                            "body": "The $100 bounty is funded after acceptance.",
                        }
                    ],
                    "urls": ["https://example.test/contributing"],
                }
            }
        )
        self.assertFalse(result["eligible"])
        self.assertEqual(result["payout_route_urls"], [])
        self.assertIn("missing_payout_route", result["blockers"])

    def test_rejects_competing_claim_and_unverified_payment(self):
        result = assess(
            {
                "evidence": {
                    "state": "open",
                    "issue_amounts_usd": [500.0],
                    "comment_amounts_usd": [],
                    "policy_amounts_usd": [],
                    "assignees": [],
                    "claimers": ["another-worker"],
                    "open_pull_requests": ["https://github.com/owner/repo/pull/5"],
                    "report_only_policy_detected": False,
                    "repository_archived": False,
                    "maintainer_statements": [],
                    "urls": [],
                }
            }
        )
        self.assertFalse(result["eligible"])
        self.assertIn("active_claimer", result["blockers"])
        self.assertIn("open_competing_pull_request", result["blockers"])
        self.assertIn("unverified_funding", result["blockers"])


if __name__ == "__main__":
    unittest.main()
