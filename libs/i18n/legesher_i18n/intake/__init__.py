"""Review-intake write path (CORE-1688): bundle + issue importers.

The pieces that turn reviewer submissions into corpus rows, one pipeline for
every lane (Stage-0 GitHub issue, Stage-1 review bundle, and later the
Stage-2 portal): canonical-JSON serialization (:mod:`.canonical`), the bundle
wire contract (:mod:`.bundle`, ``bundle_schema.json``), the six-stage
verification pipeline (:mod:`.pipeline`), the Stage-0 issue-form parser
(:mod:`.issue_parser`), and the import ledger + contributor reply
(:mod:`.ledger`).
"""
