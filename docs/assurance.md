# Assurance

What is verified about Zafonyx Local, how it is verified, and what is not verified at all. This
document exists so a reviewer can separate a tested guarantee from a designed intention — and so
the gaps are on the record rather than discovered in a questionnaire.

| | |
|---|---|
| **Document status** | Public |
| **Applies to** | 2.0 through 2.3.0 (shipped); planned items marked |
| **Claim identifiers** | `ASR-nn` |
| **Read this with** | [open questions](open-questions.md) for the limits of each claim |

---

## 1. What is verified

Each shipped security property is checked by a test that fails if the property breaks. The
properties themselves are listed per milestone; this table says how they are checked.

| Property | Check | Milestone |
|----------|-------|-----------|
| Secrets are ciphertext at rest and decrypt only on reveal | Round-trip and at-rest inspection | M0, M1 |
| A copied app-data folder does not yield the vault key on a hardware-backed platform | Copy-and-open attempt on real devices | M2 |
| Releasing the key requires presence; cancelling leaves the vault locked | Negative test per tier | M2 |
| Correcting a failed wrapping never re-keys or strands a vault | Fault injection during the wrap upgrade | M2 |
| Migration carries every record and deletes the old format only after verification | Full-content comparison, then rollback on injected failure | M3 |
| Duplicate titles and orphaned links are rejected by the store | Attempt from every write path | M3 |
| A container opens only with the right passphrase and rejects any tampering | Round-trip, single-bit corruption of body and header | M4 |
| A transfer requires both the pairing token and the session PIN | Pairwise negative tests: right token/wrong PIN, wrong token/right PIN | M4 |
| A wrong token and a wrong PIN fail identically | Observable-behaviour comparison | M4 |
| An old protocol version is refused before connecting | Version downgrade attempt | M4 |
| A receiver cannot write into the sender's vault | Write attempt during a share session | M4 |
| Imported one-time codes match their source app | Cross-check against reference generators | M1 |

**`ASR-01`** A security property is treated as shipped only when a test can fail on it. Properties
with no runnable check are described as designed, not as guaranteed.

**`ASR-02`** Key custody is checked on real hardware for every supported tier, including a device
with no security chip, so the degraded path is exercised rather than assumed.

---

## 2. How the checking is done

At the level a reviewer needs, without publishing a test plan that would amount to a map of the
implementation:

- **Round-trip and at-rest inspection** for every encrypted record type.
- **Negative tests** for every gate: wrong credential, cancelled prompt, tampered input,
  downgraded peer, replayed message.
- **Fault injection** at the two points where a failure could lose data: the wrap upgrade and the
  store migration.
- **Device matrix testing** for custody tiers, on hardware and on emulators, including the
  no-chip path.
- **Behavioural comparison** where the guarantee is about indistinguishability — a wrong token
  must look exactly like a wrong PIN to the peer.
- **Real-service testing** for passkey integration once that work starts, rather than a mock
  relying party alone.

**`ASR-03`** Tests cover the failure path, not only the success path. A guarantee that only holds
when nothing goes wrong is not a guarantee.

---

## 3. What is not verified

Stated plainly, because a reviewer will find these out anyway and a surprise costs more trust
than a gap.

| Not done | What it means for you |
|----------|----------------------|
| **No third-party security audit** | No independent firm has reviewed this design or implementation. All assurance here is first-party |
| **No penetration-test report** | None exists to share, publicly or under NDA |
| **No certification** | No SOC 2, ISO/IEC 27001, FIPS 140-3, or Common Criteria. Any certificate you have seen for a similarly named product is not this product |
| **No formal verification** | The design is reviewed and tested, not proven |
| **No bug bounty** | Reports are wanted and credited; none are paid |
| **No published SBOM** | Not produced yet; available on request and planned for publication with a future release |
| **No reproducible-build claim** | Distribution is through platform stores; we do not claim a verifiable build |
| **No runtime sandbox claim** | A live injected process is out of scope; see the [threat model](threat-model.md#5-residual-risk) |

**`ASR-04`** The absence of an audit is disclosed, not implied away. Where a guarantee rests on
first-party testing only, this document says so.

---

## 4. Distribution and updates

**`ASR-05`** Builds are distributed through the platform stores, which sign and deliver updates.
There is no side-loaded update channel and no auto-updater fetching from a vendor endpoint.

**`ASR-06`** An update preserves the vault: the package identity is stable across releases, and a
custody change rewrites the wrap record rather than vault contents, so upgrading neither
re-encrypts entries nor invalidates a purchase.

**`ASR-07`** Supported versions and their fix policy are listed in [SECURITY.md](../SECURITY.md).
A superseded line receives critical fixes only, at our discretion; end-of-life lines receive none.

---

## 5. Vulnerability handling

Summarised from [SECURITY.md](../SECURITY.md), which is authoritative:

- Private reporting through GitHub Private Vulnerability Reporting on this repository.
- Targets: acknowledge within 5 business days, assess within 10, high-severity fix within 30,
  coordinated disclosure normally 90 days after the report. Targets, not contractual commitments.
- Advisories published as GitHub Security Advisories, with a CVE requested where warranted.
- Safe harbour for good-faith research within scope.

**`ASR-08`** A reported vulnerability that contradicts a published claim is treated as a defect in
the documentation as well as in the code, and both are corrected.

---

## 6. Evidence under NDA

Where an engagement genuinely needs more than this repository contains — per-platform detail,
schemas, wire layouts, test evidence — it is shared under a written agreement and never in a
public repository. What that covers and what it does not:

**Available under a written agreement**

- Platform-by-platform custody implementation detail and the tier each device class receives.
- Test evidence for the properties in §1, and the device matrix used.
- Schema and wire-format documentation, for an integrator that must interoperate.
- Architecture walkthrough with the maintainers.
- Current known-issue list and remediation status.

**Not available under any agreement**

- The vault key, a customer's data, or any per-device value.
- Audit opinions that do not exist. An NDA does not create evidence.
- A statement of compliance we have not been assessed against.

**`ASR-09`** Nothing withheld is withheld to protect the product's reputation. It is withheld to
avoid publishing an attack map. Anything material to a trust decision is already in this
repository.

---

## 7. Traceability

Claims carry identifiers so a reviewer can cite them, and so this repository can check itself:

| Prefix | Document |
|--------|----------|
| `CRY-nn` | [cryptography](cryptography.md) |
| `THR-nn` | [threat model](threat-model.md) |
| `DAT-nn` | [data protection](data-protection.md) |
| `ASR-nn` | this document |

**`ASR-10`** Every identifier is defined exactly once and every reference to one resolves. The
check is automated and runs in CI on every push and pull request: it fails on a dangling or
duplicated identifier, a broken link or anchor, an inconsistent release table, a document that
leaves the disclosure model, a shrunken document set that would otherwise make the check pass
vacuously, or a commit that credits an automated tool as a co-author.

---

## 8. Provenance

Built from the property lists and risk sections of
[M0](milestones/m0-foundation.md#7-security-properties) through
[M4](milestones/m4-zero-trust-transfer.md#6-security-properties), the compatibility rules in
[open questions §3](open-questions.md#3-compatibility-and-upgrade-rules), and
[SECURITY.md](../SECURITY.md). No internal test plan, defect tracker, or engagement record is
reproduced.
