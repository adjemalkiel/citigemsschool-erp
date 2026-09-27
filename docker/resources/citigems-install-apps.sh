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
    branch = app.get("branch", "version-15")
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

find apps -mindepth 2 -name .git -type d -prune -exec rm -rf {} + 2>/dev/null || true
echo "citigems apps install complete"
ls -1 apps
cat sites/apps.txt
