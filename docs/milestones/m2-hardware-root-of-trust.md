# M2 — Hardware root of trust

| | |
|---|---|
| **Release** | 2.2.7 |
| **Status** | Shipped on Windows, macOS, iOS, and Android; Linux and web remain on OS secure storage |
| **Depends on** | M0, M1 |
| **Unlocks** | M4 (database key derivation), M7 (platform presence) |
| **Theme** | The vault key is unusable to a same-user process without user presence |

---

## 1. Goal

Before M2 the vault key rested in platform secure storage. That protects against another user or another machine, but not against a process already running as the logged-in user. M2 changes where the key rests and what it takes to release it:

- The vault key is wrapped by a key that **cannot be exported** from the device's security hardware or OS keystore.
- Releasing it requires **user presence** once per application start.
- A copied app-data folder is useless on a hardware-backed platform.

The vault ciphertext does not change. The vault key is still 32 bytes and its per-secret encryption format is untouched.

---

## 2. Problem

Secure storage only guards the file, not the key:

| Situation | Before M2 |
|-----------|-----------|
| Another user on the same machine | Protected |
| The app-data folder copied to another machine | Protected |
| Malware running as the logged-in user | **The key is readable without any prompt** |
| A lock screen or a biometric toggle | **No effect — the attacker never opens the UI** |

The last two rows are the reason M2 exists. A user-facing lock is not a key boundary: anything that can read the secure-storage entry as the logged-in user can decrypt the vault without ever showing a prompt.

**Requirement:** a process running as the logged-in user must not be able to obtain the vault key from disk without the user being present.

---

## 3. Design

### 3.1 Principle

The key is wrapped, not stored. The unwrapping key lives inside a security boundary the application cannot read out, and the operation that unwraps is gated by a user gesture or a device credential.

Three properties follow:

1. **Non-exportable wrap.** The wrapping key never exists in a form that can be copied off the device.
2. **Presence-gated release.** Unwrapping requires biometric, device-credential, or device-PIN approval — not merely a file read.
3. **Stable ciphertext.** Changing how the key is wrapped never rewrites vault contents.

### 3.2 Capability tiers

Rather than one implementation per platform, the product targets a capability tier and picks the best one the device supports. Tiers are ordered; a device always uses the highest tier it can satisfy.

| Tier | Custody | Presence | Copied app-data folder |
|------|---------|----------|------------------------|
| A | Device security chip | OS biometric or device credential | Cannot unwrap |
| B | Device security chip | Device credential prompt | Cannot unwrap |
| C | Device security chip | Application PIN, verified inside the chip | Cannot unwrap; chip-enforced retry limit |
| D | OS keystore, no chip | OS gesture | Cannot unwrap silently; weaker if the whole user profile is copied |
| E | Memory-hard wrap from the application PIN | Application PIN | Can be attacked offline; used only when nothing above is available |

**Supported today**

| Platform | Custody available |
|----------|-------------------|
| Windows | Device security chip where present, with or without an OS gesture; OS keystore otherwise; application-PIN wrap as the floor |
| macOS, iOS | Device security chip, released after a device-credential prompt |
| Android | Hardware-backed key storage where present; application-PIN wrap on emulators and devices without it |
| Linux, web | OS keystore, with application-PIN wrap as the floor. A chip-backed tier is planned for Linux |

Capability detection happens at runtime and is never taken from a flag the user sets. A device that reports a chip but cannot complete the operation is treated as not having one.

### 3.3 What is stored

Only a **wrap record** rests on disk:

- the wrapped vault key,
- which tier was selected and a non-secret reference the platform uses to locate the wrapping key,
- where the tier allows it, a second copy of the vault key wrapped under the application PIN so a forgotten PIN can be reset.

The record never contains the unwrapped vault key and never contains the PIN in readable form. The wrap record is the only durable copy; there is no server-side copy and no escrow.

### 3.4 Presence and session behaviour

- **Once per application start.** The gesture is requested when the application launches, not on every unlock of the UI.
- **UI lock keeps the session.** Locking the window or resuming from the system tray does not discard the key and does not prompt again.
- **New process, new prompt.** A fresh process always requires presence.
- **No silent downgrade.** Cancelling the prompt leaves the vault locked. The app does not fall back to a weaker tier on the same attempt.

Once released, the key does not rest in the application runtime as a long-lived plaintext buffer. On Windows, macOS, iOS, and Android it is held inside a protected native session and used per operation; a crash dump does not contain a readable vault key. On Linux and web it is held in process memory until a native backend exists.

### 3.5 PIN rules

| Rule | Behaviour |
|------|-----------|
| Format | A bounded digit PIN, with an enforced minimum length |
| When asked | Once per application start; not on UI lock or tray resume |
| Wrong entries | After a bounded number of consecutive failures, further attempts are refused for a short cooldown; a success resets the counter |
| Chip-enforced limit | Where the tier uses a chip, repeated failures also hit the hardware retry limit; the app does not reset it |
| Changing the PIN | Re-wraps the same vault key; vault contents are untouched |
| Forgotten PIN | Resettable where the device supports an OS gesture plus a chip-sealed PIN copy. Where it does not, the app states that recovery is unavailable rather than pretending otherwise |
| Stored PIN | Never retrievable in readable form. Where a chip can seal it, a sealed copy exists; where it cannot, no readable copy exists anywhere |

The exact PIN length, the failure count, and the cooldown are tuning values and are withheld. What
a user observes is the behaviour described above, and every claim about it is limited to that.

### 3.6 Upgrade path

A vault created before M2 is migrated on the first launch after the upgrade:

- the existing key is wrapped under the best available tier **before** anything is deleted;
- the new wrap is verified by unwrapping it and comparing with the existing key;
- only then is the old storage entry removed;
- if wrapping or verification fails, the old entry is kept and the vault stays locked.

A vault is never re-keyed to recover from a wrapping failure. A corrupt or unreadable wrap record leaves the app locked with an explicit explanation; it never mints a new vault key over existing data.

---

## 4. Decisions and rejected alternatives

| Rejected | Why |
|----------|-----|
| Sealing the key to the chip with no authorization | Any process on that boot could unwrap it, which fails the requirement |
| An OS credential store readable by any same-user process | It is exactly the threat M2 targets |
| A biometric "passed" flag as the gate | A boolean does not bind the key; it can be reported without the key being released |
| A platform primitive that can only sign, not decrypt | It cannot unwrap a wrapped key |
| A long-lived plaintext vault key in the application runtime | Exposed to crash dumps and memory inspection |
| Encrypting the key in memory with another application secret | Ciphertext and the means to unwrap it travel together; no protection against a dump |
| Falling back to the PIN after a cancelled gesture | Would let a local attacker dismiss the prompt and guess the PIN |
| Storing the PIN in a vault entry | Mixes a device credential with vault data |

---

## 5. Components

Published at the level of responsibility, not code structure:

| Responsibility | Role |
|----------------|------|
| Capability detection | Determine which tier the device can satisfy, at runtime |
| Key wrapping | Wrap and unwrap the vault key inside the platform security boundary |
| Protected session | Hold the released key for the life of the process without a readable resting copy |
| PIN custody | Set, change, verify, and — where supported — reset the PIN without storing it readably |
| Lifecycle | Cold start, migration, failure and lockout states |
| Lock service | Lock state, retry limits, and user-facing recovery messages |

The internal structure of each platform implementation is not published.

---

## 6. Security properties

These are the guarantees M2 is expected to provide, stated so they can be checked from outside the implementation:

- [x] A stolen disk, or the app-data folder copied to another machine, does not yield the vault key on a hardware-backed platform.
- [x] A process running as the logged-in user cannot obtain the vault key without the user approving the request.
- [x] Cancelling the presence prompt leaves the vault locked, with no weaker fallback on that attempt.
- [x] After a successful start, locking the UI or resuming from the tray neither prompts again nor discards the key.
- [x] The key does not rest in the application runtime as readable plaintext on any hardware-backed platform.
- [x] A failing or absent security chip degrades to a documented lower tier instead of breaking the app or silently weakening the vault.
- [x] A corrupt wrap record keeps the vault locked and never creates a replacement key.
- [x] Changing the PIN preserves the vault and cannot strand it mid-change.
- [x] Every release is checked on real devices for each tier, including a machine with no security chip.

---

## 7. Risks and open items

| Risk / gap | Status |
|------------|--------|
| A live process that is already compromised could interfere during an operation | **Accepted and out of scope.** Hardware wrapping hardens offline copies and resting memory; it does not defeat code injection |
| The PIN-only tier can be attacked offline | Accepted where no security hardware exists; the setup screen says so and recommends an OS gesture |
| No chip-backed tier on Linux or web | Known gap; the claim "hardware-sealed" is documented as applying to Windows, macOS, iOS, and Android only |
| Presence removed after enrollment (gesture or chip unavailable) | The app falls back to what the device supports now and says so |
| Forgotten PIN with no OS gesture and no sealed copy | Not recoverable; the app states this instead of offering an unreachable recovery path |
| A compromised operating system | Out of scope; no application-level control survives it |

---

## 8. Provenance

Derived from the shipped behaviour of the 2.2.7 release and the public release history. Per-platform API choices, internal module structure, key-store item names, and native call sequences are withheld under the disclosure model in the [index](../README.md).
