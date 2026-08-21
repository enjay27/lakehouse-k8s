# API latency sweep

- **run_id**: 20260822-041107
- **realm**: POLARIS
- **schema**: polaris_schema
- **polaris**: http://192.168.139.2:8181

Every number below comes from calls aimed at REAL fixture entities.
Cloned rows supply volume only -- they are synthetic, have no storage
behind them, and nothing is measured against them.

## Control -- read this first

`POST /oauth/tokens` across all 4 cells: median 0.00 ms, spread 0.00 ms (0.00 .. 0.00).

It resolves no grants, so it should not move. Any effect reported
below that is smaller than this spread is noise.

## Index effect (isolates GRANT volume)

| API | clones | without | with | delta |
|---|---:|---:|---:|---:|
| `GET  /catalog-roles/{r}/grants` | 0 | 0.00 | 0.00 | +0.00 |
| `GET  /catalog-roles/{r}/grants` | 10 | 0.00 | 0.00 | +0.00 |
| `GET  /catalogs` | 0 | 0.00 | 0.00 | -0.00 |
| `GET  /catalogs` | 10 | 0.00 | 0.00 | -0.00 |
| `GET  /catalogs/{c}/catalog-roles` | 0 | 0.00 | 0.00 | -0.00 |
| `GET  /catalogs/{c}/catalog-roles` | 10 | 0.00 | 0.00 | -0.00 |
| `GET  /catalogs/{name}` | 0 | 0.00 | 0.00 | -0.00 |
| `GET  /catalogs/{name}` | 10 | 0.00 | 0.00 | -0.00 |
| `GET  /namespaces` | 0 | 0.00 | 0.00 | +0.00 |
| `GET  /namespaces` | 10 | 0.00 | 0.00 | -0.00 |
| `GET  /namespaces/{ns}` | 0 | 0.00 | 0.00 | -0.00 |
| `GET  /namespaces/{ns}` | 10 | 0.00 | 0.00 | +0.00 |
| `GET  /namespaces/{ns}/tables` | 0 | 0.00 | 0.00 | +0.00 |
| `GET  /namespaces/{ns}/tables` | 10 | 0.00 | 0.00 | -0.00 |
| `GET  /namespaces/{ns}/views` | 0 | 0.00 | 0.00 | +0.00 |
| `GET  /namespaces/{ns}/views` | 10 | 0.00 | 0.00 | +0.00 |
| `GET  /principal-roles` | 0 | 0.00 | 0.00 | +0.00 |
| `GET  /principal-roles` | 10 | 0.00 | 0.00 | +0.00 |
| `GET  /principal-roles/{name}` | 0 | 0.00 | 0.00 | +0.00 |
| `GET  /principal-roles/{name}` | 10 | 0.00 | 0.00 | -0.00 |
| `GET  /principal-roles/{n}/principals` | 0 | 0.00 | 0.00 | +0.00 |
| `GET  /principal-roles/{n}/principals` | 10 | 0.00 | 0.00 | +0.00 |
| `GET  /principals` | 0 | 0.00 | 0.00 | +0.00 |
| `GET  /principals` | 10 | 0.00 | 0.00 | +0.00 |
| `GET  /principals/{name}` | 0 | 0.00 | 0.00 | -0.00 |
| `GET  /principals/{name}` | 10 | 0.00 | 0.00 | +0.00 |

## Volume effect at index-present (isolates ENTITY volume)

| API | 0 | 10 |
|---|---|---|
| `GET  /catalog-roles/{r}/grants` | 0.00 | 0.00 |
| `GET  /catalogs` | 0.00 | 0.00 |
| `GET  /catalogs/{c}/catalog-roles` | 0.00 | 0.00 |
| `GET  /catalogs/{name}` | 0.00 | 0.00 |
| `GET  /namespaces` | 0.00 | 0.00 |
| `GET  /namespaces/{ns}` | 0.00 | 0.00 |
| `GET  /namespaces/{ns}/tables` | 0.00 | 0.00 |
| `GET  /namespaces/{ns}/views` | 0.00 | 0.00 |
| `GET  /principal-roles` | 0.00 | 0.00 |
| `GET  /principal-roles/{name}` | 0.00 | 0.00 |
| `GET  /principal-roles/{n}/principals` | 0.00 | 0.00 |
| `GET  /principals` | 0.00 | 0.00 |
| `GET  /principals/{name}` | 0.00 | 0.00 |

## Cold vs warm

Cold is **first touch after restart**, n=1, no median and no spread --
it is not repeatable without another restart. It also is not a pure
cache miss: `warm_up()` absorbs JVM and pool cost against a decoy
catalog, but any residue lands here.

| API | clones | index | cold (n=1) | warm | ratio |
|---|---:|:--:|---:|---:|---:|
| `GET  /catalog-roles/{r}/grants` | 0 | False | 0.00 | 0.00 | 1.4x |
| `GET  /catalog-roles/{r}/grants` | 0 | True | 0.00 | 0.00 | 1.1x |
| `GET  /catalog-roles/{r}/grants` | 10 | False | 0.00 | 0.00 | 0.9x |
| `GET  /catalog-roles/{r}/grants` | 10 | True | 0.00 | 0.00 | 1.1x |
| `GET  /catalogs` | 0 | False | 0.00 | 0.00 | 1.1x |
| `GET  /catalogs` | 0 | True | 0.00 | 0.00 | 0.9x |
| `GET  /catalogs` | 10 | False | 0.00 | 0.00 | 1.0x |
| `GET  /catalogs` | 10 | True | 0.00 | 0.00 | 0.9x |
| `GET  /catalogs/{c}/catalog-roles` | 0 | False | 0.00 | 0.00 | 1.1x |
| `GET  /catalogs/{c}/catalog-roles` | 0 | True | 0.00 | 0.00 | 0.9x |
| `GET  /catalogs/{c}/catalog-roles` | 10 | False | 0.00 | 0.00 | 1.1x |
| `GET  /catalogs/{c}/catalog-roles` | 10 | True | 0.00 | 0.00 | 1.0x |
| `GET  /catalogs/{name}` | 0 | False | 0.00 | 0.00 | 0.9x |
| `GET  /catalogs/{name}` | 0 | True | 0.00 | 0.00 | 0.9x |
| `GET  /catalogs/{name}` | 10 | False | 0.00 | 0.00 | 1.0x |
| `GET  /catalogs/{name}` | 10 | True | 0.00 | 0.00 | 1.0x |
| `GET  /namespaces` | 0 | False | 0.00 | 0.00 | 1.3x |
| `GET  /namespaces` | 0 | True | 0.00 | 0.00 | 0.9x |
| `GET  /namespaces` | 10 | False | 0.00 | 0.00 | 1.0x |
| `GET  /namespaces` | 10 | True | 0.00 | 0.00 | 1.0x |
| `GET  /namespaces/{ns}` | 0 | False | 0.00 | 0.00 | 1.2x |
| `GET  /namespaces/{ns}` | 0 | True | 0.00 | 0.00 | 1.0x |
| `GET  /namespaces/{ns}` | 10 | False | 0.00 | 0.00 | 0.9x |
| `GET  /namespaces/{ns}` | 10 | True | 0.00 | 0.00 | 1.1x |
| `GET  /namespaces/{ns}/tables` | 0 | False | 0.00 | 0.00 | 1.5x |
| `GET  /namespaces/{ns}/tables` | 0 | True | 0.00 | 0.00 | 1.2x |
| `GET  /namespaces/{ns}/tables` | 10 | False | 0.00 | 0.00 | 1.3x |
| `GET  /namespaces/{ns}/tables` | 10 | True | 0.00 | 0.00 | 1.0x |
| `GET  /namespaces/{ns}/views` | 0 | False | 0.00 | 0.00 | 1.1x |
| `GET  /namespaces/{ns}/views` | 0 | True | 0.00 | 0.00 | 1.0x |
| `GET  /namespaces/{ns}/views` | 10 | False | 0.00 | 0.00 | 0.9x |
| `GET  /namespaces/{ns}/views` | 10 | True | 0.00 | 0.00 | 0.9x |
| `GET  /principal-roles` | 0 | False | 0.00 | 0.00 | 1.1x |
| `GET  /principal-roles` | 0 | True | 0.00 | 0.00 | 1.1x |
| `GET  /principal-roles` | 10 | False | 0.00 | 0.00 | 1.1x |
| `GET  /principal-roles` | 10 | True | 0.00 | 0.00 | 0.9x |
| `GET  /principal-roles/{name}` | 0 | False | 0.00 | 0.00 | 1.6x |
| `GET  /principal-roles/{name}` | 0 | True | 0.00 | 0.00 | 1.3x |
| `GET  /principal-roles/{name}` | 10 | False | 0.00 | 0.00 | 1.1x |
| `GET  /principal-roles/{name}` | 10 | True | 0.00 | 0.00 | 1.3x |
| `GET  /principal-roles/{n}/principals` | 0 | False | 0.00 | 0.00 | 1.3x |
| `GET  /principal-roles/{n}/principals` | 0 | True | 0.00 | 0.00 | 1.2x |
| `GET  /principal-roles/{n}/principals` | 10 | False | 0.00 | 0.00 | 1.1x |
| `GET  /principal-roles/{n}/principals` | 10 | True | 0.00 | 0.00 | 1.1x |
| `GET  /principals` | 0 | False | 0.00 | 0.00 | 1.2x |
| `GET  /principals` | 0 | True | 0.00 | 0.00 | 1.2x |
| `GET  /principals` | 10 | False | 0.00 | 0.00 | 0.8x |
| `GET  /principals` | 10 | True | 0.00 | 0.00 | 1.1x |
| `GET  /principals/{name}` | 0 | False | 0.00 | 0.00 | 2.0x |
| `GET  /principals/{name}` | 0 | True | 0.00 | 0.00 | 1.1x |
| `GET  /principals/{name}` | 10 | False | 0.00 | 0.00 | 1.1x |
| `GET  /principals/{name}` | 10 | True | 0.00 | 0.00 | 1.1x |
