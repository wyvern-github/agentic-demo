---
name: sqlite-management
description: "Use when designing SQLite storage, schema migrations, queries, backups, or database tests for a Python office application, utility, or mini game."
---

# SQLite and Database Management

1. Use the standard library `sqlite3` for modest local relational data unless the project already uses a suitable library. Skip a database for an app that does not need persistence, and prefer settings storage for a few UI preferences.
2. Store the database in an application-specific writable data directory. Keep query and transaction code out of widgets. Own and close each connection explicitly; the connection context manager commits or rolls back transactions but does not close it. Keep connections thread-confined and open them in the worker that uses them.
3. Enable `PRAGMA foreign_keys = ON` on each connection, before any transaction. Model identity, required values, uniqueness, valid ranges, and relationships with constraints. Keep timestamps unambiguous. Choose indexes for real lookup/sort patterns and use `EXPLAIN QUERY PLAN` for suspected bottlenecks.
4. Bind data values as SQL parameters. For identifiers that cannot be bound, map known UI choices to fixed SQL fragments. Keep related writes atomic, keep write transactions short, and roll back on failure. Choose transaction behavior explicitly for the supported Python version; don't assume all `sqlite3` autocommit defaults are alike. Handle busy and integrity errors without misleading the user about whether a save succeeded.
5. Use ordered, versioned migrations, for example with `PRAGMA user_version`. Test initialization and upgrade from the previous schema. Update the version only after successful migration work in the same transaction, and avoid APIs that implicitly commit a transaction you intend to control. Refuse to open an unsupported newer schema for writing. Back up before risky upgrades and document a tested recovery path.
6. Decide journal mode deliberately. Consider WAL for measured local reader/writer contention, not as a substitute for short transactions, and do not assume it works on network shares. Use SQLite's backup API for live backups, not a raw copy of the active database file. Test restoring a backup; avoid copying real user data into fixtures or logs.
7. Test real SQLite behavior with isolated databases under pytest `tmp_path` for reopening, migrations, constraints, and rollback. Use in-memory tests only where all operations share the intended connection. Verify failed writes leave the previous state intact.
