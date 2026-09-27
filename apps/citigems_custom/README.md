# Citigems Custom

School-focused Frappe app for **Citigems Bilingual School** (Benin).

- Publisher: **Malkiel Adje**
- Title: **Citigems School** (Powered by DevOps chrome)
- e-MECeF: MeCef Settings + Sales Invoice normalise (POST → PUT confirm) + QR Jinja helpers
- FedaPay: Settings / Payment + portal `/edu-portal` « Payer les frais » + webhook
- French desk translations + company seed (BJ / XOF / fr)

## Install (once Docker site exists)

From the bench environment (bind-mounted or copied app path):

```bash
# If apps/citigems_custom is already on the bench apps path:
bench --site citigems.localhost install-app citigems_custom
bench --site citigems.localhost migrate

# Or get-app from the host path mounted into the container:
bench get-app /workspace/apps/citigems_custom
bench --site citigems.localhost install-app citigems_custom
```

Seed company + tax helpers (no API secrets):

```bash
bench --site citigems.localhost execute citigems_custom.scripts.seed_citigems.seed
```

Then configure **MeCef Settings** and **FedaPay Settings** in Desk (tokens never in git).

Docs (repo root): `docs/branding-sync.md`, `docs/company-setup.md`, `docs/proposal-backlog.md`.

## Runtime deps

- `requests` (usually present with Frappe)
- `pyqrcode` + `pypng` for MECeF QR print helpers — install in the bench env if missing:
  `bench pip install pyqrcode pypng`
