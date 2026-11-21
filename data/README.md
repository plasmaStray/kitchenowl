# Production catalog snapshots

Snapshots contain one household's categories and catalog items. They include
`support`, the item frequency score used by search suggestions, and exclude
users, shopping lists, purchase history, recipes, and recommendation links.
`support` is calculated from shopping history by KitchenOwl's daily analysis;
it is a fraction, so `0.25` means the item appeared in a quarter of the analyzed
shopping instances. A value of `0.0` means no positive score was stored for it.

To export the current catalog from the production SQLite database, run this from
the repository root (replace the date and output filename as appropriate):

```sh
ssh us1 'python3 - --household-id 1 --snapshot-date 2026-11-21' \
  < scripts/export_catalog_snapshot.py \
  > data/production-catalog-household-1-2026-11-21.json
```

The exporter opens SQLite in read-only mode. Review the generated JSON and its
diff before committing a dated snapshot to this branch. Snapshot schema version
2 includes item `support`; version 1 snapshots predate that field.
