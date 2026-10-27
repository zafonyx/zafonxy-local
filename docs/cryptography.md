# Cryptography

The cryptographic design of Zafonyx Local: which primitives protect what, where keys rest, what
it takes to release them, and which parts of the design are unproven.

| | |
|---|---|
| **Document status** | Public |
| **Applies to** | 2.0 through 2.3.0 (shipped); passkey primitives are planned for 2.6.0 |
| **Claim identifiers** | `CRY-nn`, referenced from the [enterprise FAQ](enterprise-faq.md) and [assurance](assurance.md) |
| **Reviewed against** | FIPS 197, FIPS 203, FIPS 180-4, RFC 9106, RFC 6238, RFC 8446, WebAuthn Level 2 |

Claims here are about **data at rest and data in transit between devices**. They are not runtime
sandboxing claims. Where a claim has a limit, the limit is stated in the same section.

---

## 1. Key hierarchy

One 32-byte vault key protects the vault. Everything else is either a wrapper around it or a key
derived from it for one specific purpose.

```
user presence (biometric / device gesture)   or   application PIN
        │
        ▼
wrapping key inside the platform security boundary (non-exportable)
        │
        ▼
wrapped vault key  ──►  vault key (32 bytes, only in memory, only after presence)
                              ├── per-secret authenticated encryption
                              │     passwords · authenticator secrets · card secrets
                              │     crypto recovery material · passkey private keys
                              └── purpose-derived keys ──► database key
```

| Key | Size | Where it rests | Lifetime | Protects |
|-----|------|----------------|----------|----------|
| Vault key | 32 bytes | Never at rest unwrapped | Process lifetime after presence | Every secret record |
| Wrapping key | Platform-defined | Inside the security chip or OS keystore, non-exportable | Device lifetime | The vault key |
| Wrap record | Contains the wrapped vault key | On disk | Device lifetime | Nothing by itself; useless without the wrapping key |
| Database key | Derived from the vault key | Never at rest | Per store open | The relational store |
| Backup content key | Random per backup | Never at rest | One container, then wiped | The backup document |
| Passphrase wrapping key | Derived by KDF | Never written | One container open | The backup content key |
| Session direction keys | Derived per transfer | Never at rest | One transfer session | One direction of a transfer |
| Per-secret nonce | Random per encryption | Stored beside the ciphertext | Per ciphertext | Nonce uniqueness only |

**`CRY-01`** The vault key never leaves the device and is never stored unwrapped. Only a wrap
record rests on disk.

**`CRY-02`** The vault ciphertext format is stable across releases. A custody change rewrites the
wrap record, not vault contents, so changing the PIN or the custody tier never re-encrypts
entries.

**`CRY-03`** The database key is not the vault key. It is derived from the vault key for that
purpose alone, so exposure of one derived key does not expose the vault key. See
[M3 §3.1](milestones/m3-encrypted-data-store.md#31-database-and-keys).

---

## 2. Primitives

| Purpose | Primitive | Parameter class | Standard | Claim |
|---------|-----------|-----------------|----------|-------|
| Secret encryption at rest | AES-256-GCM | 256-bit key, 96-bit nonce, 128-bit tag | FIPS 197, SP 800-38D | `CRY-04` |
| Backup passphrase stretching | Argon2id | Memory-hard; parameters travel with the container and are bounded-checked before use | RFC 9106 | `CRY-05` |
| Transfer key agreement | ML-KEM-768 | Post-quantum KEM, ephemeral per session | FIPS 203 | `CRY-06` |
| Session transport sealing | Authenticated encryption with per-direction keys | One key per direction per session | — | `CRY-07` |
| One-time codes | TOTP | SHA-1, SHA-256, SHA-512; standard digit counts and periods | RFC 6238 | `CRY-08` |
| Integrity hashing | SHA-2 family | 256-bit and above | FIPS 180-4 | `CRY-09` |
| Elliptic-curve signatures (planned) | ES256 and EdDSA over COSE keys | WebAuthn credential keys | WebAuthn L2, RFC 9052 | `CRY-10` |
| Encrypted relational store | SQLCipher over SQLite, keyed by the database key | Build refuses to open an unencrypted store | — | `CRY-11` |
| Randomness | OS CSPRNG | Every key, nonce, token, and session PIN | — | `CRY-12` |

**`CRY-04`** Every secret record is individually authenticated-encrypted under the vault key with a
fresh random nonce. A nonce is never reused under the same key.

**`CRY-05`** A backup passphrase is stretched with a memory-hard KDF whose declared parameters are
read from the container and bounds-checked *before* the KDF runs, so a crafted file cannot
exhaust device memory.

**`CRY-06`** Transfer sessions use an ephemeral post-quantum KEM, so a recorded session cannot be
opened later by a quantum adversary, and no long-term key is exposed by a single session.

**`CRY-07`** Each direction of a transfer session has its own key. Both sides refuse a replayed
or out-of-session message.

**`CRY-08`** One-time codes follow RFC 6238. Per-record parameters are preserved on import, so a
generated code matches the app it came from.

**`CRY-09`** Integrity hashing uses SHA-2 at 256 bits and above. Neither MD5 nor SHA-1 is used for
an integrity decision.

**`CRY-10`** Passkey signatures will use ES256 and EdDSA over COSE keys with maintained libraries,
not hand-written primitives. Planned for M7; no part is shipped.

**`CRY-11`** The relational store is encrypted under the purpose-derived database key. A build that
cannot confirm the encryption layer is active refuses to open the store rather than writing an
unencrypted vault.

**`CRY-12`** All key material, nonces, pairing tokens, and session PINs come from the operating
system CSPRNG. No application-level PRNG is used for anything security-relevant.

Parameters that are fixed by a published standard are quoted exactly above, because withholding
them would only obscure a standard already in the public domain. Product tuning values — retry
counts, cooldowns, KDF cost, timeouts — are published as ranges or qualitative statements; the
policy and its rationale are in [docs/README.md](README.md#disclosure-model).

---

## 3. Key custody tiers

The product targets a **capability tier** and uses the highest one the device can satisfy.
Detection happens at runtime and is never taken from a user-settable flag. A device that reports
a security chip but cannot complete the operation is treated as not having one.

| Tier | Custody | What releases the key | Copied app-data folder |
|------|---------|-----------------------|------------------------|
| A | Device security chip | OS biometric or device credential | Cannot unwrap |
| B | Device security chip | Device credential prompt | Cannot unwrap |
| C | Device security chip | Application PIN, verified inside the chip | Cannot unwrap; chip-enforced retry limit |
| D | OS keystore, no chip | OS gesture | Cannot unwrap silently; weaker if the whole user profile is copied |
| E | Memory-hard wrap from the application PIN | Application PIN | Can be attacked offline; used only when nothing above is available |

**Coverage today**

| Platform | Best available tier |
|----------|---------------------|
| Windows | Chip-backed where present (A/B/C), OS keystore otherwise (D), PIN wrap as the floor (E) |
| macOS, iOS | Chip-backed, released after a device-credential prompt (A/B) |
| Android | Hardware-backed storage where present (A/B/C), PIN wrap on emulators and devices without it (E) |
| Linux, web | OS keystore (D) with PIN wrap as the floor (E); a chip-backed tier is planned for Linux |

**`CRY-13`** On every platform where tier A, B, or C is in use, a process running as the logged-in
user cannot obtain the vault key from disk without the user approving a release.

**`CRY-14`** The "hardware-sealed" claim applies to Windows, macOS, iOS, and Android only. On
Linux and web the vault key is protected by OS secure storage, and a copied app-data folder is
not useless to the same user there. This limit is repeated wherever the claim appears.

Full tier behaviour, session lifetime, and PIN handling: [M2](milestones/m2-hardware-root-of-trust.md).

---

## 4. Secret handling in memory

**`CRY-15`** A decrypted secret is held in a wipeable byte buffer with exactly one owner, and is
cleared when it is no longer displayed. A secret is never converted to an immutable string type
inside the vault flow, so it cannot survive until garbage collection or into a crash dump.

**`CRY-16`** Decrypted secret material is never written to a log, a crash report, a diagnostic
file, or a network body. Only lifecycle and error metadata is logged.

Residual gaps in this area — input-method text, paste paths, clipboard managers, and the absence
of off-heap isolation — are listed in [open questions](open-questions.md#2-known-limitations)
rather than in a footnote.

---

## 5. Envelope encryption for backups and transfer

A backup is a versioned header plus one authenticated ciphertext over the whole document.

```
passphrase ──memory-hard KDF──► wrapping key ──► unwrap content key ──► decrypt document
```

- The content key is random, used once, and wiped after use.
- Every secret inside the document keeps its own ciphertext, re-sealed under the content key, so
  no secret ever appears as plaintext in a document that leaves the device.
- The header carries only what a reader needs to open the body: format version, KDF parameters,
  and the wrapped content key. Header fields are authenticated; changing any of them invalidates
  the body.
- For LAN transfer the passphrase material is a pairing token plus a per-session PIN. The token
  is high-entropy and never transmitted; the PIN is low-entropy and never contributes to session
  keys, so there is nothing for an offline attacker to test.

**`CRY-17`** A stolen backup file yields no passwords, no category names, no entry titles, and no
vault key.

Full design and rejected alternatives: [M4](milestones/m4-zero-trust-transfer.md).

---

## 6. Standards mapping

Provided so a reviewer can check our vocabulary against recognised sources.

| Area | Standard | How this design relates |
|------|----------|-------------------------|
| Symmetric encryption | FIPS 197, NIST SP 800-38D | AES-256-GCM in its standard construction |
| Key management vocabulary | NIST SP 800-57 Part 1 | "Wrap", "derived key", and "key lifetime" used in the standard sense |
| Post-quantum KEM | FIPS 203 (ML-KEM) | ML-KEM-768 |
| Password hashing / KDF | RFC 9106 (Argon2) | Argon2id, memory-hard |
| One-time passwords | RFC 6238 (TOTP) | Per-record parameters preserved on import |
| Transport authentication | RFC 8446 vocabulary | Not TLS; the sealing pattern follows the same authenticated-record model |
| WebAuthn credentials | WebAuthn Level 2, RFC 9052 (COSE), RFC 8949 (CBOR) | Planned, M7 |
| Vulnerability handling | ISO/IEC 29147, ISO/IEC 30111 | Referenced in [SECURITY.md](../SECURITY.md) |

Naming a standard describes the construction we implement. It does **not** mean the product is
validated, certified, or approved under that standard. See [assurance](assurance.md).

---

## 7. What is not claimed

- **No FIPS 140-3 validation.** Validated modules are not used or claimed. AES-256-GCM and the
  post-quantum KEM follow the named standards; that is not a certification.
- **No formal verification.** The design has been reviewed, not machine-checked or proven.
- **No third-party cryptographic audit yet.** See [assurance](assurance.md).
- **No protection against a compromised operating system**, and none against code injected into
  the process during a cryptographic operation. On tier E, no protection against offline attack
  on the PIN.
- **No forward secrecy for vault contents.** The vault key is long-lived by design; per-session
  ephemerality applies to transfer sessions only.
- **No deniable encryption, and no hidden volume.** There is one vault and it is what it says.

---

## 8. Provenance

Derived from the shipped cryptographic behaviour of 2.0 through 2.3.0 as described in
[M0](milestones/m0-foundation.md#33-cryptography-and-key-storage),
[M1](milestones/m1-secret-safe-vault.md#32-byte-only-secret-handling),
[M2](milestones/m2-hardware-root-of-trust.md),
[M3](milestones/m3-encrypted-data-store.md), and
[M4](milestones/m4-zero-trust-transfer.md), with M7 for the planned signature suites. Per-platform
API choices, key-store item names, wire layouts, and exact cost parameters are withheld under the
[disclosure model](README.md#disclosure-model).
