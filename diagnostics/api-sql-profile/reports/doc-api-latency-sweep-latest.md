# API latency sweep

- **run_id**: 20260822-044103
- **realm**: POLARIS
- **schema**: polaris_schema
- **polaris**: http://192.168.139.2:8181

Every number below comes from calls aimed at REAL fixture entities.
Cloned rows supply volume only -- they are synthetic, have no storage
behind them, and nothing is measured against them.

## Control -- read this first

`POST /oauth/tokens` across all 4 cells: median 6.84 ms, spread 0.60 ms (6.74 .. 7.34).

It resolves no grants, so it should not move. Any effect reported
below that is smaller than this spread is noise.

## Index effect (isolates GRANT volume)

| API | clones | without | with | delta |
|---|---:|---:|---:|---:|
| `GET  /catalog-roles/{r}/grants` | 0 | 8.21 | 9.32 | -1.11 |
| `GET  /catalog-roles/{r}/grants` | 100 | 7.73 | 8.21 | -0.48 |
| `GET  /catalogs` | 0 | 8.64 | 8.28 | +0.36 |
| `GET  /catalogs` | 100 | 15.94 | 13.36 | +2.58 |
| `GET  /catalogs/{c}/catalog-roles` | 0 | 8.11 | 7.84 | +0.27 |
| `GET  /catalogs/{c}/catalog-roles` | 100 | 6.36 | 7.52 | -1.16 |
| `GET  /catalogs/{name}` | 0 | 6.75 | 7.17 | -0.42 |
| `GET  /catalogs/{name}` | 100 | 10.57 | 8.05 | +2.52 |
| `GET  /namespaces` | 0 | 7.54 | 7.71 | -0.16 |
| `GET  /namespaces` | 100 | 7.63 | 7.03 | +0.60 |
| `GET  /namespaces/{ns}` | 0 | 7.28 | 7.13 | +0.16 |
| `GET  /namespaces/{ns}` | 100 | 6.74 | 6.70 | +0.04 |
| `GET  /namespaces/{ns}/tables` | 0 | 8.27 | 7.63 | +0.64 |
| `GET  /namespaces/{ns}/tables` | 100 | 7.90 | 6.97 | +0.93 |
| `GET  /namespaces/{ns}/views` | 0 | 8.88 | 7.81 | +1.07 |
| `GET  /namespaces/{ns}/views` | 100 | 8.28 | 7.28 | +1.00 |
| `GET  /principal-roles` | 0 | 7.96 | 8.47 | -0.51 |
| `GET  /principal-roles` | 100 | 10.86 | 9.64 | +1.22 |
| `GET  /principal-roles/{name}` | 0 | 7.58 | 7.20 | +0.38 |
| `GET  /principal-roles/{name}` | 100 | 7.22 | 7.42 | -0.20 |
| `GET  /principal-roles/{n}/principals` | 0 | 8.60 | 8.19 | +0.41 |
| `GET  /principal-roles/{n}/principals` | 100 | 8.55 | 8.53 | +0.02 |
| `GET  /principals` | 0 | 11.18 | 10.41 | +0.78 |
| `GET  /principals` | 100 | 11.67 | 11.20 | +0.47 |
| `GET  /principals/{name}` | 0 | 7.98 | 7.71 | +0.27 |
| `GET  /principals/{name}` | 100 | 7.98 | 7.95 | +0.03 |

## Volume effect at index-present (isolates ENTITY volume)

| API | 0 | 100 |
|---|---|---|
| `GET  /catalog-roles/{r}/grants` | 9.32 | 8.21 |
| `GET  /catalogs` | 8.28 | 13.36 |
| `GET  /catalogs/{c}/catalog-roles` | 7.84 | 7.52 |
| `GET  /catalogs/{name}` | 7.17 | 8.05 |
| `GET  /namespaces` | 7.71 | 7.03 |
| `GET  /namespaces/{ns}` | 7.13 | 6.70 |
| `GET  /namespaces/{ns}/tables` | 7.63 | 6.97 |
| `GET  /namespaces/{ns}/views` | 7.81 | 7.28 |
| `GET  /principal-roles` | 8.47 | 9.64 |
| `GET  /principal-roles/{name}` | 7.20 | 7.42 |
| `GET  /principal-roles/{n}/principals` | 8.19 | 8.53 |
| `GET  /principals` | 10.41 | 11.20 |
| `GET  /principals/{name}` | 7.71 | 7.95 |

## Cold vs warm

Cold is **first touch after restart**, n=1, no median and no spread --
it is not repeatable without another restart. It also is not a pure
cache miss: `warm_up()` absorbs JVM and pool cost against a decoy
catalog, but any residue lands here.

| API | clones | index | cold (n=1) | warm | ratio |
|---|---:|:--:|---:|---:|---:|
| `GET  /catalog-roles/{r}/grants` | 0 | False | 76.62 | 8.21 | 9.3x |
| `GET  /catalog-roles/{r}/grants` | 0 | True | 65.50 | 9.32 | 7.0x |
| `GET  /catalog-roles/{r}/grants` | 100 | False | 16.64 | 7.73 | 2.2x |
| `GET  /catalog-roles/{r}/grants` | 100 | True | 74.35 | 8.21 | 9.1x |
| `GET  /catalogs` | 0 | False | 14.83 | 8.64 | 1.7x |
| `GET  /catalogs` | 0 | True | 13.98 | 8.28 | 1.7x |
| `GET  /catalogs` | 100 | False | 39.56 | 15.94 | 2.5x |
| `GET  /catalogs` | 100 | True | 66.08 | 13.36 | 4.9x |
| `GET  /catalogs/{c}/catalog-roles` | 0 | False | 17.52 | 8.11 | 2.2x |
| `GET  /catalogs/{c}/catalog-roles` | 0 | True | 12.57 | 7.84 | 1.6x |
| `GET  /catalogs/{c}/catalog-roles` | 100 | False | 13.70 | 6.36 | 2.2x |
| `GET  /catalogs/{c}/catalog-roles` | 100 | True | 14.95 | 7.52 | 2.0x |
| `GET  /catalogs/{name}` | 0 | False | 51.36 | 6.75 | 7.6x |
| `GET  /catalogs/{name}` | 0 | True | 11.75 | 7.17 | 1.6x |
| `GET  /catalogs/{name}` | 100 | False | 39.74 | 10.57 | 3.8x |
| `GET  /catalogs/{name}` | 100 | True | 14.08 | 8.05 | 1.7x |
| `GET  /namespaces` | 0 | False | 43.40 | 7.54 | 5.8x |
| `GET  /namespaces` | 0 | True | 98.53 | 7.71 | 12.8x |
| `GET  /namespaces` | 100 | False | 82.65 | 7.63 | 10.8x |
| `GET  /namespaces` | 100 | True | 39.96 | 7.03 | 5.7x |
| `GET  /namespaces/{ns}` | 0 | False | 70.71 | 7.28 | 9.7x |
| `GET  /namespaces/{ns}` | 0 | True | 26.73 | 7.13 | 3.7x |
| `GET  /namespaces/{ns}` | 100 | False | 23.05 | 6.74 | 3.4x |
| `GET  /namespaces/{ns}` | 100 | True | 48.41 | 6.70 | 7.2x |
| `GET  /namespaces/{ns}/tables` | 0 | False | 14.82 | 8.27 | 1.8x |
| `GET  /namespaces/{ns}/tables` | 0 | True | 70.73 | 7.63 | 9.3x |
| `GET  /namespaces/{ns}/tables` | 100 | False | 63.74 | 7.90 | 8.1x |
| `GET  /namespaces/{ns}/tables` | 100 | True | 21.68 | 6.97 | 3.1x |
| `GET  /namespaces/{ns}/views` | 0 | False | 13.81 | 8.88 | 1.6x |
| `GET  /namespaces/{ns}/views` | 0 | True | 12.07 | 7.81 | 1.5x |
| `GET  /namespaces/{ns}/views` | 100 | False | 15.05 | 8.28 | 1.8x |
| `GET  /namespaces/{ns}/views` | 100 | True | 12.56 | 7.28 | 1.7x |
| `GET  /principal-roles` | 0 | False | 12.85 | 7.96 | 1.6x |
| `GET  /principal-roles` | 0 | True | 33.69 | 8.47 | 4.0x |
| `GET  /principal-roles` | 100 | False | 28.92 | 10.86 | 2.7x |
| `GET  /principal-roles` | 100 | True | 13.45 | 9.64 | 1.4x |
| `GET  /principal-roles/{name}` | 0 | False | 15.19 | 7.58 | 2.0x |
| `GET  /principal-roles/{name}` | 0 | True | 12.17 | 7.20 | 1.7x |
| `GET  /principal-roles/{name}` | 100 | False | 47.06 | 7.22 | 6.5x |
| `GET  /principal-roles/{name}` | 100 | True | 12.96 | 7.42 | 1.7x |
| `GET  /principal-roles/{n}/principals` | 0 | False | 13.41 | 8.60 | 1.6x |
| `GET  /principal-roles/{n}/principals` | 0 | True | 26.58 | 8.19 | 3.2x |
| `GET  /principal-roles/{n}/principals` | 100 | False | 15.69 | 8.55 | 1.8x |
| `GET  /principal-roles/{n}/principals` | 100 | True | 13.45 | 8.53 | 1.6x |
| `GET  /principals` | 0 | False | 14.93 | 11.18 | 1.3x |
| `GET  /principals` | 0 | True | 16.92 | 10.41 | 1.6x |
| `GET  /principals` | 100 | False | 16.97 | 11.67 | 1.5x |
| `GET  /principals` | 100 | True | 15.53 | 11.20 | 1.4x |
| `GET  /principals/{name}` | 0 | False | 59.53 | 7.98 | 7.5x |
| `GET  /principals/{name}` | 0 | True | 12.14 | 7.71 | 1.6x |
| `GET  /principals/{name}` | 100 | False | 12.50 | 7.98 | 1.6x |
| `GET  /principals/{name}` | 100 | True | 71.82 | 7.95 | 9.0x |
