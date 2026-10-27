# M6 — Wallet: cryptocurrency

| | |
|---|---|
| **Release** | 2.5.0 |
| **Status** | Planned — record shape fixed in the 2.4.0 design so it is not reopened |
| **Depends on** | M5 (Wallet page, per-record store pattern) |
| **Unlocks** | — |
| **Theme** | Store crypto backups without becoming a crypto wallet |

---

## 1. Goal

Let a user keep the recovery material for a crypto wallet in the same local vault, as a record type of its own:

- Network-aware records (Bitcoin, Ethereum, BNB chain, Tron, Solana, XRP, Litecoin, Dogecoin, other).
- Public fields (email, address, memo, derivation path) readable without a reveal step.
- Secret fields (recovery words, extra passphrase, private key, extended public key) encrypted with the vault key.
- No chain interaction: no balance, send, receive, network calls, key generation, or address derivation.

The purpose is safe storage and readable recovery, not replacing a wallet app.

---

## 2. Problem

Crypto recovery material fits neither an account nor a bank card:

- A recovery phrase or private key is not a password, and the record has no username or URL.
- Wallets span several networks with different backup shapes.
- Public information must be readable, while recovery material must never be shown by default.
- Putting these fields on the account store would make every account path network-aware and risk exposing a seed phrase through account search or backup.

M5 rejected a shared wallet list with a type field for the same reason cards were rejected: two schemas in one list fail together and force each release to tolerate rows it cannot edit.

---

## 3. Design

### 3.1 Record type

| Item | Value |
|------|-------|
| Storage | Its own flat record list, the same style as authenticator items and cards |
| Backup key | Its own optional list in the backup payload |
| Merge | Re-encrypt by identifier, after cards |
| Compatibility | A 2.4.0 build ignores the crypto list; a 2.5.0 build merges it; an empty list is omitted |

### 3.2 Fields

A crypto record holds its own identifier, the network, an optional asset name, a display label, an
optional email, the public address, an optional memo or destination tag, an optional derivation
path, and a last-updated time — plus up to four secret fields.

The **recovery words, extra passphrase, private key, and extended public key are ciphertext**. Every
other field is confidential metadata. At least one of recovery words, private key, or extended
public key is required.

Email, address, memo, and derivation path are shown without a reveal step. Recovery words, extra
passphrase, private key, and extended public key are masked until revealed.

### 3.3 Networks

| Network | Typical backup material |
|---------|-------------------------|
| Bitcoin | address, word list, optional passphrase, private key, extended public key, derivation path |
| Ethereum | address, word list, optional passphrase, private key or keystore export; optional asset name |
| BNB chain | address, word list, private key, optional memo; optional asset name |
| Tron | address, word list or private key; optional asset name |
| Solana | base58 address, word list or private key |
| XRP | address plus destination tag |
| Litecoin | Bitcoin-shaped backup |
| Dogecoin | address, word list or private key |
| Other | user-supplied name, with the fields the user provides |

Common fields for every network: network, label, email, address, recovery words, private key.

If a restored record has a field the editor normally hides, show the field anyway so the value is not trapped.

Address shape is a **non-blocking warning**; saving is never refused. Each supported network has a light shape hint (prefix or length family), and "other" has no check.

The BNB entry means a BNB chain wallet, not an exchange login, API key, or API secret. Exchange credentials stay accounts.

### 3.4 Encryption

- Reuse the vault key and the same authenticated-encryption service as passwords, authenticator secrets, and cards, for the four secret fields.
- Decrypt only to reveal, edit, copy, or re-encrypt on restore.
- Clear decrypted bytes after use.
- Never log recovery words, the extra passphrase, a private key, or an extended public key.
- On restore, re-encrypt each present secret with the local key. One failed secret fails that list; never write a partial crypto list.
- On load, do not replace a failed secret with an empty value; show it as unreadable.
- Empty optional secrets are omitted, not stored as empty ciphertext.

### 3.5 Wallet UI

The Wallet page gains a **Bank cards | Crypto** control. Switching does not change the other store.

- Adding a crypto record starts with a network picker; the editor then shows the fields for that network.
- List row: network name, label, email, truncated address, and memo when set.
- Search filters network, asset name, label, email, address, and memo only; it does not decrypt a secret.
- Copy address and memo from the row; copy the secret fields only from the revealed editor, through the clipboard service.
- Suggested label when empty: network name plus truncated address.
- Deleting a crypto record removes it only; it does not touch cards, accounts, or authenticator records.

### 3.6 Merge behaviour

- Same identifier: the newer updated time wins.
- Unknown identifier: append.
- Never match by label or address.
- Preserve unknown fields on a record so a newer field is not stripped by an older save.
- Restore order: accounts, authenticator items, cards, crypto records.

---

## 4. Decisions and rejected alternatives

| Decision | Why |
|----------|-----|
| Separate crypto store | One schema, one failure domain, independent merge and backup key |
| Separate from the card store | Different sensitivity and different edit flow |
| Network is a stored value, not a free-text label | Bitcoin, Ethereum, and BNB must be real types the UI renders correctly |
| Public fields plaintext, secrets encrypted | Address and memo need to be readable; recovery material must not be |
| Storage only | Chain features would add network calls, address derivation, and a much larger attack surface |
| Derivation path and extended public key stored as text | The user pastes a backup; the app does not compute or validate a wallet |
| Address mismatch is a warning | A valid but unusual address must not be blocked |

Rejected: account kinds, a shared wallet list, seed generation, balance display, send and receive, payment QR codes, name-service lookups, network RPC, wordlist validation, and computing an address from stored material.

---

## 5. Components

| Responsibility | Role |
|---------------|------|
| Crypto records | Fields, network metadata, validation warnings |
| Crypto store | Load, save, export, re-encryption on restore, merge by identifier |
| Backup integration | Optional crypto list after cards |
| Wallet UI | Bank cards / Crypto switch, network picker, editor, reveal and copy |
| Localization | Network names and field labels in every supported language |

---

## 6. Security properties

- [ ] Crypto records live in their own record set, not in the card list or the account store.
- [ ] Bitcoin, Ethereum, and BNB records each save with the network set and display that network.
- [ ] Recovery words, extra passphrase, private key, and extended public key are ciphertext at rest.
- [ ] Email, address, memo, and derivation path are shown as plaintext.
- [ ] At least one of recovery words, private key, or extended public key is required.
- [ ] The app does not generate keys, derive addresses, or show a balance.
- [ ] Backup and transfer carry the crypto list and re-encrypt those secrets.
- [ ] A build that predates Wallet ignores the crypto list without corrupting its own records.
- [ ] Deleting a crypto record does not touch cards, accounts, or authenticator records.
- [ ] Search never decrypts a secret field.

---

## 7. Risks and open items

| Risk | Mitigation |
|------|------------|
| A recovery phrase or private key is the highest-value secret in the app | Encrypt at rest, mask by default, reveal on demand, never log, wipe buffers |
| Restored secrets may be ciphertext under another device key | Re-encrypt on restore; fail the whole list rather than write a partial one |
| Users may expect wallet functionality | UI copy states storage only; no balance, send, or receive controls |
| A derivation path may be mistaken for a validated path | Label it as user-supplied text; never derive an address |
| No stable account identifier yet | Crypto records use their own identifier and do not depend on account identity |

---

## 8. Provenance

Summarizes the 2.5.0 scope as planned. Storage keys and source locations are withheld under the disclosure model in the [index](../README.md).
