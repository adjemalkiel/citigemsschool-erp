#!/bin/bash
set -euo pipefail
cd /home/frappe/frappe-bench
export JOBS="${JOBS:-1}"
# Reduce yarn/node parallelism
export CHILD_CONCURRENCY=1
export npm_config_jobs=1

python3 <<'PY'
import json, subprocess, os, pathlib, shutil
apps = json.load(open("/opt/frappe/apps.json"))
bench = pathlib.Path("/home/frappe/frappe-bench")
existing = {p.name for p in (bench / "apps").iterdir() if p.is_dir()}
sp = next(bench.glob("env/lib/python*/site-packages"))

def clone_and_pip(name, url, branch):
    dest = bench / "apps" / name
    if dest.exists():
        print(f"skip existing app: {name}", flush=True)
        return
    print(f"clone {name} ({branch})", flush=True)
    subprocess.check_call(
        ["git", "clone", "--depth", "1", "--branch", branch, url, str(dest)],
        env={**os.environ},
    )
    pth = sp / f"{name}.pth"
    pth.write_text(f"/home/frappe/frappe-bench/apps/{name}\n")
    subprocess.check_call(
        [str(bench / "env/bin/pip"), "install", "--quiet", "-e", f"apps/{name}"],
        cwd=str(bench),
    )
    print(f"{name} baked OK", flush=True)

for app in apps:
    url = app["url"]
    branch = app.get("branch", "version-16")
    name = url.rstrip("/").split("/")[-1]
    if name.endswith(".git"):
        name = name[:-4]
    if name == "erpnext" and name in existing:
        print(f"skip existing app: {name}", flush=True)
        continue
    # Prefer clone+pip (skips yarn SPA install — run bench build later for desk assets)
    clone_and_pip(name, url, branch)
PY

ls -1 apps > sites/apps.txt

# Desk asset build only (skip missing SPA frontends if yarn not run)
if ! bench build --app hrms --app education --app payments 2>/tmp/bench-build.log; then
  echo "bench build with app filter failed; trying full build" >&2
  cat /tmp/bench-build.log >&2 || true
  bench build || true
fi

if [ -d sites/assets ]; then
  rm -rf assets
  cp -a sites/assets assets
  rm -rf sites/assets
fi

# Ensure assets.json maps short bundle names → hashed dist files (bench build may no-op without node).
python3 <<'PY'
from pathlib import Path
import re, json
assets = Path("/home/frappe/frappe-bench/assets")
assets.mkdir(parents=True, exist_ok=True)
ltr, rtl = {}, {}
for dist in assets.glob("*/dist/**/*"):
    if not dist.is_file() or dist.suffix == ".map":
        continue
    m = re.match(r"^(.+)\.([A-Z0-9]+)\.(css|js)$", dist.name)
    if not m:
        continue
    short = f"{m.group(1)}.{m.group(3)}"
    url = f"/assets/{dist.relative_to(assets).as_posix()}"
    if "/css-rtl/" in url or "/js-rtl/" in url:
        rtl[f"rtl_{short}"] = url
    else:
        ltr[short] = url
out = dict(ltr)
out.update(rtl)
path = assets / "assets.json"
existing = {}
if path.exists():
    try:
        existing = json.loads(path.read_text() or "{}")
    except Exception:
        existing = {}
if len(existing) < 5 and out:
    path.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(f"wrote assets.json with {len(out)} keys", flush=True)
else:
    print(f"assets.json ok ({len(existing)} keys)", flush=True)
# Link any app public/ dirs missing from assets/
apps = Path("/home/frappe/frappe-bench/apps")
for app in apps.iterdir():
    if not app.is_dir():
        continue
    pub = next(app.glob("*/public"), None)
    if pub is None or not pub.is_dir():
        continue
    link = assets / app.name
    if not link.exists():
        link.symlink_to(pub)
        print(f"linked assets/{app.name}", flush=True)
PY

find apps -mindepth 2 -name .git -type d -prune -exec rm -rf {} + 2>/dev/null || true
echo "citigems apps install complete"
ls -1 apps
cat sites/apps.txt
