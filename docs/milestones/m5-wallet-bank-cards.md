# M5 — Wallet: bank cards

| | |
|---|---|
| **Release** | 2.4.0 |
| **Status** | Planned — design complete, implementation not started |
| **Depends on** | M3 (per-record storage), M4 (backup key pattern) |
| **Unlocks** | M6 (crypto records on the same page) |
| **Theme** | Split the vault by record type instead of adding "kinds" to accounts |

---

## 1. Goal

Give bank cards their own section, record type, store, and backup key, while keeping the account store account-only. Replace the separate password-generator and security destinations with one **Securities** page.

A card is not an account. It has a number, holder, expiry, security code, and PIN; putting those on an account row makes account load, search, security scoring, and merge treat non-passwords as passwords.

---

## 2. Problem

The vault is one category map of login entries. Adding cards would force a "kind" field and card columns onto every account entry. Three approaches were considered:

| Approach | Verdict |
|----------|---------|
| **A — kinds inside the account store** | Reject. Account load, search, security score, profile count, and merge all become kind-aware; card numbers sit beside passwords |
| **B — one shared wallet list with a type field** | Reject. Two schemas share a list; a bad card decrypt and a bad crypto decrypt fail as one import; each release must tolerate rows it cannot edit |
| **C — one store per record type** | Choose. Accounts, authenticator items, cards, and crypto records each keep one schema and one backup key |

C follows the pattern the authenticator store already established, so it is the lowest-risk extension.

---

## 3. Design

### 3.1 Navigation and information architecture

Destinations in order:

1. **Account** — the current vault page, accounts only. Label changes from Vault to Account. Categories, inline edit, authenticator link, and search behave as today.
2. **Wallet** — new page. 2.4.0 shows bank cards.
3. **Securities** — password generator and account security health on one page. Generator and Security are removed as destinations.
4. **Authenticator** — desktop keeps the sidebar item; mobile opens it from Securities.
5. **Transfer**, **Settings** — unchanged.
6. **Profile** — account and usage information.

Mobile bottom navigation: Account, Wallet, Securities, Transfer, Settings.

- The authenticator stays its own store and is not merged into Securities.

### 3.2 Account store unchanged

The account store remains a category map of login entries: a title, the password as ciphertext, an
optional description, a last-updated time, and an optional authenticator reference.

No kind field. No card number, security code, PIN, private key, or recovery words on an account. Payment-service logins stay accounts.

Security health and the profile password count keep reading the account store only. A card must not change the score or the password total.

A stable account identifier remains out of scope for this release.

### 3.3 Bank card records

Cards live in their own flat list — no categories.

A card record holds its own identifier, a display label, an optional holder name, the brand, the
card number, the last four digits for display, an optional expiry, an optional security code, an
optional card PIN, optional notes, and a last-updated time.

The **card number, security code, and card PIN are ciphertext**. The identifier, label, holder
name, brand, last four digits, expiry, notes, and timestamps are confidential metadata. The stored
last-four value is derived on save and never contains the whole number.

Validation:

- Card number: digits only, length-bounded. A checksum failure is a warning, not a block.
- Security code and card PIN, when present: short digit strings, bounded in length.
- The stored last-four value is recomputed whenever the number is saved or re-encrypted. A restored value that disagrees with the decrypted number is not trusted.

The list row shows label, brand, masked number, and expiry. The full number, security code, and PIN stay masked until revealed. Copy goes through the clipboard service: number as the primary action, security code only when it exists.

No authenticator link on a card. No card scanning, issuer lookup, or network tokenisation. Suggested label when empty: brand plus last four.

### 3.4 Encryption

Reuse the vault key and the same authenticated-encryption service as passwords and authenticator secrets:

- Card: number, security code, PIN.
- Account: password only, unchanged.

Rules:

- The vault key stays in the hardware or OS key layer.
- Decrypt only to reveal, edit, copy, or re-encrypt on restore.
- Clear decrypted bytes after use.
- Never log a card number, security code, or PIN.
- On restore, decrypt each present secret with the container key and re-encrypt it with the local key. One failed secret fails that list; never write a partial card list.
- On load, do not replace a failed secret with an empty value; leave it and show it as unreadable.
- Empty optional secrets are omitted, not stored as empty ciphertext.

### 3.5 Backup and transfer

- The backup payload keeps the account document and the authenticator list, and may add a card list.
- An empty card list is omitted.
- Restore order: accounts, then authenticator items, then cards.
- Merge matches on identifier only: the same identifier keeps the newer updated time; an unknown identifier is appended; cards are never matched by label; unknown fields on a card are preserved.
- An older build that imports a newer file merges accounts and authenticator items and ignores the card list. Cards sync only between builds that know them, so users are advised to upgrade every paired device before relying on Wallet items.
- An unknown record list is never absorbed into the account data.

### 3.6 Wallet page

Follow the authenticator page, not the inline account row:

- Header title Wallet.
- Add opens a blank card editor.
- List, detail, and editor for one record.
- Search filters label, holder name, brand, last four, and expiry; it does **not** decrypt the number.
- Delete removes the card only; it does not touch accounts or authenticator records.

### 3.7 Securities page

One destination, two blocks on one scroll (or two segments if a phone is too short):

1. **Generator** — the current password generator; keep the mobile authenticator link.
2. **Security** — the current health report (score, weak, reused, old); still reads the account store only; drilling into an issue opens that account entry.

Generator and Security no longer exist as destinations; both appear only inside Securities. The
authenticator keeps its own route, so no page shows one of the two without the other.

Account quick search stays account-only. Cards are copied from Wallet.

---

## 4. Decisions and rejected alternatives

| Decision | Why |
|----------|-----|
| Separate card store | One schema, one failure domain, independent merge and backup key |
| Account store stays account-only | Security scoring, search, and merge keep their existing meaning |
| Masked display, reveal on demand | A card list on screen is the main shoulder-surfing risk |
| Last four digits only in the list | Enough to recognise a card without exposing the number |
| Checksum failure is a warning | A valid but unusual number must not be unsaveable |
| Preserve unknown fields on a record | A newer client's field must not be stripped by an older save |

Rejected: a kind field on accounts, a shared wallet list, storing a card number in plaintext, and card scanning or network tokenisation in this release.

---

## 5. Components

| Responsibility | Role |
|---------------|------|
| Card records | Fields, validation, last-four derivation, unknown-field preservation |
| Card store | Load, save, export, re-encryption on restore, merge by identifier |
| Backup integration | Optional card list in the payload, restore ordering |
| App navigation | Account / Wallet / Securities destinations and index mapping |
| Wallet UI | List, detail, editor, reveal and copy |
| Securities UI | Hosts the generator and the security report |
| Localization | New strings in every supported language |

---

## 6. Security properties

- [ ] The account destination is labelled Account and edits only account records.
- [ ] Generator and Security are one Securities destination; the authenticator is still reachable.
- [ ] Cards live in their own record set, not in the account store.
- [ ] Number, security code, and PIN are ciphertext; lists show only the last four digits.
- [ ] Backup and transfer carry the card list and re-encrypt card secrets.
- [ ] Account merge behaviour is unchanged; the security score and password count ignore cards.
- [ ] A build that predates Wallet can still import accounts and authenticator items from a file that also contains cards.
- [ ] Deleting a card does not touch accounts or authenticator records.
- [ ] Search never decrypts a card number.
- [ ] An older build ignores the card list without rewriting it.

---

## 7. Risks and open items

| Risk | Mitigation |
|------|------------|
| Card metadata (label, holder, last four, expiry) is plaintext at rest | Accepted, same model as entry titles; secrets are encrypted |
| A restore failure could drop unknown future fields | Preserve unknown fields; never rebuild the list from a partial model |
| Older clients silently ignore the card list | Release note: upgrade all paired devices before relying on Wallet |
| Navigation index reuse after removing Generator / Security | Map or reset the stored index |
| No stable account identifier yet | Cards use their own identifier and do not depend on account identity |

---

## 8. Provenance

Summarizes the 2.4.0 scope as planned. Storage keys, source locations, and internal identifiers are withheld under the disclosure model in the [index](../README.md).
