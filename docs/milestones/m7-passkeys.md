# M7 — Passkeys

| | |
|---|---|
| **Release** | 2.6.0 |
| **Status** | Planned — roadmap only, no implementation |
| **Depends on** | M2 (hardware presence), M4 (sealed backup and merge), M5 (per-record store pattern) |
| **Unlocks** | — |
| **Theme** | Store WebAuthn credentials and act as a platform authenticator |

---

## 1. Goal

Store passkeys in the vault and expose Zafonyx Local as a platform authenticator, so a browser or native app can create and use a passkey without a browser extension.

Success means: a user registers a passkey on a website, the operating system routes the request to Zafonyx Local, the credential is created or an assertion is signed from the encrypted vault, and the result returns to the relying party.

---

## 2. Problem

The vault stores passwords and authenticator codes but not WebAuthn credentials. As services move to passkeys, a password manager that cannot hold one becomes a partial record of a user's accounts.

A passkey is not a password or an authenticator seed:

| Property | Password / one-time code | Passkey |
|----------|--------------------------|---------|
| Secret | Symmetric secret or seed | Asymmetric private key |
| Verification | Server compares or derives a code | Relying party verifies a signature over a challenge |
| Identity | Service plus username | Relying-party identifier plus credential and user handle |
| Counter | None | Optional signature counter |
| User presence | App unlock | Platform gesture at assertion time |

Passkeys also need an operating-system integration. A Flutter-only implementation cannot be a platform authenticator on its own.

---

## 3. Design

### 3.1 Foundation (done in earlier milestones)

- Cross-platform Flutter app with a local encrypted vault.
- Hardware-wrapped vault key, released by a user gesture (M2).
- Encrypted relational store (M3).
- Sealed backup container and authenticated local transfer (M4).

### 3.2 Credential storage

Conceptual record:

A credential record holds a public credential identifier, the relying-party identifier, a user
handle, the public key, the private key, an optional signature counter, the transports the
credential supports, a display label, and created and updated timestamps.

Only the **private key is ciphertext**, decrypted while signing and cleared immediately after. The
public key and the credential identifier are not secrets; the relying-party identifier, user
handle, and counter are confidential metadata.

Key rules:

- The private key is never stored in plaintext and is cleared immediately after signing.
- The public key and credential identifier are not secrets.
- The relying-party identifier and user handle are required to match an assertion to the right service and account.
- The signature counter is preserved through backup and merge.

**Storage placement is an open decision.** One early proposal attached a passkey to an account entry. That conflicts with the one-record-type-per-store invariant that authenticator items, cards, and crypto records follow. The recommended shape is a separate passkey store and a passkey list in the backup payload, with an optional non-secret link to an account entry. Either choice must be settled before implementation; see [open-questions.md](../open-questions.md).

### 3.3 Platform authenticator

| Platform | Approach |
|----------|----------|
| Windows | Register with the OS passkey provider so system and browser prompts can route to the app |
| macOS | Provide the system credential-provider integration |
| Linux | No uniform OS passkey provider today; scope open |
| iOS / Android | Scope decision pending — see [open-questions.md](../open-questions.md) |

**Standards work:** WebAuthn Level 2 or later, COSE key encoding, CBOR, and ES256/EdDSA signature suites, using maintained libraries rather than hand-written primitives.

**Flow:**

```
browser / app → OS WebAuthn UI → Zafonyx Local credential provider
  create: validate relying-party identifier → generate a key pair
          → store the encrypted private key → return attestation
  get:    match credential and relying-party identifier
          → require user presence → sign the challenge → return assertion
```

The OS gesture is the user-presence check. A platform authenticator must not sign silently.

### 3.4 Local authentication (mostly done)

| Method | Status |
|--------|--------|
| App PIN | Done |
| Device biometrics | Done |
| Hardware security key as an unlock method | Optional, not required |

### 3.5 Transfer

Passkeys must travel in the same sealed backup container as accounts and authenticator items, re-encrypted under the destination key. The merge pattern is the one M4 established: same identifier, newer updated time wins.

### 3.6 Local daemon and browser extension (optional, last)

Only if the system authenticator turns out to be insufficient for a supported browser or operating
system would a local bridge be considered, paired with a companion browser extension. It would add
a local network attack surface and per-browser maintenance, so it is deferred until the platform
authenticator ships and the gap is real. No bridge is designed or scheduled.

---

## 4. Decisions and rejected alternatives

| Decision | Why |
|----------|-----|
| System platform authenticator, not extension-first | Native experience, no per-browser install, OS-mediated user presence |
| Private key encrypted under the vault key | Same at-rest model as passwords and authenticator seeds |
| Sign only after an OS gesture | A platform authenticator must not assert without user presence |
| Browser extension deferred | The daemon is a fallback, not the architecture |
| Passkeys travel through the existing sealed container | No new transport; re-encrypt by identifier |

Rejected: an extension-only product, a plaintext private key, signing without user presence, and a separate cloud passkey sync service.

**Open:** whether passkeys live in a separate store or embedded on an account entry, and which platforms are in scope for 2.6.0.

---

## 5. Components

| Responsibility | Role |
|---------------|------|
| Passkey records | Fields, matching keys, merge, backup list |
| Encrypted store integration | New record set and a schema upgrade |
| WebAuthn engine | Challenge handling, encoding, assertion construction |
| Platform providers | OS registration and the bridge into the app, per platform |
| Backup and transfer | Optional passkey list, re-encryption on restore |
| UI | Passkey list, detail, account-link affordance |

---

## 6. Security properties

- [ ] A passkey can be created from a browser or native app through the OS prompt, with the app as the provider.
- [ ] The private key is ciphertext at rest and plaintext only while signing.
- [ ] An assertion requires a user-presence gesture; there is no silent signing path.
- [ ] Relying-party and user-handle matching prevent a credential from being used for another service.
- [ ] The signature counter updates after an assertion and survives backup and merge.
- [ ] A passkey round-trips through the sealed backup container and local transfer with re-encryption.
- [ ] Each supported platform documents its provider path; an unsupported platform shows a clear state instead of failing opaquely.
- [ ] No browser extension is required for the primary path.

---

## 7. Risks and open items

| Risk | Mitigation |
|------|------------|
| OS authenticator APIs differ and may require privileged registration or signing | Prototype the Windows and macOS paths early; keep the app-facing interface narrow |
| Linux has no uniform platform-authenticator API | Treat Linux as the daemon candidate, or scope 2.6.0 to Windows and macOS first |
| Attestation and relying-party validation are easy to get wrong | Prefer platform APIs; test with real services |
| Passkeys are high-value and hard to back up | Include them in the sealed backup and transfer from day one |
| Separate store vs embedded record | Decide before schema work; the rest of the architecture favours a separate store |
| Signing requires an unlocked vault | Define the unlock and presence flow; never keep the vault key in a long-lived plaintext buffer |
| Browser coverage gaps | The daemon and extension are the fallback, not the plan |

---

## 8. Provenance

Summarizes the 2.6.0 scope as planned; no part of it is implemented. Platform API surfaces, bundle identifiers, and source locations are withheld under the disclosure model in the [index](../README.md).
