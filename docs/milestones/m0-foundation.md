# M0 — Foundation and product shell

| | |
|---|---|
| **Releases** | 2.0 – 2.1 |
| **Status** | Shipped |
| **Depends on** | — |
| **Unlocks** | M1, M2, M3 |
| **Theme** | A local-first, cross-platform password manager with a one-time store unlock |

---

## 1. Goal

Ship a usable password manager on Windows, macOS, Linux, iOS, Android, and web where the vault is local, secrets are encrypted at rest, and the paid unlock is a one-time store purchase rather than a subscription or an account.

M0 is the baseline that later security milestones harden. Several of its shortcuts are the reason M1–M4 exist.

---

## 2. Problem

The product needed a working shell before it could justify a security architecture:

- Six platforms with different window, tray, packaging, and store rules.
- A vault usable without an account, with optional social sign-in.
- A paid unlock that works offline and survives reinstall without a licence server.
- A data model simple enough to ship: categories of login entries.

---

## 3. Design

### 3.1 Application shell

- One Flutter codebase with a shared navigation shell.
- Desktop closes to the system tray instead of quitting, with a tray menu (show, quick search, launch at startup, quit) and a global quick-search hotkey that opens a compact search window.
- Optional launch at OS login.
- Mobile uses bottom navigation; desktop uses a sidebar with the same destinations.
- Localized UI; the product ships 13 languages.

### 3.2 Vault data model

A map of category name to an ordered list of entries, persisted as a single document.

An entry holds a title, its password, an optional note, and a last-updated time. Only the password
is ciphertext; the title and the note are stored as confidential metadata. A title is unique
inside its category, and its length is bounded.

- Category order is the map key order; entries are newest-first by updated time.
- First install seeds two sample categories.

### 3.3 Cryptography and key storage

- A 32-byte vault key is generated on first use.
- Each password is authenticated encryption with a random nonce.
- The vault key was protected by platform secure storage; hardware wrapping and per-use presence
  arrive in M2.

### 3.4 Feature set

| Area | Behaviour |
|------|-----------|
| Vault | Categories, add / edit / delete, move between categories, unique titles |
| Generator | Adjustable length and character sets, strength indicator, copy |
| Security | Score plus weak / reused / old password list, drill into the entry |
| Search | Multi-term matching with quoted phrases |
| Backup | JSON export and merge by updated time |
| Lock | PIN lock screen, optional biometrics, auto-lock, manual lock |
| Accounts | Email, Google, Apple, guest mode |
| Settings | Language, theme, clipboard behaviour, data management |
| Profile | Account and usage information |

### 3.5 Paid unlock

- One-time non-consumable purchase through the platform stores.
- Restore is supported, including offline use of an already-verified entitlement.

### 3.6 Packaging

- Desktop and mobile builds are produced from one shared pipeline.
- Each platform is distributed through its native store and, where applicable, a vendor download.
- Store metadata and policy pages are prepared per platform.

---

## 4. Decisions that survived M0

1. **Local-only vault.** No server stores the vault or the key.
2. **Category → entry model.** Still the account store in M5; other record types get their own stores.
3. **Per-secret authenticated encryption.** Still the primitive in every later milestone.
4. **One-time store unlock.** Unchanged; only the entitlement state machine was hardened.
5. **Account-free use.** Guest mode remains a first-class path.
6. **Unique title per category.** Still enforced by the encrypted database in M3.
7. **13 languages.** Every later feature adds strings to all of them.

---

## 5. Limitations that forced later milestones

| Limitation | Closed by |
|------------|-----------|
| The vault key was protected by OS secure storage alone | M2 — hardware / OS wrap with a user gesture |
| Decrypted passwords lived in immutable text values that cannot be wiped | M1 — wipeable buffers and protected input |
| Clipboard kept copied secrets indefinitely | M1 — auto-clear |
| The whole vault was one rewritten document | M3 — encrypted relational store |
| Backup did not meet the confidentiality bar for a file that leaves the device | M4 — sealed container |
| Transfer did not meet the zero-trust bar for an untrusted network | M4 — authenticated post-quantum session |
| No authenticator, wallet, or passkey support | M1, M5 / M6, M7 |

Every later milestone removes a concrete M0 weakness rather than adding a feature for its own sake.

---

## 6. Components

| Responsibility | Role |
|---------------|------|
| App shell | Navigation, locale, startup tasks, desktop integration |
| Vault UI | Category list, entry editor, entry rows, search |
| Cryptographic service | Vault key access and per-secret encryption |
| Lock service | PIN verification and lock state |
| Security scoring | Reads the account store only |
| Purchase services | Platform in-app purchase and entitlement state |
| Localization | Shared string catalogues for every supported language |

---

## 7. Security properties

- [x] A user can create categories and entries, edit them, and move them between categories.
- [x] Passwords are ciphertext at rest and decrypt only on reveal.
- [x] The app locks on demand and after the configured inactivity period.
- [x] The vault behaves identically on all six target platforms with the same data model.
- [x] A store purchase unlocks the paid surfaces and can be restored.
- [x] No account is required for guest use.
- [x] All user-visible strings exist in the supported languages.

M0 properties are historical: they describe what shipped, not a new test plan.

---

## 8. Risks carried into M1

- The vault key is only as safe as the secure-storage file (M2 closes this).
- Secret handling relies on immutable text (M1 closes this).
- Whole-document rewrites risk partial writes and data loss (M3 closes this).
- The backup path is a confidentiality gap (M4 closes this).
- Entitlement is verified with the platform store. Accepted: there is no server, so there is no
  server-side licence enforcement; the product sells convenience rather than a subscription.

---

## 9. Provenance

Derived from the shipped behaviour of the 2.0–2.1 releases and the public release history. Implementation identifiers are withheld under the disclosure model in the [index](../README.md).
