# Company setup — Citigems Bilingual School

After the Docker site exists and `citigems_custom` is installed:

```bash
bench --site citigems.localhost execute citigems_custom.scripts.seed_citigems.seed
```

Creates / updates:

| Setting | Value |
|---------|--------|
| Company | Citigems Bilingual School |
| Abbreviation | CBS |
| Country | Benin (BJ) |
| Currency | XOF |
| Language | fr |
| Note | 18-month bilingual school foundation scope |

Also ensures Mobile Money mode of payment and MECeF tax templates A/B when Chart of Accounts is ready.

**Secrets (Desk only, never in git):**

1. **MeCef Settings** for company CBS — IFU, Bearer token, host (`…/api/invoice`), NIM/sandbox as needed  
2. **FedaPay Settings** — API key, webhook secret, Sandbox|Live  
   Webhook URL: `https://<site>/api/method/citigems_custom.api.fedapay.webhook`
