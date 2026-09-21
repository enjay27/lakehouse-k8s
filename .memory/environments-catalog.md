# Environments & test flow — do not conflate

Three environments, totally different connection vars/secrets, selected via `init_env(<env>)`. Default = **`local`** (safe):
1. **`local`** — personal OrbStack; full suite + destructive `admin/` utilities. `src/config/local.yaml` (gitignored).
2. **`dev`** — shared **company** DEV; functional/integration suites only. NEVER destructive teardown (wipes other users' data). `src/config/dev.yaml` from `dev.example.yaml`.
3. **`prod`** — shared **company** PROD; **availability tests ONLY.** No lifecycle/privilege/purge/mutating notebooks. From `prod.example.yaml`.
Enforcement now in place: module default env = `local`; mutating notebooks call `require_not_prod(...)`; `admin/polaris_clean_all.ipynb` is **intentionally** hardcoded to localhost + has an `assert` host guard (a safety feature) — do NOT port it onto `init_env`/shared config.

