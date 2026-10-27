# M1 — Secret-safe vault

| | |
|---|---|
| **Releases** | 2.2.0 – 2.2.7 |
| **Status** | Shipped |
| **Depends on** | M0 |
| **Unlocks** | M2, M3 |
| **Theme** | Stop treating plaintext secrets as immutable text; add the built-in authenticator |

---

## 1. Goal

Make the app's own handling of secrets defensible before adding hardware key custody:

- A decrypted password or PIN lives in a wipeable byte buffer, not an immutable text value.
- Copied secrets do not stay on the clipboard indefinitely.
- Authenticator seeds get the same protection as passwords and can be linked to an account entry.
- The product gets a name that is safe to ship.

M1 does not change where the vault key lives; that is M2.

---

## 2. Problem

M0 held decrypted passwords in immutable text values. Immutable text cannot be zeroed, so a password could survive in memory until garbage collection — and in a crash dump after that. Three concrete gaps:

1. Secret input flowed through ordinary text-editing widgets.
2. Copied secrets stayed on the clipboard indefinitely.
3. The vault had passwords but no verification-code support, so users kept a second authenticator app.

---

## 3. Design

### 3.1 Built-in authenticator

**Record model** (product level):

An authenticator record holds a unique identifier, a label and issuer for display, the secret as
ciphertext under the same protection as a password, the algorithm, digit count, and period so
imported codes keep matching their source, an optional reference to a linked account entry, and a
last-updated time.

- New secrets default to the standard one-time-code parameters.
- Imported accounts keep their own algorithm, digit count, and period so generated codes match the
  app they came from.
- Authenticator records live in their own store; an account entry keeps only a non-secret reference.
- The link is bidirectional: linking, unlinking, renaming, and moving keep both sides consistent. Stale references are cleared on load.

**Import surface:**

- Generate a new secret, paste an existing secret, or paste a standard provisioning URI.
- Scan a pairing QR on mobile; camera or image pick on desktop.
- Bulk import from a well-known authenticator's export format, with a review list before anything is committed.
- Duplicate suppression by secret or issuer + label.
- Counter-based accounts from an export are skipped with a notice; a half-parsed secret is never stored.

**Navigation:**

The authenticator is its own destination on desktop. On mobile it is reached from the Securities
and generator pages rather than taking a bottom-bar slot of its own.

**Integration:**

- An account entry can attach, create, or unlink an authenticator record.
- A linked entry can copy the current code without opening the authenticator screen.
- Quick search offers a second copy action only when an entry is linked.
- All copies go through the clipboard service.

### 3.2 Byte-only secret handling

- A decrypted secret is held in a wipeable byte buffer and zeroed when it is no longer displayed.
- Each buffer has exactly one owner. Helpers borrow; only the owner clears.
- No decrypted secret is converted to an immutable string type at any point in the vault flow.
- Logging records lifecycle and errors only, never contents.

**PIN entry:**

- PIN entry uses a dedicated digit pad rather than a general text field, so the digits are never
  held in an ordinary text value while the user types.
- Digits are held in a wipeable buffer for the life of the entry.
- PIN verification works on bytes directly rather than on a text value.

**Free-form password entry:**

- A dedicated secure password field does not hand the value to an ordinary text field while the user is editing.
- Obscure / reveal toggle, paste support, and optional clipboard clear after paste.
- On save the buffer goes straight into the encryption path and is cleared immediately after. No text round-trip.
- Cloud sign-in screens may still use ordinary text input; they are outside the vault.

**Rejected:** off-heap or locked-memory isolation for secret input. The available option covered only mobile, while the product is desktop-heavy. Accepted residual risk: the buffer is wipeable but not off-heap.

### 3.3 Clipboard hygiene

- One clipboard service is the only copy path for secrets.
- Optional setting: overwrite the clipboard with random text, then clear it after a short delay.
- Platform clipboard history is purged where the OS allows it.
- The same service serves accounts, quick search, and authenticator codes.

### 3.4 Screen and diagnostic hardening

- Screenshots and screen recording are blocked where the OS allows it, including the recent-app
  preview on mobile.
- Release builds resist runtime inspection where the OS permits.
- Crash reporting is optional and excludes vault contents, passwords, clipboard, and PINs.
- No secret is written to a log, a crash report, or a diagnostic file.

### 3.5 Release-quality work

- Auto-start at OS login.
- An in-app support channel.
- **2.2.6 — product rename.** The user-facing name changed. Package identity was preserved so
  updates keep vault data and purchases.

---

## 4. Decisions and rejected alternatives

| Decision | Why |
|----------|-----|
| Separate authenticator records, not fields on an account entry | A secret can exist without an entry; an entry needs only a non-secret reference |
| Imported parameters honoured per record | Otherwise imported codes silently differ from the source app |
| No new mobile bottom tab | The bar is already full; links from Securities and the generator are enough |
| Byte-only secrets, not off-heap isolation | Off-heap support did not cover desktop; residual risk documented |
| Import-only authenticator migration | Exporting back to other apps was out of scope |
| Overwrite then clear the clipboard | A plain clear can leave the value retrievable by clipboard managers |
| Rename without changing package identity | Preserve in-place updates, purchases, and vault continuity |

---

## 5. Components

| Responsibility | Role |
|---------------|------|
| Authenticator records | Record model, link maintenance, merge, re-encryption on import |
| Code generation and parsing | Standard one-time-code algorithms and provisioning URIs |
| QR capture | Camera on mobile, camera or image pick on desktop |
| Authenticator UI | List, detail, editor, import review |
| Secure buffers | Wipeable byte and digit buffers, one owner each |
| Protected input | PIN pad and secure password field |
| Lock service | PIN verification on bytes |
| Clipboard service | The only secret copy path, with auto-clear |
| Navigation | Destinations and indices |

---

## 6. Security properties

- [x] A user can generate a secret, paste a secret or provisioning URI, scan a QR, and bulk-import from a well-known authenticator.
- [x] Imported accounts produce the same codes as their source app for non-default algorithm, digit count, and period.
- [x] A bulk import shows a review list; duplicates and counter-based accounts are skipped with a notice, and a half-parsed secret is never stored.
- [x] Authenticator secrets are ciphertext at rest; a generated code exists only in memory or on the clipboard.
- [x] Desktop reaches the authenticator from the sidebar; mobile reaches it from Securities or the generator.
- [x] An account entry can link and unlink an authenticator record, and a linked entry exposes the current code.
- [x] Import, merge, and transfer preserve authenticator secrets and re-encrypt them under the destination key.
- [x] A decrypted secret is never held as an immutable string within the vault flow.
- [x] Clipboard auto-clear can be enabled, and platform clipboard history is purged where the OS allows.
- [x] The renamed build updates in place and keeps existing vault data.

---

## 7. Risks and residual gaps

| Risk | Status |
|------|--------|
| An input-method value exists briefly as text while the field is focused | Accepted; outside the app's control |
| Paste or password generation creates brief text copies | Accepted and documented |
| OS keyboard, accessibility, and clipboard managers are outside the app | Accepted |
| Secure buffers are wipeable but not off-heap | Accepted |
| Authenticator records still lived in a single stored document | Closed by M3 |
| The vault key was still readable by a same-user process | Closed by M2 |

---

## 8. Provenance

Derived from the shipped behaviour of the 2.2.0–2.2.7 releases and the public release history, including the security work on secret input and clipboard handling. Implementation identifiers are withheld under the disclosure model in the [index](../README.md).
