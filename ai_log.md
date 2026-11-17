# AI use log (about half a page)
Tool: Claude (Anthropic), one long working session. Full transcript: see ai_transcripts/ (add the exported chat here).

Two mistakes caught
1. Misread payers_dN as cumulative; the implied payer curve was impossible. Checking against telemetry showed it is per-day. Corrected before any modelling.
2. Explained the Jun-Jul jump between d7 and d30 revenue as an outage/backfill. Telemetry showed a rewarded-eCPM spike on 14-16 Jul (A) / 15-16 Jul (B) instead, so the fix is a spike correction, not a backfill adjustment. (Also: early Net-D ROAS was overstated by rich early-August cohorts in the window; changed to a 6-week window.)

One big time-saver
Writing the cleaning pipeline, curve model, bootstrap, backtests and the constrained optimiser (with a second solver as a check) as re-runnable code.

What I checked myself: the numbers in the memo against outputs/ files, and that run_all.py reproduces them.
