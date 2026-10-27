# Data protection

What Zafonyx Local stores, where it stores it, what can leave the device, and which third
parties are involved. Written for a privacy officer or legal reviewer assessing a local-first
product, not a cloud service.

| | |
|---|---|
| **Document status** | Public |
| **Applies to** | 2.0 through 2.3.0 (shipped); planned items marked |
| **Claim identifiers** | `DAT-nn` |
| **Key point** | There is no service that stores customer data, so most vendor-privacy questions resolve to "not applicable" |

This document describes how the product is designed to handle data. It is not a legal opinion,
and the absence of a certification is stated rather than glossed — see [assurance](assurance.md).

---

## 1. The structural position

**`DAT-01`** The product operates no server that stores vault data, secrets, or account data.
There is no cloud sync, no server-side key, no escrow, and no remote backup. The organisation
that makes Zafonyx Local therefore does not hold, process, or have access to a customer's vault,
and cannot produce it on request — including a request from us to a customer, or from a
customer to us.

Three consequences follow, and they are the answer to a large share of a standard vendor
questionnaire:

1. There is no data processor acting on vault content, because no vault content is transmitted.
2. There is no cross-border transfer of vault data, because there is no transfer.
3. There is no server-side retention period, because there is no server-side copy. Retention is
   whatever the user keeps on their own device.

**`DAT-02`** The organisation is not a controller or processor of the vault contents. The user
holds their own data; the vault key never leaves their device.

---

## 2. Data inventory

| Data | Stored on device | Encrypted | Can leave the device |
|------|------------------|-----------|----------------------|
| Passwords, one-time-code seeds, card secrets, crypto recovery material | Yes | Yes, per record | Only inside a sealed container the user creates or sends |
| Category names, entry titles, notes | Yes | Confidential metadata, not individually encrypted at rest | Only inside a sealed container |
| Vault key | No — memory only after presence | n/a | Never |
| Wrap record | Yes | Contains only the wrapped key | Never |
| Application PIN | No readable copy | Sealed by hardware where available | Never |
| Backup passphrase | No | Never stored | Never |
| Pairing token | Displayed, not stored | n/a | Never transmitted |
| Purchase entitlement | Held by the platform store | n/a | Only to the store that issued it |
| Crash and diagnostic data | Only if the user opts in | Contains no vault data | Yes, to the crash-reporting provider |
| Usage analytics | **None collected** | n/a | n/a |

**`DAT-03`** No telemetry or analytics is collected. There is no product analytics SDK, no
behaviour tracking, and no advertising identifier use.

**`DAT-04`** Crash reporting is optional, off unless the user opts in, and excludes vault
contents, passwords, clipboard contents, PINs, seeds, and metadata. Its payload is limited to
what is needed to reproduce a crash.

---

## 3. Egress paths

Four paths exist, and each is user-initiated or platform-mandated. Nothing else leaves the device.

| Path | Trigger | Content | Protection |
|------|---------|---------|------------|
| Backup file export | User action | Whole sealed container | Sealed under a passphrase-derived key; no metadata in the clear; the user chooses where it goes |
| LAN transfer or one-way share | User action, per session | Selected categories and their secrets | Authenticated post-quantum session; one-shot delivery; one-way enforced by the sender |
| Platform purchase | User action | Store transaction, as for any paid app | Handled entirely by the platform store under its own terms |
| Crash report | Opt-in only | Stack and environment data, no vault data | Provider is the only third party that receives anything |

**`DAT-05`** The device lock PIN is never transmitted, never used as a transfer credential, and
never stored in readable form. Sharing uses a per-session PIN displayed on the sending device.

**`DAT-06`** A backup file is under the user's control the moment it is written. Where it is
stored, who can read it, and how long it is kept are the user's decisions, not ours. A weak
passphrase weakens the container regardless of the KDF.

---

## 4. Third parties

| Party | Role | Data received |
|-------|------|---------------|
| Apple App Store, Google Play, Microsoft Store | Process the one-time purchase and restore | Transaction and entitlement data, as for any paid app |
| Optional crash-reporting provider | Receives crash payloads when the user opts in | Technical crash data, never vault data |
| Optional social sign-in providers (Google, Apple) | Only if the user chooses that sign-in for the profile surface | The fact of a sign-in and the basic profile the provider shares |

**`DAT-07`** Social sign-in is optional and only affects the account and profile surface. The
vault works fully in guest mode, and no vault function depends on a signed-in account. A user who
never signs in sends nothing to an identity provider.

**`DAT-08`** No other third party is involved. There is no analytics vendor, no advertising
network, no data broker, and no sub-processor handling vault content.

---

## 5. Retention and deletion

| Situation | What happens |
|-----------|--------------|
| Normal use | Data stays on the device until the user deletes it |
| Deleting an entry or record | That record is removed from the store |
| Explicit reset | The user is asked to confirm, then the vault and its wrap record are removed |
| Uninstalling the app | Whether app data is also removed depends on the platform; treat it as not guaranteed and reset before uninstalling |
| Crash reports | Retained by the provider under its own policy; we do not receive vault data to retain |
| Server-side data | None exists |

**`DAT-09`** There is no silent wipe and no automatic deletion of a vault. A corrupt or
unopenable vault produces an explanation and an explicit, confirmed reset — never an automatic
one. See [M3 §3.5](milestones/m3-encrypted-data-store.md#35-failure-and-reset).

---

## 6. Rights and requests

Because the organisation holds no customer vault data, the usual subject-access workflow does not
apply to vault contents:

- **Access** — the user already has the data, on their own device.
- **Erasure** — performed locally: delete records, reset the vault, or remove app data.
- **Portability** — the backup container is the export. It is a sealed document, not a plaintext
  dump, by design.
- **Rectification** — the user edits their own records.
- **Objection to processing** — there is no processing of vault content to object to.

**`DAT-10`** A request we cannot fulfil is a request about data we do not hold. Where a request
concerns the limited data we do handle — a purchase record at a platform store, or a crash report
the user opted into — the fastest route is the platform store or the crash-reporting provider's
own request process.

---

## 7. Compliance posture, stated plainly

- **No certification is claimed.** No SOC 2 report, no ISO/IEC 27001 certificate, no FIPS 140-3
  validation. See [assurance](assurance.md).
- **The design is data-minimising by architecture**, not by policy: there is no server to
  misconfigure, no database to breach, and no key to subpoena.
- **A customer's own obligations** — records of processing, transfer impact assessments, vendor
  registers — are usually satisfied by "no data leaves the device except by explicit user
  action", but you should confirm that against your own regime rather than rely on this page.
- **We do not describe the product as compliant with a specific regulation.** Any such statement
  belongs in a signed agreement, not in a public document.

---

## 8. Provenance

Consolidates the data-flow facts published per milestone — notably
[M0 §3.4](milestones/m0-foundation.md#34-feature-set) for the optional account surface,
[M1 §3.3](milestones/m1-secret-safe-vault.md#33-clipboard-hygiene) for clipboard handling,
[M2](milestones/m2-hardware-root-of-trust.md) for the PIN, and
[M4](milestones/m4-zero-trust-transfer.md) for the two egress paths — plus the local-first
invariant in [00-overview §3](milestones/00-overview.md#3-cross-cutting-invariants). No internal
data-flow diagram or vendor contract is reproduced.
