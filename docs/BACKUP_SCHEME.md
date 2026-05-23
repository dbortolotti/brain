# Backup Scheme

Brain backups are timestamped backup directories with a manifest. The backup job is implemented by `scripts/backup_stores.py`.

Production verification checks the latest backup manifest as part of:

```bash
make prod-check
```

## Goals

The backup scheme must preserve enough state to rebuild Brain after local disk loss or a bad deploy:

- Brain SQLite databases under the configured data roots and runtime system root.
- Raw source/data directories.
- Vector-store data, either as a pgvector SQL dump or LanceDB archives, depending on the configured vector backend.
- Production secret files needed to restart the services.
- Neo4j graph state when graph data exists.
- A machine-readable manifest describing what was captured and verified.
- Optional Google Drive replication.

Brain DB remains the authoritative memory store. Cognee, pgvector/LanceDB, and Neo4j are treated as rebuildable projections where possible, but they are still backed up to reduce restore time and preserve debugging context.

## Default Locations

Local defaults come from `.env.example`; deployed defaults are rendered by the production deployment scripts and checked-in environment configs.

```env
BRAIN_BACKUP_DIR=/Volumes/xpg_usb4/prod/brain/shared/backups
BRAIN_GOOGLE_DRIVE_BACKUP_ENABLED=true
BRAIN_GOOGLE_DRIVE_FOLDER=backup/brain
BRAIN_GOOGLE_DRIVE_LOCAL_PATH=
BRAIN_GOOGLE_DRIVE_REMOTE=
BRAIN_NEO4J_DUMP_ENABLED=false
BRAIN_NEO4J_STOP_FOR_DUMP=false
```

Production renders `BRAIN_GOOGLE_DRIVE_BACKUP_ENABLED=true`, `BRAIN_NEO4J_DUMP_ENABLED=true`, and `BRAIN_NEO4J_STOP_FOR_DUMP=true`. Staging renders `BRAIN_GOOGLE_DRIVE_BACKUP_ENABLED=false`, `BRAIN_NEO4J_DUMP_ENABLED=true`, and `BRAIN_NEO4J_STOP_FOR_DUMP=true`. The checked-in prod and staging configs currently use `VECTOR_DB_PROVIDER=pgvector`, so `pgvector/` is the expected vector-store archive directory in both environments; `lancedb/` is used when LanceDB is the configured vector backend. The deployed auth registry file is configured as `BRAIN_AUTH_USERS_FILE` in prod, staging, and QA, but it is not part of the default backup inputs unless the script is explicitly extended to capture it.

Each backup run creates:

```text
$BRAIN_BACKUP_DIR/YYYYMMDD_HHMMSS/
```

A typical run directory contains:

```text
manifest.json
sqlite/
raw_data/
pgvector/
lancedb/
secrets/
neo4j/
neo4j-counts.json
```

Some directories are omitted when the corresponding source does not exist or is disabled.

## Running A Backup

Local prod, staging, and QA deploys install a daily system LaunchDaemon from `deployment/launchd/com.brain.maintenance.plist.template`. The rendered production label is `com.brain.prod.maintenance` and runs as `oric_prod`; staging renders as `com.brain.staging.maintenance` and runs as `oric_staging`; QA renders as `com.brain.qa.maintenance` and runs as `oric`. The maintenance job runs `scripts/nightly_maintenance.py`, which runs `scripts/backup_stores.py`.

Run the backup script directly with the configured environment:

```bash
ENV_FILE=/Volumes/xpg_usb4/prod/brain/shared/secrets/brain.env uv run python scripts/backup_stores.py
```

Override the backup root for a one-off run:

```bash
ENV_FILE=/Volumes/xpg_usb4/prod/brain/shared/secrets/brain.env uv run python scripts/backup_stores.py --backup-dir /Volumes/xpg_usb4/prod/brain/shared/backups/manual
```

Override the shared data root:

```bash
ENV_FILE=/Volumes/xpg_usb4/prod/brain/shared/secrets/brain.env uv run python scripts/backup_stores.py --data-dir /Volumes/xpg_usb4/prod/brain/shared/data
```

Skip Google Drive replication for a local test:

```bash
ENV_FILE=/Volumes/xpg_usb4/prod/brain/shared/secrets/brain.env uv run python scripts/backup_stores.py --skip-google-drive
```

If `--skip-google-drive` is used while Google Drive backup is enabled, the manifest records that replication as skipped instead of verified.

## Manifest Contract

Every backup writes `manifest.json` with this shape:

```json
{
  "timestamp": "20260510_120000",
  "backup_dir": "/Volumes/xpg_usb4/prod/brain/shared/backups/20260510_120000",
  "data_root": "/Volumes/xpg_usb4/prod/brain/shared/data",
  "data_roots": ["/Volumes/xpg_usb4/prod/brain/shared/data", "/Volumes/xpg_usb4/prod/brain/shared/data/data"],
  "sqlite_roots": ["/Volumes/xpg_usb4/prod/brain/shared/data", "/Volumes/xpg_usb4/prod/brain/shared/data/data", "/Volumes/xpg_usb4/prod/brain/shared/data/system"],
  "sqlite": [],
  "lancedb": [],
  "pgvector": [],
  "raw_data": [],
  "secrets": [],
  "neo4j": [],
  "google_drive": null,
  "blockers": []
}
```

`google_drive` is populated after the local manifest is written when Drive replication runs. If `--skip-google-drive` is used while Google Drive backup is enabled, the manifest records `{"skipped": true}` for that step. `blockers` means the run finished but missed something operationally important. Production verification treats blockers as failures.

## SQLite Backups

The backup script searches the configured data roots and runtime system root for SQLite databases:

```text
*.sqlite
*.sqlite3
*.db
system/databases/*
```

It only backs up files that SQLite identifies as databases. Each SQLite file is copied using SQLite's online backup API, not a raw file copy. The backup is then checked with:

```sql
PRAGMA integrity_check;
```

Manifest entries look like:

```json
{
  "source": "/Volumes/xpg_usb4/prod/brain/shared/data/system/databases/cognee_db",
  "backup": "/Volumes/xpg_usb4/prod/brain/shared/backups/20260510_120000/sqlite/system__databases__cognee_db",
  "integrity_check": "ok"
}
```

Production verification requires:

- At least one SQLite backup entry.
- The configured Brain SQLite database to be included.
- `integrity_check` equal to `ok`.
- The backup file still present on disk.

## Raw Data Archive

Each data root in the deduplicated backup set is archived as:

```text
raw_data/<data-root-name>.tar.gz
```

This preserves source data and runtime files that are not captured by the SQLite- or vector-store-specific paths.

If a data root is missing, the manifest receives a blocker for that root and no raw-data archive is written for it.

## Vector Store Backups

The script backs up exactly one vector-store family based on `VECTOR_DB_PROVIDER`.

### pgvector Backup

When `VECTOR_DB_PROVIDER=pgvector`, the backup script creates a Postgres dump of the configured vector database. The dump is written to:

```text
pgvector/<db-name>.sql
```

The dump is produced with Docker when available. The manifest entry records the dump method, database name, return code, captured stderr, and whether the dump was verified as non-empty.

If Docker is not available, the manifest receives a blocker and the pgvector backup does not complete.

If the dump is produced but not verified as non-empty, the script raises an error.

### LanceDB Archive

When the vector backend is LanceDB, the script archives:

- The configured `VECTOR_DB_URL`.
- Any path under the shared data root whose name contains `lancedb`.

If `VECTOR_DB_URL` is not absolute, the script resolves it relative to the shared data root before checking for the path.

Each candidate is stored as:

```text
lancedb/<source-name>.tar.gz
```

If no LanceDB path is found, the manifest receives a blocker because production verification expects a vector-store artifact when LanceDB is the configured backend.

## Secrets Archive

The backup script archives existing secret files from:

```text
$ENV_FILE
$BRAIN_AUTH_PASSWORD_FILE
$BRAIN_AUTH_STATE_PATH
```

The archive is written to:

```text
secrets/secrets.tar.gz
```

If no secret files are found, the manifest receives a blocker. The deployed auth registry file (`BRAIN_AUTH_USERS_FILE`, rendered by production deploys under the environment's `shared/secrets/brain-auth-users.json`) is not assumed to be captured by this backup unless you have explicitly extended the backup inputs.

Production secret rendering and conflict rules are documented in [Production Secrets](production-secrets.md).

## Neo4j Backup

The script first attempts a read-only graph count with `cypher-shell` and writes `neo4j-counts.json` when available. A successful count check is recorded as a verified Neo4j manifest entry.

If `BRAIN_NEO4J_DUMP_ENABLED=false`:

- Empty graph: no dump is required.
- Non-empty graph: the manifest receives a blocker, and the script may create a raw live archive as a fallback.

Raw live Neo4j archives are not considered consistent backups.

For a consistent Neo4j dump:

```env
BRAIN_NEO4J_DUMP_ENABLED=true
```

When Docker is available, the script runs `neo4j-admin database dump` inside the configured Neo4j Docker container and copies the dump into:

```text
neo4j/neo4j.dump
```

When Docker is not available, it uses local `neo4j-admin` and writes:

```text
neo4j/<GRAPH_DATABASE_NAME>.dump
```

If the local database is in use, enable a stop-the-world dump window:

```env
BRAIN_NEO4J_STOP_FOR_DUMP=true
```

With this enabled, the script stops the configured Neo4j service, runs the dump, restarts Neo4j, and waits for readiness.

## Google Drive Replication

When `BRAIN_GOOGLE_DRIVE_BACKUP_ENABLED=true`, the backup is replicated after the local manifest is written.

Preferred local-mounted Drive path:

```env
BRAIN_GOOGLE_DRIVE_LOCAL_PATH=/path/to/local/Google Drive
BRAIN_GOOGLE_DRIVE_FOLDER=backup/brain
```

The script copies the complete run directory to:

```text
$BRAIN_GOOGLE_DRIVE_LOCAL_PATH/$BRAIN_GOOGLE_DRIVE_FOLDER/YYYYMMDD_HHMMSS/
```

If no local path is configured, the script uses `rclone` and targets:

```text
$BRAIN_GOOGLE_DRIVE_REMOTE:$BRAIN_GOOGLE_DRIVE_FOLDER/YYYYMMDD_HHMMSS/
```

Replication is considered verified only when the copied/uploaded directory contains `manifest.json`. The manifest records either:

```json
{"method": "local_path", "path": "...", "verified": true}
```

or:

```json
{"method": "rclone", "remote": "...", "verified": true}
```

If `--skip-google-drive` is used, the manifest records the Drive step as skipped when Google Drive backup is enabled.

Production verification requires Google Drive verification when `BRAIN_GOOGLE_DRIVE_BACKUP_ENABLED=true`.

## Production Verification

`scripts/verify_mcp_production.py` checks the latest manifest under `BRAIN_BACKUP_DIR` unless `--skip-backups` is passed. It also checks that the configured runtime paths are absolute and under `shared/data`.

It fails when:

- The backup directory does not exist.
- No `*/manifest.json` files exist.
- The latest manifest contains blockers.
- SQLite backups are missing or fail integrity checks.
- The configured Brain SQLite database was not included.
- The configured vector-store artifact is missing or unverified.
- Raw data or secrets archives are missing.
- No verified Neo4j count or dump exists.
- Google Drive replication is enabled but not verified.

Run:

```bash
ENV_FILE=/Volumes/xpg_usb4/prod/brain/shared/secrets/brain.env make prod-check
```

Use this only when intentionally skipping backup validation:

```bash
ENV_FILE=/Volumes/xpg_usb4/prod/brain/shared/secrets/brain.env uv run python scripts/verify_mcp_production.py --skip-backups
```

## Restore Outline

Stop Brain services before restoring:

```bash
sudo launchctl bootout system /Library/LaunchDaemons/com.brain.prod.mcp.plist
sudo launchctl bootout system /Library/LaunchDaemons/com.brain.prod.slack-agent.plist
sudo launchctl bootout system /Library/LaunchDaemons/com.brain.prod.ui.plist
```

Restore secrets:

```bash
mkdir -p /Volumes/xpg_usb4/prod/brain/shared/secrets
tar -xzf BACKUP_DIR/secrets/secrets.tar.gz -C /Volumes/xpg_usb4/prod/brain/shared/secrets
chmod 600 /Volumes/xpg_usb4/prod/brain/shared/secrets/*
```

Restore SQLite databases by copying the selected files from `sqlite/` back to their manifest `source` paths.

Restore raw data from the matching archive in `raw_data/` for each archived data root.

Restore vector data from the matching archive for the configured backend:

- `pgvector/<db-name>.sql` for pgvector deployments.
- `lancedb/<source-name>.tar.gz` for LanceDB deployments.

Restore Neo4j only from a verified dump:

```bash
neo4j-admin database load neo4j --from-path=BACKUP_DIR/neo4j --overwrite-destination=true
```

After restoring, restart services and run:

```bash
ENV_FILE=/Volumes/xpg_usb4/prod/brain/shared/secrets/brain.env make prod-check
```

## Operating Rules

- Run a backup before any destructive migration, production deploy, production promotion, or manual data repair.
- Treat `manifest.json` as the source of truth for what was captured.
- Do not rely on raw live Neo4j archives for restore.
- Keep `ENV_FILE`, `BRAIN_AUTH_PASSWORD_FILE`, and `BRAIN_AUTH_STATE_PATH` in the secrets archive.
- Do not assume `BRAIN_AUTH_USERS_FILE` is captured unless the backup inputs were explicitly extended to include it.
- Keep at least one verified off-device copy when Google Drive backup is enabled.
- Resolve manifest blockers before considering a backup usable.

<!-- brain-doc-source-hash: 498b9587c35d3a30a4d3c4652d60277904a5ab01b15b7bb7c3f6482c92834c3c -->
