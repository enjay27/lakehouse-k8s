# API latency sweep

- **run_id**: 20260822-052837
- **realm**: POLARIS
- **schema**: polaris_schema
- **polaris**: http://192.168.139.2:8181

Every number below comes from calls aimed at REAL fixture entities.
Cloned rows supply volume only -- they are synthetic, have no storage
behind them, and nothing is measured against them.

## Control -- read this first

`POST /oauth/tokens` across all 4 cells: median 0.00 ms, spread 0.00 ms (0.00 .. 0.00).

It resolves no grants, so it should not move -- and it did not.

**But do NOT use this spread as the noise floor.** It is a spread
between MEDIANS, and a median of 15 calls is stable by
construction; it says nothing about whether any one median is
trustworthy. The `noise` column below carries the within-cell
min/max spread, which does. An earlier version of this report made
exactly that substitution and bounded 2 ms claims with a 0.6 ms
figure while the true spread was 60 ms.

## THIS RUN DOES NOT MEASURE WHAT THE TABLES SAY

- **clones=0, index=False**
  - 7,319 grant_records -- below the 30,009 at which notebook 02 first measured an index effect, so an absence of effect here is uninformative
- **clones=0, index=True**
  - 7,319 grant_records -- below the 30,009 at which notebook 02 first measured an index effect, so an absence of effect here is uninformative
- **clones=10, index=False**
  - 7,319 grant_records -- below the 30,009 at which notebook 02 first measured an index effect, so an absence of effect here is uninformative
- **clones=10, index=True**
  - 7,319 grant_records -- below the 30,009 at which notebook 02 first measured an index effect, so an absence of effect here is uninformative

Read the tables below as a proof that the harness runs, not as a
result. Fixing the labels would not help: the cells have to be
re-measured at a volume where the planner behaves differently.

## Index effect (isolates GRANT volume)

`noise` is the worst within-cell min/max spread for that API -- the
real floor. A delta smaller than it is not a measurement.

| API | clones | without | with | delta | noise | verdict |
|---|---:|---:|---:|---:|---:|:--|
| `GET  /catalog-roles/{r}/grants` | 0 | 0.00 | 0.00 | -0.00 | 0.00 | NOISE |
| `GET  /catalog-roles/{r}/grants` | 10 | 0.00 | 0.00 | +0.00 | 0.00 | NOISE |
| `GET  /catalogs` | 0 | 0.00 | 0.00 | +0.00 | 0.00 | NOISE |
| `GET  /catalogs` | 10 | 0.00 | 0.00 | +0.00 | 0.00 | above floor |
| `GET  /catalogs/{c}/catalog-roles` | 0 | 0.00 | 0.00 | +0.00 | 0.00 | NOISE |
| `GET  /catalogs/{c}/catalog-roles` | 10 | 0.00 | 0.00 | +0.00 | 0.00 | NOISE |
| `GET  /catalogs/{name}` | 0 | 0.00 | 0.00 | +0.00 | 0.00 | NOISE |
| `GET  /catalogs/{name}` | 10 | 0.00 | 0.00 | +0.00 | 0.00 | NOISE |
| `GET  /namespaces` | 0 | 0.00 | 0.00 | +0.00 | 0.00 | above floor |
| `GET  /namespaces` | 10 | 0.00 | 0.00 | +0.00 | 0.00 | above floor |
| `GET  /namespaces/{ns}` | 0 | 0.00 | 0.00 | +0.00 | 0.00 | NOISE |
| `GET  /namespaces/{ns}` | 10 | 0.00 | 0.00 | -0.00 | 0.00 | NOISE |
| `GET  /namespaces/{ns}/tables` | 0 | 0.00 | 0.00 | +0.00 | 0.00 | NOISE |
| `GET  /namespaces/{ns}/tables` | 10 | 0.00 | 0.00 | +0.00 | 0.00 | NOISE |
| `GET  /namespaces/{ns}/views` | 0 | 0.00 | 0.00 | +0.00 | 0.00 | NOISE |
| `GET  /namespaces/{ns}/views` | 10 | 0.00 | 0.00 | +0.00 | 0.00 | NOISE |
| `GET  /principal-roles` | 0 | 0.00 | 0.00 | +0.00 | 0.00 | NOISE |
| `GET  /principal-roles` | 10 | 0.00 | 0.00 | +0.00 | 0.00 | NOISE |
| `GET  /principal-roles/{name}` | 0 | 0.00 | 0.00 | +0.00 | 0.00 | above floor |
| `GET  /principal-roles/{name}` | 10 | 0.00 | 0.00 | +0.00 | 0.00 | NOISE |
| `GET  /principal-roles/{n}/principals` | 0 | 0.00 | 0.00 | +0.00 | 0.00 | above floor |
| `GET  /principal-roles/{n}/principals` | 10 | 0.00 | 0.00 | +0.00 | 0.00 | above floor |
| `GET  /principals` | 0 | 0.00 | 0.00 | +0.00 | 0.00 | above floor |
| `GET  /principals` | 10 | 0.00 | 0.00 | -0.00 | 0.00 | NOISE |
| `GET  /principals/{name}` | 0 | 0.00 | 0.00 | +0.00 | 0.00 | NOISE |
| `GET  /principals/{name}` | 10 | 0.00 | 0.00 | +0.00 | 0.00 | NOISE |

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
| `GET  /catalog-roles/{r}/grants` | 0 | False | 0.00 | 0.00 | 1.5x |
| `GET  /catalog-roles/{r}/grants` | 0 | True | 0.00 | 0.00 | 1.1x |
| `GET  /catalog-roles/{r}/grants` | 10 | False | 0.00 | 0.00 | 0.9x |
| `GET  /catalog-roles/{r}/grants` | 10 | True | 0.00 | 0.00 | 1.1x |
| `GET  /catalogs` | 0 | False | 0.00 | 0.00 | 1.2x |
| `GET  /catalogs` | 0 | True | 0.00 | 0.00 | 1.0x |
| `GET  /catalogs` | 10 | False | 0.00 | 0.00 | 0.9x |
| `GET  /catalogs` | 10 | True | 0.00 | 0.00 | 1.0x |
| `GET  /catalogs/{c}/catalog-roles` | 0 | False | 0.00 | 0.00 | 1.2x |
| `GET  /catalogs/{c}/catalog-roles` | 0 | True | 0.00 | 0.00 | 0.9x |
| `GET  /catalogs/{c}/catalog-roles` | 10 | False | 0.00 | 0.00 | 1.2x |
| `GET  /catalogs/{c}/catalog-roles` | 10 | True | 0.00 | 0.00 | 1.2x |
| `GET  /catalogs/{name}` | 0 | False | 0.00 | 0.00 | 1.1x |
| `GET  /catalogs/{name}` | 0 | True | 0.00 | 0.00 | 1.0x |
| `GET  /catalogs/{name}` | 10 | False | 0.00 | 0.00 | 1.0x |
| `GET  /catalogs/{name}` | 10 | True | 0.00 | 0.00 | 1.2x |
| `GET  /namespaces` | 0 | False | 0.00 | 0.00 | 1.1x |
| `GET  /namespaces` | 0 | True | 0.00 | 0.00 | 1.0x |
| `GET  /namespaces` | 10 | False | 0.00 | 0.00 | 0.9x |
| `GET  /namespaces` | 10 | True | 0.00 | 0.00 | 1.2x |
| `GET  /namespaces/{ns}` | 0 | False | 0.00 | 0.00 | 1.1x |
| `GET  /namespaces/{ns}` | 0 | True | 0.00 | 0.00 | 1.1x |
| `GET  /namespaces/{ns}` | 10 | False | 0.00 | 0.00 | 1.2x |
| `GET  /namespaces/{ns}` | 10 | True | 0.00 | 0.00 | 1.0x |
| `GET  /namespaces/{ns}/tables` | 0 | False | 0.00 | 0.00 | 1.1x |
| `GET  /namespaces/{ns}/tables` | 0 | True | 0.00 | 0.00 | 0.9x |
| `GET  /namespaces/{ns}/tables` | 10 | False | 0.00 | 0.00 | 0.9x |
| `GET  /namespaces/{ns}/tables` | 10 | True | 0.00 | 0.00 | 0.9x |
| `GET  /namespaces/{ns}/views` | 0 | False | 0.00 | 0.00 | 1.1x |
| `GET  /namespaces/{ns}/views` | 0 | True | 0.00 | 0.00 | 0.9x |
| `GET  /namespaces/{ns}/views` | 10 | False | 0.00 | 0.00 | 0.9x |
| `GET  /namespaces/{ns}/views` | 10 | True | 0.00 | 0.00 | 1.1x |
| `GET  /principal-roles` | 0 | False | 0.00 | 0.00 | 1.1x |
| `GET  /principal-roles` | 0 | True | 0.00 | 0.00 | 1.1x |
| `GET  /principal-roles` | 10 | False | 0.00 | 0.00 | 0.9x |
| `GET  /principal-roles` | 10 | True | 0.00 | 0.00 | 0.9x |
| `GET  /principal-roles/{name}` | 0 | False | 0.00 | 0.00 | 1.3x |
| `GET  /principal-roles/{name}` | 0 | True | 0.00 | 0.00 | 1.4x |
| `GET  /principal-roles/{name}` | 10 | False | 0.00 | 0.00 | 1.1x |
| `GET  /principal-roles/{name}` | 10 | True | 0.00 | 0.00 | 1.1x |
| `GET  /principal-roles/{n}/principals` | 0 | False | 0.00 | 0.00 | 1.0x |
| `GET  /principal-roles/{n}/principals` | 0 | True | 0.00 | 0.00 | 1.1x |
| `GET  /principal-roles/{n}/principals` | 10 | False | 0.00 | 0.00 | 0.9x |
| `GET  /principal-roles/{n}/principals` | 10 | True | 0.00 | 0.00 | 1.0x |
| `GET  /principals` | 0 | False | 0.00 | 0.00 | 1.3x |
| `GET  /principals` | 0 | True | 0.00 | 0.00 | 1.1x |
| `GET  /principals` | 10 | False | 0.00 | 0.00 | 1.2x |
| `GET  /principals` | 10 | True | 0.00 | 0.00 | 0.9x |
| `GET  /principals/{name}` | 0 | False | 0.00 | 0.00 | 1.9x |
| `GET  /principals/{name}` | 0 | True | 0.00 | 0.00 | 1.1x |
| `GET  /principals/{name}` | 10 | False | 0.00 | 0.00 | 1.1x |
| `GET  /principals/{name}` | 10 | True | 0.00 | 0.00 | 1.0x |
