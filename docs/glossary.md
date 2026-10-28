# Glossary

Every term used across these documents, defined once, with the place it is explained in full.

| | |
|---|---|
| **Document status** | Public |
| **Applies to** | All documents in this repository |

---

## Keys and cryptography

**Vault key** — The single 32-byte symmetric key that protects vault contents. It never leaves the
device and is never stored unwrapped. [Cryptography §1](cryptography.md#1-key-hierarchy)

**Wrapping key** — A key held inside a device security chip or OS keystore that cannot be
exported. It encrypts (wraps) the vault key so the vault key need not rest in readable form.
[M2](milestones/m2-hardware-root-of-trust.md)

**Wrap record** — The only durable copy of the vault key: the wrapped key, plus which custody tier
produced it. Useless without the wrapping key.

**Hardware-sealed** — Wrapped by a key that cannot leave a security chip, released only after user
presence. Applies to Windows, macOS, iOS, and Android only. Linux is planned; web is not supported.
[Cryptography §3](cryptography.md#3-key-custody-tiers)

**Sealed** — Authenticated-encrypted under a key only the intended party can derive. Used for
secrets and containers, not for describing a device.

**Content key** — A random key, used once per backup container, that wraps each record's
ciphertext inside the document. Wiped after use.

**Database key** — A key derived from the vault key solely to open the encrypted relational store.
It is not the vault key. [M3 §3.1](milestones/m3-encrypted-data-store.md#31-database-and-keys)

**Purpose-derived key** — Any key derived from the vault key for exactly one use, so that its
exposure does not expose the vault key.

**Protected session** — The native session, available on chip-backed platforms, that holds the
released vault key and performs operations, so no long-lived plaintext key sits in the app.

**KDF (key derivation function)** — A deliberately slow function turning a passphrase into a key.
This product uses a memory-hard one for backups. [Cryptography §2](cryptography.md#2-primitives)

**Nonce** — A random value used once per encryption. Reuse under the same key is catastrophic for
authenticated encryption, so each encryption gets a fresh one.

**Authenticated encryption** — Encryption that also detects tampering, so a modified ciphertext is
rejected rather than decrypted to garbage.

**CSPRNG** — The operating system's cryptographically secure random generator; the only source of
key material, nonces, tokens, and session PINs here.

---

## Custody and access

**Custody tier** — The ranked capability level a device achieves for holding the vault key, from a
chip-backed presence gate down to an application-PIN wrap. A device uses the highest tier it can
satisfy. [Cryptography §3](cryptography.md#3-key-custody-tiers)

**User presence** — Proof that a human is at the device: a biometric, a device credential, or a
PIN verified inside a chip. Required to release the vault key; a background process cannot supply
it. [Cryptography §1](cryptography.md#1-key-hierarchy)

**Application PIN** — A device credential used to unlock the app. Never transmitted, never used as
a transfer credential, never stored in readable form.

**Device credential** — A biometric or lock credential owned by the operating system, distinct
from the application PIN.

---

## Records and storage

**Record type** — A class of stored item with its own store and its own backup key: accounts,
authenticator items, bank cards, crypto records, passkeys. Types never share a list.
[M5 §3.1](milestones/m5-wallet-bank-cards.md#31-navigation-and-information-architecture)

**Account store** — The original category-to-entries model holding logins. It holds nothing else.

**Encrypted relational store** — The single encrypted database that replaced whole-document
storage, enabling per-record writes and store-enforced constraints.
[M3](milestones/m3-encrypted-data-store.md)

**Metadata** — Category names, titles, notes, counts. Confidential; sealed inside a backup or a
transfer payload as if it were a secret. [Threat model §1](threat-model.md#1-assets)

**Wipeable buffer** — A byte buffer that can be zeroed, used for every decrypted secret instead of
an immutable string, and the reason a secret need not survive to garbage collection or a crash
dump. [M1 §3.2](milestones/m1-secret-safe-vault.md#32-byte-only-secret-handling)

---

## Backup and transfer

**Container** — The single backup format: a versioned header plus one authenticated ciphertext
over the whole document. Used for file backup and LAN transfer alike.
[M4 §3.1](milestones/m4-zero-trust-transfer.md#31-sealed-backup-container)

**Pairing token** — High-entropy data exchanged out of band to authorise a transfer. Never
transmitted over the network, so it cannot be captured in flight.

**Session PIN** — A low-entropy PIN generated per share and shown on the sending device. It
proves the receiver can see the sending screen; it never contributes to session keys.

**One-way sharing** — A share where the receiver can only fetch. Enforced by the sender refusing
the write path for the whole session, not by receiver behaviour.

**No silent downgrade** — Refusing an old peer rather than serving it a weaker protocol. There is
no fallback path.

**One-shot delivery** — A transfer payload is served once and then no longer advertised.

**Merge** — Combining received records into a local vault: same identifier keeps the newer update,
an unknown identifier is appended, and an unknown record type is left untouched.

---

## Assurance

**Claim identifier** — A stable label such as `CRY-04` or `THR-09`, defined once and citable from
a questionnaire or a review note. [Assurance §7](assurance.md#7-traceability)

**Security property** — A statement about behaviour that can be checked from outside the
implementation, including its negative cases.

**Residual risk** — Exposure that remains after the design, accepted on the record rather than
left implicit. [Threat model §5](threat-model.md#5-residual-risk)

**Disclosure model** — The rule set for what these documents publish and what they withhold, and
why. [docs/README.md](README.md#disclosure-model)
