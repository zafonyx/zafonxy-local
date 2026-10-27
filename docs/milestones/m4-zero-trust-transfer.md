# M4 — Zero-trust transfer

| | |
|---|---|
| **Release** | 2.3.0 |
| **Status** | Shipped |
| **Depends on** | M2 (hardware-wrapped key), M3 (transactional merge target) |
| **Unlocks** | M5 / M6 (backup-key extension), M7 (session patterns) |
| **Theme** | One sealed backup container and an authenticated, post-quantum transfer session |

---

## 1. Goal

- A stolen backup file reveals no passwords, no metadata, and no vault key.
- File backup, one-way sharing, and LAN transfer use one sealed container.
- Every transfer request and response is authenticated and encrypted; a passive observer learns only message sizes and timing.
- The device lock PIN never leaves the device.
- An old peer is refused instead of being served a weaker protocol.

M4 consolidates three older paths — file backup, one-way sharing, and LAN transfer — into one design. Each previously ran on its own machinery and a lower bar; all three now share the same container and the same session.

---

## 2. Problem

Before 2.3.0 the three paths did not share a design and did not meet the bar above. Four gaps motivated the rewrite:

| Gap | Why it was unacceptable |
|-----|-------------------------|
| Metadata sat outside the ciphertext | Anyone holding a backup file could read category names and entry titles |
| The container key rested on a secret that cannot carry the needed entropy | A file that leaves the device must resist offline attack by its holder |
| The control plane was not fully sealed | A LAN observer could learn more than message sizes and timing |
| A device credential was reused as a transfer credential | A sharing flow must not ask for the device lock PIN |

The earlier paths are retired. Their internal details are not published, and old peers are refused rather than supported.

---

## 3. Design

### 3.1 Sealed backup container

One container format serves file backup and LAN transfer.

A container is a versioned header followed by one authenticated ciphertext over the whole document. The header carries only what a reader needs to open the body — the format version, the key-derivation parameters, and the wrapped content key — and nothing about the payload. Field order and encoding are implementation detail.

Document contents:

- Accounts: category names, entry titles, descriptions, timestamps, and authenticator references.
- Authenticator records: label, issuer, and secret.
- Optional record lists added by later milestones.

Every secret inside the document is additionally sealed under a random per-backup **content key**, so per-record ciphertext keeps its existing form instead of appearing as plaintext in the document. The content key is random, used once, and wiped after use.

**Key hierarchy**

```
passphrase  --memory-hard KDF-->  wrapping key
                                   │
                                   ▼
                            unwrap content key  ──►  decrypt document
```

- The wrapping key never leaves memory and is never written anywhere.
- The passphrase for a file backup is user-chosen and enforced to a minimum length; there is no recovery path.
- For LAN transfer the passphrase material is the pairing token plus the session PIN, so a captured payload cannot be opened from the PIN alone.
- The header is fully authenticated: changing any header field invalidates the ciphertext.
- Declared KDF parameters are bounds-checked **before** the KDF runs, so a crafted file cannot exhaust memory on import.
- The cipher cannot distinguish a wrong passphrase from a corrupted file, so both surface as one message.
- Earlier container formats are refused rather than kept as read-only compatibility: they did not meet this bar, and keeping a reader would keep the weaker design reachable.

### 3.2 Buffer discipline

- A secret moves from stored ciphertext to a wipeable buffer, is re-sealed straight from that buffer, and is cleared immediately.
- No plaintext password is ever converted to immutable text during backup or restore.
- The backup builder borrows the content key; the code that opened the container owns and clears it.
- The only text values in the flow are ciphertext and metadata, which need no wiping.

### 3.3 One-way sharing

- The sender picks categories and receives a time-limited pairing code plus a freshly generated session PIN.
- The PIN is displayed on the sender's screen, not encoded in the pairing code.
- The receiver proves the PIN, fetches the container, merges locally, and never sends data back.
- The payload contains only the selected categories and only the authenticator records linked to entries inside them.
- The one-way guarantee is enforced by the sender: the write path is refused for the entire share session, so a receiver that ignores the routing hint still cannot write into the sender's vault.
- Delivery is one-shot: the first successful fetch serves the payload and stops advertising. Serving repeatedly for the whole window would keep a decryptable payload reachable.
- Repeated wrong PIN attempts close the window; the sender's countdown ends and a new code is required.
- The device lock PIN is never used or compared.

### 3.4 Authenticated transfer session

Both transfer modes use the same session establishment.

**Roles:** the host advertises a pairing code; the scanning device reads it. Both transfer modes use the same session establishment.

**Flow, at design level:** the host offers an ephemeral post-quantum public key. The scanning device proves knowledge of the pairing token and of the session PIN in one message exchange, then encapsulates a shared secret to the host. The host validates the request before it decapsulates, and each direction of the session derives its own key. Every later request and response body is sealed under its direction key.

**Security properties:**

- The token is high-entropy random data. It is never transmitted, and it authenticates the pairing instead of encrypting with a value that could be guessed offline.
- The PIN is low-entropy and never contributes to the session keys. The session therefore keeps the full strength of the key exchange, and there is nothing for an offline attacker to test.
- The key exchange material is ephemeral and used once; a replay is refused.
- A session is short-lived and torn down with its keys.
- Every rejection looks the same to the peer, so an attacker cannot tell a wrong token from a wrong PIN, and a stranger cannot make the receiving device display a dialog.
- The receiving device refuses a session unless its own lock credential is configured.

**No downgrade:** the pairing code carries an explicit protocol version. A peer that does not advertise it is refused before dialling, and the sender refuses the retired endpoint. There is deliberately no fallback.

### 3.5 User interface

- Transfer offers two modes, sync and share, behind the paid gate.
- Both show the generated session PIN under the pairing code.
- A pairing code stops being advertised once the session is established, when the user leaves the
  page, or when the mode is switched.
- Share requires at least one selected category and shows a countdown while advertising.
- The result reports what the transfer carried, never the size of the local vault.
- A sync scan action also accepts a share code and takes the receive-only path.

---

## 4. Decisions and rejected alternatives

| Decision | Why |
|----------|-----|
| One container for file backup and transfer | One implementation instead of two; one format to audit |
| Memory-hard KDF over a user passphrase for files | A numeric secret cannot carry the entropy an offline-resistant file needs |
| Token plus session PIN for transfer | No user-typed passphrase; the token carries the entropy |
| Random per-backup content key | Keeps per-record ciphertext form and unwraps once |
| ML-KEM-768 | Post-quantum, and available in every target platform library |
| PIN proven during pairing, never used as key material | A low-entropy PIN must not weaken the session |
| Per-session PIN shown on the sending device | Replaces the reusable device lock PIN; authorisation becomes "can see the sending screen" |
| One-shot pairing and one-shot delivery | Limits the exposure window of a photographed code |
| Write path refused for the whole share session | Enforces one-way at the sender, not by receiver behaviour |
| No downgrade path | A weaker fallback would let an attacker force the retired exchange |
| Retired container formats refused | They did not meet the confidentiality bar; a reader would keep that path alive |

Rejected: deriving the container key from the transfer session keys. It would remove the KDF cost but needs its own container design.

---

## 5. Components

| Responsibility | Role |
|----------------|------|
| Container service | Seal, open, validate declared parameters, authenticate the header |
| Payload builder | Re-seal record secrets from the vault key to the content key and back |
| Passphrase dialogs | Backup and restore entry, with confirmation on export |
| Transfer service | Advertising, session lifetime, one-way enforcement |
| Session layer | Ephemeral key exchange, pairing proof, per-direction sealing |
| Merge service | Open the container, re-encrypt into the local vault, report a summary |
| Transfer UI | Sync and share segments, scanning, progress and result states |

---

## 6. Security properties

**Container**

- [x] A container sealed on one device opens on another with the same passphrase, and only with the right passphrase.
- [x] The header carries no payload metadata: category names and titles appear nowhere outside the ciphertext.
- [x] Record secrets inside the document remain ciphertext, not plaintext.
- [x] Any modification to the ciphertext or the header is detected and rejected.
- [x] Declared cost parameters are bounds-checked before any expensive work starts, so a crafted file cannot exhaust memory.
- [x] Retired formats and malformed input are refused rather than half-read.

**Restore and transfer**

- [x] A transfer payload opens only with both the pairing token and the session PIN.
- [x] A wrong token and a wrong PIN produce the same observable failure.
- [x] Category names, titles, and secrets do not appear in any request or response body.
- [x] Restored secrets are re-encrypted under the destination device's key.
- [x] A peer that does not advertise the current protocol version is refused before connecting.
- [x] The retired endpoint is refused.

**Sharing**

- [x] The session PIN is generated per share and the device lock PIN is not accepted.
- [x] Repeated wrong PINs close the window.
- [x] A receiver cannot write into the sender's vault, even if it ignores the one-way signal.
- [x] The payload holds exactly the selected categories and the authenticator records linked to them.
- [x] Delivery is one-shot; the payload is not offered again after a successful fetch.

---

## 7. Risks and residual gaps

| Risk | Status |
|------|--------|
| A host on the same network can occupy a pairing window with bogus requests | Accepted availability nuisance; no confidentiality impact |
| Passphrase entropy is the real limit for file backups | Only a minimum length is enforced; there is no strength meter |
| No recovery for a lost backup passphrase | By design; stated in the dialog |
| Plaintext exists briefly in memory during backup | Unavoidable with per-record encryption; one record at a time, buffer wiped |
| One container means one blast radius | Accepted; tamper and round-trip properties above are the guard |
| Memory-hard KDF cost on older phones | Parameters travel with the container and were sized for older mid-range hardware |
| Sharing and sync share one session design | Accepted; a defect affects both, which is why the properties above cover both |

---

## 8. Provenance

Derived from the shipped behaviour of the 2.3.0 release and the public release history. Wire layouts, field names, endpoint paths, associated-data strings, status codes, and source locations are withheld under the disclosure model in the [index](../README.md).
