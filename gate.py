"""Deterministic eligibility gate for PariBounty JSON evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

TRUSTED_ASSOCIATIONS = {"OWNER", "MEMBER", "COLLABORATOR"}
PAYOUT_URL_MARKERS = ("payout", "payment", "escrow", "bounty")


def assess(report: dict[str, Any]) -> dict[str, Any]:
    """Return a fail-closed eligibility decision from a PariBounty report."""
    evidence = report.get("evidence", {})
    if not isinstance(evidence, dict):
        return {"eligible": False, "blockers": ["invalid_evidence"], "payout_route_urls": []}

    blockers: list[str] = []
    if str(evidence.get("state", "")).lower() != "open":
        blockers.append("issue_not_open")
    if evidence.get("repository_archived"):
        blockers.append("repository_archived")
    if evidence.get("report_only_policy_detected"):
        blockers.append("report_only_policy")
    if evidence.get("assignees"):
        blockers.append("assigned_to_another_contributor")
    if evidence.get("claimers"):
        blockers.append("active_claimer")
    if evidence.get("open_pull_requests"):
        blockers.append("open_competing_pull_request")

    trusted_statements = [
        statement
        for statement in evidence.get("maintainer_statements", [])
        if str(statement.get("association", "")).upper() in TRUSTED_ASSOCIATIONS
    ]
    trusted_text = " ".join(str(item.get("body", "")).lower() for item in trusted_statements)
    amount_evidence = any(
        isinstance(amount, (int, float)) and amount > 0
        for key in ("issue_amounts_usd", "comment_amounts_usd", "policy_amounts_usd")
        for amount in evidence.get(key, [])
        if isinstance(evidence.get(key, []), list)
    )
    funding_terms = ("funded", "escrow", "paid after", "payment")
    if not amount_evidence or not any(term in trusted_text for term in funding_terms):
        blockers.append("unverified_funding")

    payout_route_urls = sorted(
        {
            str(url)
            for url in evidence.get("urls", [])
            if url and any(marker in str(url).lower() for marker in PAYOUT_URL_MARKERS)
        }
    )
    if not payout_route_urls:
        blockers.append("missing_payout_route")

    eligible = not blockers
    return {
        "eligible": eligible,
        "blockers": blockers,
        "payout_route_urls": payout_route_urls,
        "next_step": (
            "recheck_original_source_then_claim_once" if eligible else "do_not_claim"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, help="PariBounty JSON report path")
    args = parser.parse_args()
    try:
        report = json.loads(args.report.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        parser.error(f"cannot read JSON report: {error}")
    decision = assess(report)
    print(json.dumps(decision, sort_keys=True))
    return 0 if decision["eligible"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
