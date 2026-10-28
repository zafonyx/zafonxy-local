# Threat model

Who Zafonyx Local defends against, which assets it protects, where the trust boundaries fall,
and what it deliberately does not defend against.

| | |
|---|---|
| **Document status** | Public |
| **Applies to** | 2.0 through 2.3.0 (shipped); planned items marked |
| **Claim identifiers** | `THR-nn` |
| **Method** | Asset-based model with STRIDE categories per trust boundary |

This is a summary written for review, not a substitute for your own assessment. Where this
document and [open questions](open-questions.md) disagree, the limitation wins.

---

## 1. Assets

| Asset | Why it matters | Where it lives |
|-------|----------------|----------------|
| Vault secrets | Passwords, one-time-code seeds, card secrets, crypto recovery material | Ciphertext on disk; plaintext only in a wipeable buffer while revealed |
| Vault metadata | Category names, entry titles, notes, counts | Confidential, stored as metadata; sealed inside a backup container |
| Vault key | One 32-byte key opens everything | Never at rest unwrapped; released only after user presence |
| Device credential | Unlocks the app; may seal a PIN copy | Never transmitted, never used as a transfer credential |
| Backup passphrase | The only key to a container that has left the device | Known only to the user; no escrow, no recovery |
| Pairing token | Carries the entropy for a transfer session | Displayed locally, never transmitted |
| Passkey private keys (planned) | Authentication to relying parties | Ciphertext at rest; plaintext only while signing |
| Entitlement state | Whether the paid surfaces are unlocked | Platform store; no server-side licence |

**`THR-01`** The confidentiality of a secret covers its metadata. A category name or an entry
title is treated as confidential as the password beside it.

---

## 2. Trust boundaries

```
┌──────────────────────────────────────────────────────────┐
│ Device                                                   │
│  ┌──────────────────────────┐   ┌─────────────────────┐  │
│  │ App process              │   │ Security boundary   │  │
│  │  vault key (in memory)   │──►│  non-exportable     │  │
│  │  wipeable secret buffers │   │  wrapping key       │  │
│  └──────────────────────────┘   └─────────────────────┘  │
│  ┌──────────────────────────┐                            │
│  │ Local storage            │                            │
│  │  ciphertext · wrap record│                            │
│  └──────────────────────────┘                            │
└──────────────────────────────────────────────────────────┘
            │                                   │
            │ untrusted network                 │ platform store
            ▼                                   ▼
   pairing peer / LAN observer          purchase entitlement
```

| Boundary | Crossing it requires | What a failure exposes |
|----------|----------------------|------------------------|
| User → app | OS biometric, device credential, or application PIN | Unlocked vault for that session |
| App → security boundary | A key operation the boundary performs, never key export | Nothing: the wrapping key cannot be read out |
| App → local storage | Nothing; anything running as the user can read files | Ciphertext and the wrap record only |
| App → network | An explicit transfer the user started | A sealed, one-shot payload |
| App → platform store | A purchase or restore | Entitlement state; no vault data |

---

## 3. Adversaries and coverage

| # | Adversary | Capability | Covered? | How |
|---|-----------|-----------|----------|-----|
| **`THR-02`** | Opportunistic thief | Has the device or a copy of the app-data folder; no credentials | Yes, on tiers A–C | The wrap record cannot be unwrapped without presence |
| **`THR-03`** | Malware as the logged-in user | Reads any file the user can read; never opens the UI | Yes, on tiers A–C | Releasing the key needs a gesture the malware cannot forge |
| **`THR-04`** | Offline attacker with the app PIN tier | Copies the profile and brute-forces the PIN | **Partly** | Memory-hard wrap only; a short PIN is weak. Stated at setup |
| **`THR-05`** | LAN observer during pairing or transfer | Sees every packet | Yes | Post-quantum handshake; every body sealed; token never transmitted |
| **`THR-06`** | Malicious receiver of a share | Has a valid pairing code and PIN | Yes | One-way enforced by the sender; write path refused for the session |
| **`THR-07`** | Holder of a stolen backup file | Has the container, not the passphrase | Yes, subject to passphrase entropy | Whole document sealed; no metadata in the clear; KDF bounded |
| **`THR-08`** | Peer forcing a weaker exchange | Old protocol version, replayed messages | Yes | Explicit version gate, no fallback; replay refused |
| **`THR-09`** | Same-user process during a crypto operation | Injects or hooks while the vault is open | **No** | Stated residual risk; see §5 |
| **`THR-10`** | Shoulder surfer | Photographs the screen | Partly | Masked display, reveal on demand, screen capture blocked where the OS allows |
| **`THR-11`** | Clipboard and history observer | Reads clipboard managers and OS history | Partly | Single copy path, auto-clear, platform history purged where allowed |
| **`THR-12`** | Compromised OS or hypervisor | Full control of memory and I/O | **No** | Out of scope for any application-level design |

---

## 4. STRIDE summary

| Category | Example against this product | Control |
|----------|------------------------------|---------|
| Spoofing | A fake peer answering a pairing request | Pairing token plus session PIN; every rejection looks identical to the peer |
| Tampering | Altering a backup header or a transfer body | Header fully authenticated; each direction keyed; any change rejected |
| Repudiation | — | Not applicable: no server-side action to repudiate |
| Information disclosure | Metadata in a backup; secrets in logs or crash dumps | Metadata sealed with content; byte-only buffers; logging excludes contents |
| Denial of service | Exhausting memory with a crafted KDF header; squatting a pairing window | Parameters bounds-checked before use; squatting accepted as an availability nuisance |
| Elevation of privilege | Reading the wrap record to obtain the key; silent passkey signing | Non-exportable wrapping key; presence gate; no silent assertion path |

---

## 5. Residual risk

Accepted, documented, and not treated as defects. Each is stated in the product where a user
would otherwise assume otherwise.

| Risk | Reach | Why accepted |
|------|-------|--------------|
| A live compromised process can interfere during a cryptographic operation | Every platform | Hardware wrapping hardens offline copies and resting memory, not a runtime being watched from inside |
| Tier E (PIN-only) resists offline attack only by KDF cost | Devices with no security hardware | The setup screen says so and recommends an OS gesture |
| No chip-backed tier on Linux (planned) | Linux | Known gap for the planned platform; the hardware-sealed claim is scoped accordingly |
| Backup passphrase entropy is the user's responsibility | File backups | Only a minimum length is enforced; there is no strength meter |
| Lost backup passphrase is unrecoverable | File backups | By design: no escrow, no server, no back door |
| A same-network host can occupy a pairing window | LAN transfer | Availability nuisance; no confidentiality impact |
| Metadata is plaintext at rest on the device | Local storage | Same model as entry titles; secrets are what is encrypted, and the device boundary is the boundary |
| A compromised operating system defeats everything above | Every platform | No application-level control survives it |

**`THR-13`** Every claim in this document covers resting data and network transport. No claim
here survives a compromised operating system or a live injected process.

---

## 6. Coverage by milestone

| Milestone | Threat closed or narrowed |
|-----------|----------------------------|
| M0 | Baseline: local vault, per-secret encryption, PIN lock |
| M1 | Secret lifespans in memory, clipboard exposure, crash-dump exposure |
| M2 | File-level key theft and same-user malware without presence (`THR-02`, `THR-03`) |
| M3 | Whole-document corruption and partial writes; transactional integrity |
| M4 | Backup confidentiality, transfer confidentiality, downgrade and replay (`THR-05`–`THR-08`) |
| M5–M7 (planned) | Record-type isolation; wallet and passkey secrets; silent assertion |

---

## 7. Reading a claim

- A claim names the property, not the mechanism. If you need the mechanism to reach a decision,
  that is a question for a written agreement — see [assurance](assurance.md#6-evidence-under-nda).
- If a platform is not named in a claim, the claim does not cover it.
- "Hardware-sealed" always means the four-platform scope in
  [cryptography §3](cryptography.md#3-key-custody-tiers).
- Documentation that appears to claim more than this section permits should be reported, not
  assumed to be the stronger reading.

---

## 8. Provenance

Consolidates the threat material published per milestone — [M2 §2](milestones/m2-hardware-root-of-trust.md#2-problem),
[M4 §1](milestones/m4-zero-trust-transfer.md#1-goal), [open questions §4](open-questions.md#4-how-to-read-a-security-claim-here)
— and the cross-cutting invariants in [00-overview §3](milestones/00-overview.md#3-cross-cutting-invariants).
No internal threat-model artefact is cited or reproduced.
