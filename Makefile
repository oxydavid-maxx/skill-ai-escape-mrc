# skill-ai-escape-mrc Makefile
# WIKI-CONSULTED: silent-staleness#detection-via-content
# WIKI-FINDING: A make target that doesn't write a fresh evidence file or
#   exits 0 vacuously reproduces silent-staleness; the audit-closed-loop
#   target must produce governance/audits/*.json with the actual run trace.
# WIKI-ACTION: --json-report-file path is fixed (not date-templated) so
#   re-runs overwrite, and the file's mtime is the staleness signal R17 uses.
# Source: AI Escape MRC run-1777208113-4411cfdc Task 2 Step 5.

.PHONY: audit-closed-loop test

audit-closed-loop:
	mkdir -p governance/audits
	py -3 -m pytest tests/e2e/test_closed_loop_pipeline.py -v \
		--json-report --json-report-file=governance/audits/2026-04-26-closed-loop-e2e.json

test:
	py -3 -m pytest tests/ -v
