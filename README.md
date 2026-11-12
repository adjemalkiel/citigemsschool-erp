# Citigems School ERP

Dockerized **ERPNext v16** for Citigems Bilingual School (Benin), with Education, HRMS, and Payments.

## How to start the stack

```bash
# 0) Docker access (local daemon)
sudo usermod -aG docker "$USER" && newgrp docker

# 1) Env / secrets (once)
cp docker/.env.example docker/.env
# Set DB_PASSWORD and ADMIN_PASSWORD (or use values already in secrets/)

# 2) Build image citigems/erpnext:16
./scripts/build.sh

# 3) Compose up + create site
./scripts/up.sh

# 4) Browse
# Production / remote: https://erp.citigemsschool.com  (A/AAAA → Docker host)
# Local daemon alternative: set SITE_NAME=citigems.localhost and add hosts entry
```

| Item | Value |
|------|--------|
| Site URL | https://erp.citigemsschool.com (see `SITE_NAME` in `docker/.env`) |
| Login | `Administrator` |
| Admin password | `secrets/admin_password.txt` (also `ADMIN_PASSWORD` in gitignored `docker/.env`) |
| DB root password | `secrets/db_password.txt` / `DB_PASSWORD` in `docker/.env` |
| Compose | `docker/pwd.yml` (project `citigems`) |
| HTTP publish port | `HTTP_PUBLISH_PORT` (default **8080**) |
| Image | `citigems/erpnext:16` |
| Custom app bind | `docker/compose.bind-citigems-custom.yaml` → `apps/citigems_custom` (local Docker only) |

### Scripts

| Script | Purpose |
|--------|---------|
| `./scripts/build.sh` | Lightweight extend of `frappe/erpnext:v16` + apps from `apps.json` |
| `./scripts/build.sh --layered` | Full frappe_docker layered build (more RAM) |
| `./scripts/up.sh` | `docker compose up -d` and wait for `create-site` |
| `./scripts/bench.sh …` | `bench` in the backend container |

### Apps (`apps.json`)

| App | Branch |
|-----|--------|
| erpnext | `version-16` |
| hrms | `version-16` |
| education | `version-16` |
| payments | `version-16` |

Build uses BuildKit `--secret id=apps_json`. `APPS_JSON_BASE64` is also written to gitignored `apps.json.b64` for compatibility.

## Low-RAM builds (~8GB)

Default `./scripts/build.sh` extends `frappe/erpnext:v16` and clones apps with `JOBS=1` (avoids full `bench init` OOM).

If the build still OOMs: free memory, avoid `--layered`, or add swap (e.g. 4G). Prefer the default extend build on this host size.

## Custom app mount

`apps/citigems_custom` is bind-mounted when Docker runs **locally** (overlay `compose.bind-citigems-custom.yaml`). After the app is scaffolded:

```bash
./scripts/bench.sh --site citigems.localhost install-app citigems_custom
```

## Notes

- `docker/` is vendored [frappe/frappe_docker](https://github.com/frappe/frappe_docker) plus Citigems overlays (`Containerfile.citigems`, `pwd.yml`, bind overlay).
- Never commit `docker/.env`, `secrets/`, or API tokens.
- If the local user cannot access `/var/run/docker.sock`, set `DOCKER_HOST` in `docker/.env` (see `.env.example`) and pick a free `HTTP_PUBLISH_PORT` on that host.
