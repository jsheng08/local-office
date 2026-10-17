# Local Office synthetic upload pack

1. Drop `1_SPL_client_brief_v1.pdf` into PRJ-SPL first. Run local Nemotron analysis, inspect citations and proposed tasks, then have the PM approve.
2. Drop `2_SPL_client_brief_v2_CHANGED.pdf` next. Re-analyze to show §6 deferred, §8 PDPA controls promoted, §9 earlier go-live, and §11 e-invoicing added. Review before/after proposals; PM approval is required to apply changes.
3. `3_SPL_brief_v2.md` is the equivalent UTF-8 text upload.
4. `4_SPL_brief_v2_photo_of_page.png` is a synthetic printed-page-on-a-desk illustration of the v2 text. It needs the local Omni model; OCR accuracy and the image upload path are **unverified until tested live**. The SVG source is retained for reproducibility and is not an accepted upload format.

The PDFs use Helvetica/WinAnsi with searchable text and multiple pages. PDF extraction is a limited stdlib parser; arbitrary embedded-font or scanned PDFs are not guaranteed. Scanned PDFs must be uploaded as page images. All content is confidential-labelled synthetic demo data.

Leave windows use `LO_TODAY=2026-10-17` for a reproducible demo, otherwise the machine's current date. No approved assignments are changed by the leave filter.

Regenerate with `.venv/bin/python scripts/make_demo_pack.py` (PNG conversion needs macOS qlmanage or sips).

PNG generation: succeeded with macOS Quick Look outside the sandbox; transcription not tested.
