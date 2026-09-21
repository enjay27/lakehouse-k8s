# Goal & structure

The standing objective and the shape of the work. Changes rarely; when it
does, the change is the news.

- **Goal:** Build robust diagnostic / verification notebooks for the local platform services in the `datahub-hynix` namespace (Apache Polaris 1.3.0, PostgreSQL HA via **Pgpool-II** (not PgBouncer — corrected 2026-08-20), MinIO, OpenSearch 1.5.0).
- **Structure model (current):** reusable Python in `src/`; each test domain is its own directory holding notebook(s) + a `README.md` + `doc-*.md` reports. Notebooks bootstrap `src/` onto `sys.path` and call `init_env(env)` for config.
