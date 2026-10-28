# Open questions and known limitations

Decisions that are still open in the published design, and the limits of the shipped product that users and integrators should know about. Nothing here blocks reading the milestones.

| | |
|---|---|
| **Document status** | Public |
| **Applies to** | 2.0 through 2.3.0 (shipped); open decisions concern 2.4.0 through 2.6.0 |
| **Use with** | [assurance](assurance.md) and the [threat model](threat-model.md) |

---

## 1. Open scope decisions

| # | Question | Why it matters | Current leaning |
|---|----------|----------------|-----------------|
| Q1 | Does a passkey live in its own store, or attached to an account entry? | A schema decision is expensive to reverse and affects backup and merge. | A separate passkey store, a passkey list in the backup payload, and an optional non-secret link to an account entry. Attaching passkeys to account entries conflicts with the one-record-type-per-store invariant. |
| Q2 | Which platforms are in scope for the first passkey release? | The operating-system integration work differs greatly per platform. | Windows and macOS first; mobile next; Linux only through an optional local bridge, and only once the platform ships. |
| Q3 | Is a hardware-backed key backend in scope for Linux? | Without one, the "hardware-sealed key" claim covers Windows, macOS, iOS, and Android only. | Undecided. Until then a Linux build would rely on OS secure storage and would say so. |
| Q4 | How does a user recover a forgotten PIN on a machine with no OS gesture and no hardware-sealed PIN copy? | Those users currently have no reset path. | A peer-assisted recovery path is an option; the alternative is to state plainly that recovery is unavailable. |
| Q5 | Do account records need a stable identifier? | Cards, authenticator items, crypto records, and passkeys already have their own identifiers. Accounts are still addressed by category and title. | Deferred until a feature needs cross-record links or finer conflict handling. |
| Q6 | Is the local bridge and browser extension ever built for passkeys? | It adds a loopback service and per-browser maintenance. | Only as a fallback if the platform authenticator cannot cover a supported browser or OS. |

---

## 2. Known limitations

| Limitation | What it means in practice |
|------------|---------------------------|
| No hardware-sealed key on Linux (planned) | Linux is not supported yet. When it ships, the vault key will be protected by OS secure storage only, so a copied app-data folder will not be unusable to the same user there, unlike the hardware-backed platforms. |
| PIN-only wrap can be attacked offline | Used only on devices with no security hardware. A short PIN is weak under offline attack; the setup screen says so. |
| A live, already-compromised process is out of scope | Hardware wrapping protects offline copies and resting memory. It does not defeat code injection or hooking during a cryptographic operation. |
| Backup passphrase entropy is the user's responsibility | Only a minimum length is enforced. A weak passphrase weakens the container regardless of the KDF. |
| No recovery for a lost backup passphrase | By design. There is no escrow, no server, and no back door. |
| A host on the same network can exhaust a pairing window with bogus requests | Availability nuisance while a pairing code is displayed; no effect on confidentiality. |
| Silent signing is impossible by design | Passkey assertions require a user-presence gesture, so a background process cannot assert on the user's behalf. |
| The device lock PIN is not a transfer credential | Sharing uses a per-session PIN shown on the sending device. A receiver never needs the sender's device PIN. |

---

## 3. Compatibility and upgrade rules

- **Older clients ignore newer record lists.** A build that predates a record type merges what it understands and leaves the rest untouched. Users should upgrade every paired device before relying on a new record type.
- **Legacy backup containers are refused, not read.** Earlier formats did not meet the current confidentiality bar; keeping a reader would keep that weakness reachable.
- **Protocol versions are gated.** A peer that does not advertise the current transfer protocol is refused before connecting. There is no downgrade path.
- **A corrupt or unopenable vault never mints a new key.** The app stays locked and offers an explicit, confirmed reset instead.
- **Vault ciphertext is stable across upgrades.** A key-custody change rewrites the wrap record, not the vault contents.

---

## 4. How to read a security claim here

Claims in these documents are about **resting data and network transport**. When a document says the key is hardware-sealed, it means an attacker who copies the disk or the app-data folder cannot unwrap it without the user's gesture. It does not mean the running process is immune to inspection, and it does not cover a compromised operating system.

Where a limitation above applies to a claim, the limitation wins. Report documentation that contradicts this section rather than assuming the stronger reading.
