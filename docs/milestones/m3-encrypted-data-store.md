# M3 — Encrypted data store

| | |
|---|---|
| **Release** | 2.2.8 |
| **Status** | Shipped |
| **Depends on** | M0, M1 |
| **Unlocks** | M4 (transactional merge target), M5 / M6 (per-record stores) |
| **Theme** | Replace a whole-document vault with an encrypted relational store and a verified migration |

---

## 1. Goal

Move the vault from two encrypted documents to one encrypted store with per-record writes and a verified one-time migration. After migration the store is the only source of truth and the old documents are removed.

The secret format does not change: passwords and authenticator secrets remain authenticated ciphertext under the vault key. Only the container changes.

---

## 2. Problem

Accounts and authenticator items were each held as a single stored document.

| Problem | Consequence |
|---------|-------------|
| Every save rewrote the whole vault | Any partial write risked the entire vault |
| No transactions | A failed edit could leave entries and links inconsistent |
| Two independent documents | Account, entry, and authenticator links could diverge |
| No per-record query | Load and search materialized everything |
| No constraints | Duplicate titles and orphan links were enforced only in application code |

The store also needs its own key, derived for this purpose alone, so the database key is not the vault key.

---

## 3. Design

### 3.1 Database and keys

- A single encrypted database file per device.
- A build that cannot confirm the encryption layer is active refuses to open the store rather than
  writing an unencrypted vault.
- The database key is **not** the vault key. It is derived from the vault key for this purpose alone, so one derived key does not expose the other.
- The derivation happens inside the platform key layer wherever a security chip is available, so the vault key does not enter the application runtime for this purpose. On Linux and web it happens in process.

### 3.2 Data model

One record set per record type, plus schema-version metadata that also records whether the
migration has completed.

Key properties:

- Categories, entries, and authenticator items are stored as separate records rather than one document, so a write touches only what changed.
- A category has a stable identifier, so reordering or renaming the tree does not re-point the entries under it.
- Entry titles are unique within a category, enforced by the store rather than by application code.
- An authenticator record refers to at most one entry, so renaming a category or moving an entry needs no follow-up write.
- Deleting an entry detaches its authenticator record instead of deleting it.
- Referential integrity is enforced by the store: no orphaned records and no duplicate titles from any code path.

Column definitions, index definitions, and identifier encoding are withheld under the disclosure model.

### 3.3 Access layer

- All reads and writes go through one access layer; no screen or import path touches the storage engine directly.
- The layer exposes category, entry, and authenticator operations and keeps the record invariants above.
- After migration there is no read or write fallback to the pre-2.2.8 format.

### 3.4 Migration

The migration from the pre-2.2.8 format is a **verified, reversible, one-time** operation. It runs when the store is opened and follows three rules:

1. **Import in one transaction.** A partial import is impossible.
2. **Verify before trusting.** The imported content is read back and compared against the source. Only a full match counts as success.
3. **Retain the source until success.** If verification fails, the import is discarded and the previous format is kept as the source of truth, so the next open retries instead of losing data.

The previous format is deleted only after a successful verification. A migration that cannot complete leaves the app on the old format and reports the condition rather than degrading silently.

The verification steps, identifiers, and ordering guarantees are implementation detail and are withheld.

### 3.5 Failure and reset

- If the store or its key cannot be opened, the lock screen explains why and offers an explicit, confirmed reset instead of leaving the app unusable.
- The reset is user-initiated. There is no silent wipe, and it never runs automatically.
- A corrupt store never causes the app to create a replacement key over existing data.

---

## 4. Decisions and rejected alternatives

| Decision | Why |
|----------|-----|
| Normalized records, not one stored document | Per-record writes, store-enforced constraints, transactional link updates |
| Stable category identifiers | Renames and reordering do not re-point entries |
| Title uniqueness enforced by the store | The product rule becomes impossible to violate from any code path |
| One-to-one authenticator link | Renames and moves need no follow-up write |
| Per-purpose key derivation | The database key is not the vault key |
| Derivation inside the key layer where a chip exists | Keeps the vault key out of the application runtime |
| Verified import, then purge | The old format stays authoritative until the new store is proven correct |
| Explicit reset dialog | A corrupt store must not brick the app silently |

Rejected: keeping the old documents as a read fallback after migration (two sources of truth), and migrating legacy inline authenticator fields (the separate store already owns them).

---

## 5. Components

| Responsibility | Role |
|---------------|------|
| Store service | Open, key handling, schema versioning, migration state, reset signalling |
| Key derivation | Purpose-specific derivation from the vault key |
| Access layer | Category, entry, and authenticator operations with record invariants |
| Reset dialog | Explains an unopenable vault and confirms a reset |
| Account UI | Reads and writes through the access layer |

---

## 6. Security properties

- [x] A first launch on the pre-2.2.8 format carries every category, entry, and authenticator record into the encrypted store.
- [x] The content of the new store matches the source in record count, titles, ciphertext, links, and order.
- [x] The previous format is removed only after a successful verification.
- [x] A failed verification leaves the previous format authoritative, and no data is lost.
- [x] A record store that is not encrypted cannot be opened; the app never writes an unencrypted vault.
- [x] The database key differs from the vault key.
- [x] Duplicate titles inside a category are rejected regardless of which code path attempts them.
- [x] Renaming or moving does not break an authenticator link.
- [x] An unreadable store produces an explanation and an explicit reset, never a silent wipe.

---

## 7. Risks and open items

| Risk | Mitigation |
|------|------------|
| A migration bug loses vault data | One transaction, full verification, rollback, source retained on any failure |
| Duplicate titles in the old format inside one category | Newest wins; the collision is surfaced rather than silently resolved |
| The encryption layer is missing or replaced in a build | The store refuses to open rather than writing plaintext |
| A database key change would orphan the vault | The key derives from the vault key, so it changes only when the vault key changes |
| Linux and web derive the database key in process | Accepted; same output, vault key briefly in memory |
| Future schema evolution | Versioned store; upgrades must be additive and transactional |

---

## 8. Provenance

Derived from the shipped behaviour of the 2.2.8 release and the public release history. Schema definitions, storage keys, and migration code are withheld under the disclosure model in the [index](../README.md).
