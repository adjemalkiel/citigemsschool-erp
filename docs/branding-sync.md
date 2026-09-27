# Branding & French translations sync

Pull DevOps branding / FR catalogs from the live reference stack and adapt into `apps/citigems_custom`. Prefer remote; `/tmp` copies are ephemeral.

## Remote (preferred)

```bash
# Full app snapshot (review before merge — contains POS/Maya noise)
rsync -az --exclude='*.pyc' --exclude='__pycache__' --exclude='.git' \
  -e ssh \
  devopserp@37.60.247.195:~/devops/devops_custom/ \
  /tmp/devops_custom_pull/

# Selective branding + FR + images into citigems_custom
APP=apps/citigems_custom/citigems_custom
SRC=/tmp/devops_custom_pull/devops_custom

rsync -av "$SRC/public/images/devops-"*.svg "$APP/public/images/"
rsync -av "$SRC/public/images/mobile_money/" "$APP/public/images/mobile_money/"
rsync -av "$SRC/translations/fr.csv" "$APP/translations/fr.csv"
rsync -av "$SRC/french_translations/" "$APP/french_translations/"
# Then re-apply school renames: devops_custom → citigems_custom in sync.py imports
# Drop ury / maya / jewelry / POS-only modules from sync catalog list
```

Optional local branding packs:

```bash
cp /tmp/berakha-branding/devops-images/devops-*.svg apps/citigems_custom/citigems_custom/public/images/
cp /tmp/op-logos/{mtn.svg,moov.png,celtiis.svg} apps/citigems_custom/citigems_custom/public/images/mobile_money/
```

## After sync — keep school-only

- Product title: **Citigems School** (`hooks.py` / `branding.py`)
- Engine chrome: **Powered by DevOps** (logos, rebrand JS, footer)
- Do **not** copy: `public/jewelry/`, `public/maya_shop/`, URY POS routes, storefront API, FacNO device premium
- School FR overrides live in `french_translations/school.py` (élève, scolarité, bulletin, frais, tuteur)

## Apply on site

```bash
bench --site citigems.localhost migrate
# or
bench --site citigems.localhost execute citigems_custom.french_translations.sync.sync_translations
bench --site citigems.localhost execute citigems_custom.branding.ensure_website_branding
```

## Credentials

Never commit IFU / Bearer tokens, FedaPay secret keys, or `.env`. Enter them only in **MeCef Settings** and **FedaPay Settings** Desk forms after install.
