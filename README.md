# Bounty Gate

Fail-closed local gate for a PariBounty JSON report. It accepts only when the
report shows an open, unarchived issue; no assignment, claimant, competing PR,
or report-only policy; evidence of a dollar amount and trusted maintainer funding
terms; and at least one payout-route URL.

```bash
python3 gate.py path/to/paribounty-report.json
```

It prints a JSON decision, exits `0` only for an eligible report, and exits `1`
with machine-readable blockers otherwise. It makes no network request and never
creates a claim, payout record, or external write.

```bash
python3 -m unittest discover -s tests -v
```
