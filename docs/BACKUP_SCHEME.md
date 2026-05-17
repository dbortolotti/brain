# Backup Scheme

Brain backups are timestamped filesystem snapshots with a manifest. The backup
job is implemented by `scripts/backup_stores.py` and exposed through:

```bash
make backup
```

Production verification checks the latest backup manifest as part of:

```bash
make prod-check
```

## Goals

The backup scheme must preserve enough state to rebuild Brain after local disk
loss or a bad deploy:

- Brain SQLite databases under the shared data root.
- Raw source/data directories.
- Vector-store data, either as a pgvector SQL dump or LanceDB archives,
  depending on the configured vector backend.
- Production secret files needed to restart the services.
- Neo4j graph state when graph data exists.
- A machine-readable manifest describing what was captured and verified.
- Optional Google Drive replication.

Brain DB remains the authoritative memory store. Cognee, pgvector/LanceDB, and
Neo4j are treated as rebuildable projections where possible, but they are still
backed up to reduce restore time and preserve debugging context.

## Default Locations

Local defaults come from `.env.example`; production defaults are rendered by the
production deployment scripts.

```env
BRAIN_BACKUP_DIR=/Volumes/xpg_usb4/prod/brain/shared/backups
BRAIN_GOOGLE_DRIVE_BACKUP_ENABLED=true
BRAIN_GOOGLE_DRIVE_FOLDER=backup/brain
BRAIN_GOOGLE_DRIVE_LOCAL_PATH=
BRAIN_NEO4J_DUMP_ENABLED=false
BRAIN_NEO4J_STOP_FOR_DUMP=false
```

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

Some directories are omitted when the corresponding source does not exist or is
disabled. Current production uses `VECTOR_DB_PROVIDER=pgvector`, so `pgvector/`
is the expected vector-store archive directory; `lancedb/` is used when
LanceDB is the configured vector backend.

## Running A Backup

Local prod and staging deploys install a daily maintenance launchd job from
`deployment/launchd/com.brain.maintenance.plist.template`. The rendered
production label is `com.brain.prod.maintenance`; staging renders as
`com.brain.staging.maintenance`. The job starts at 03:00 and runs
`scripts/nightly_maintenance.py` against the environment's shared `brain.env`.
That script runs `scripts/brain_agent_memory.py` first, then runs
`scripts/backup_stores.py` only if the agent-memory/Cognee improvement step
exits successfully. A failed cognify run therefore skips backup instead of
creating a snapshot from a partially refreshed projection.

Use the configured environment:

```bash
ENV_FILE=/Volumes/xpg_usb4/prod/brain/shared/secrets/brain.env make backup
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

If `--skip-google-drive` is used while Google Drive backup is enabled, the
manifest records that replication as skipped instead of verified.

## Manifest Contract

Every backup writes `manifest.json` with this shape:

```json
{
  "timestamp": "20260510_120000",
  "backup_dir": "/Volumes/xpg_usb4/prod/brain/shared/backups/20260510_120000",
  "data_root": "/Volumes/xpg_usb4/prod/brain/shared/data",
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

`google_drive` is populated after the local manifest is written when Drive
replication runs. `blockers` means the run finished but missed something
operationally important. Production verification treats blockers as failures.

## SQLite Backups

The backup script searches the shared data root for SQLite databases:

```text
*.sqlite
*.sqlite3
*.db
system/databases/*
```

Each SQLite file is copied using SQLite's online backup API, not a raw file
copy. The backup is then checked with:

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

`DATA_ROOT_DIRECTORY` is archived as:

```text
raw_data/<data-root-name>.tar.gz
```

This preserves source data and runtime files that are not captured by the
SQLite- or vector-store-specific paths.

If `DATA_ROOT_DIRECTORY` is missing, the manifest receives a blocker.

## Vector Store Backups

The script backs up exactly one vector-store family based on `VECTOR_DB_PROVIDER`.

### pgvector Backup

When `VECTOR_DB_PROVIDER=pgvector`, the backup script creates a Postgres dump
of the configured vector database. The dump is written to:

```text
pgvector/<db-name>.sql
```

The dump is produced with `docker exec brain-prod-postgres pg_dump` when Docker
is available. The manifest entry records the dump method, database name, return
code, captured stderr, and whether the dump was verified as non-empty.

If Docker is not available, the manifest receives a blocker and the pgvector
backup does not complete.

### LanceDB Archive

When the vector backend is LanceDB, the script archives:

- The configured `VECTOR_DB_URL`.
- Any path under the shared data root whose name contains `lancedb`.

Each candidate is stored as:

```text
lancedb/<source-name>.tar.gz
```

If no LanceDB path is found, the manifest receives a blocker because production
verification expects a vector-store artifact when LanceDB is the configured
backend.

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

The archive mode is set to `0600`.

If no secret files are found, the manifest receives a blocker. The deployed auth
registry file (`BRAIN_AUTH_USERS_FILE`) is rendered by production deploys; do not
assume it is captured by this backup unless you have added it to the backup
inputs.

Production secret rendering and conflict rules are documented in
[Production Secrets](production-secrets.md).

## Neo4j Backup

The script first attempts a read-only graph count with `cypher-shell` and writes
`neo4j-counts.json` when available. A successful count check is recorded as a
verified Neo4j manifest entry.

If `BRAIN_NEO4J_DUMP_ENABLED=false`:

- Empty graph: no dump is required.
- Non-empty graph: the manifest receives a blocker, and the script may create a
  raw live archive as a fallback.

Raw live Neo4j archives are not considered consistent backups.

For a consistent Neo4j dump:

```env
BRAIN_NEO4J_DUMP_ENABLED=true
```

When Docker is available, the script runs `neo4j-admin database dump` inside the
configured Neo4j Docker container and copies the dump into:

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

With this enabled, the script stops the configured Neo4j service, runs the dump,
restarts Neo4j, and waits for readiness.

## Google Drive Replication

When `BRAIN_GOOGLE_DRIVE_BACKUP_ENABLED=true`, the backup is replicated after the
local manifest is written.

Preferred local-mounted Drive path:

```env
BRAIN_GOOGLE_DRIVE_LOCAL_PATH=/path/to/local/Google Drive
BRAIN_GOOGLE_DRIVE_FOLDER=backup/brain
```

The script copies the complete run directory to:

```text
$BRAIN_GOOGLE_DRIVE_LOCAL_PATH/$BRAIN_GOOGLE_DRIVE_FOLDER/YYYYMMDD_HHMMSS/
```

If no local path is configured, the script uses `rclone`:

```text
$BRAIN_GOOGLE_DRIVE_REMOTE:$BRAIN_GOOGLE_DRIVE_FOLDER/YYYYMMDD_HHMMSS/
```

Replication is considered verified only when the copied/uploaded directory
contains `manifest.json`. The manifest records either:

```json
{"method": "local_path", "path": "...", "verified": true}
```

or:

```json
{"method": "rclone", "remote": "...", "verified": true}
```

If `--skip-google-drive` is used, the manifest records the Drive step as
skipped when Google Drive backup is enabled.

Production verification requires Google Drive verification when
`BRAIN_GOOGLE_DRIVE_BACKUP_ENABLED=true`.

## Production Verification

`scripts/verify_mcp_production.py` checks the latest manifest under
`BRAIN_BACKUP_DIR` unless `--skip-backups` is passed.

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
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.brain.mcp.plist
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.brain.slack-agent.plist
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.brain.ui.plist
```

Restore secrets:

```bash
mkdir -p /Volumes/xpg_usb4/prod/brain/shared/secrets
tar -xzf BACKUP_DIR/secrets/secrets.tar.gz -C /Volumes/xpg_usb4/prod/brain/shared/secrets
chmod 600 /Volumes/xpg_usb4/prod/brain/shared/secrets/*
```

Restore SQLite databases by copying the selected files from `sqlite/` back to
their manifest `source` paths.

Restore raw data from the matching archive in `raw_data/`.

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

- Run a backup before any destructive migration, production deploy, or manual
  data repair.
- Treat `manifest.json` as the source of truth for what was captured.
- Do not rely on raw live Neo4j archives for restore.
- Keep `ENV_FILE`, `BRAIN_AUTH_PASSWORD_FILE`, and `BRAIN_AUTH_STATE_PATH` in
  the secrets archive.
- Keep at least one verified off-device copy when Google Drive backup is
  enabled.
- Resolve manifest blockers before considering a backup usable.

<!-- brain-doc-source-hash: fac95be470505dd5db82db9b184e3b8de7ff76d9dd96565be8148e0618690314 -->
