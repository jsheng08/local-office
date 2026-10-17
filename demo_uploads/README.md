# Local Office synthetic upload pack

## Demo: "client change v2" (recommended)

1. In the Office tab, press **↺ Reset data (v1 approved)**. The board returns to the approved brief v1 baseline, restored from a recorded real local Nemotron run (`data/demo/baseline_v1.json`, run `run-ec6339e7`). No model call happens on reset.
2. Drag **`2_SPL_client_brief_v2_CHANGED.pdf`** onto the office (the mailroom chute lights up). The helper reads it with local Nemotron and re-triages: §8 PDPA IC handling promoted, §11 LHDN MyInvois added, §9 go-live pulled in, §6 KPI reports deferred.
3. Optional: **Try approving as Analyst** to show the backend's 403.
4. Press **Approve as PM** to open the change-request document, review it, then **Sign & apply to board**. The wards update straight away.

Alternatives for step 2: `3_SPL_brief_v2.md` (same text as plain markdown) or `4_SPL_brief_v2_photo_of_page.png` (needs the local Omni model; **unverified until tested live**).

## From scratch

Drop `1_SPL_client_brief_v1.pdf` instead of resetting to run the v1 analysis live (it contains the hidden §6 "ignore previous instructions" line that gets quarantined), approve as PM, then continue at step 2.

The PDFs use Helvetica/WinAnsi with searchable text and multiple pages. PDF extraction is a limited stdlib parser; arbitrary embedded-font or scanned PDFs are not guaranteed. Scanned PDFs must be uploaded as page images. All content is confidential-labelled synthetic demo data.

Leave windows use `LO_TODAY=2026-10-17` for a reproducible demo, otherwise the machine's current date. No approved assignments are changed by the leave filter.

Regenerate with `.venv/bin/python scripts/make_demo_pack.py` (PNG conversion needs macOS qlmanage or sips).

PNG generation: succeeded with macOS Quick Look outside the sandbox; transcription not tested.
