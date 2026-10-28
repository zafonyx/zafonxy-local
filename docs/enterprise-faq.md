# Enterprise FAQ

Procurement-shaped answers for a commercial buyer. Each answer is short and points at the
document that carries the detail, so a questionnaire can be filled without a sales call and
without an NDA.

| | |
|---|---|
| **Document status** | Public |
| **Applies to** | 2.0 through 2.3.0 (shipped); planned items marked |
| **Use with** | [cryptography](cryptography.md), [threat model](threat-model.md), [data protection](data-protection.md), [assurance](assurance.md) |

---

## 1. Start here: what kind of product this is

Most vendor questionnaires assume a service. This one is a local application, which makes a large
block of standard questions inapplicable rather than answered.

| Question | Answer |
|----------|--------|
| Where is customer data hosted? | On the customer's own device. We operate no service that stores it — `DAT-01` |
| Which regions process customer data? | None. There is no server-side processing to locate |
| Who are the sub-processors? | None for vault content. Platform stores handle purchases; an optional crash reporter receives crash data only — `DAT-08` |
| What is the data-retention period? | Whatever the customer keeps locally. No server-side copy exists — `DAT-09` |
| Can you access our vault? | No. The vault key never leaves the device — `CRY-01` |
| Can you produce data under a legal request? | We hold no vault data to produce. This is stated as a structural fact, not a policy promise — `DAT-01` |
| What is the RTO/RPO for a service outage? | Not applicable: no service. Availability is bounded by the device and the platform store |

**If a questionnaire row cannot be answered "not applicable", say so in writing rather than
guessing.** A wrong answer on a vendor form is worse than a gap.

---

## 2. Deployment and platforms

| Question | Answer |
|----------|--------|
| What platforms? | Windows, macOS, iOS, and Android, from one shared interface. Linux is planned; web is not supported |
| Is there an agent, a browser extension, or a background service? | No. The app is the client; there is no server component and no required extension |
| How is it deployed in an enterprise? | Per-device installation through the platform's normal app distribution. There is no MDM-specific build; standard platform management applies |
| Does it require an account? | No. Guest use is a first-class path — `DAT-07` |
| Does it work offline? | Fully, including the paid unlock once the store has verified entitlement |
| Is there an admin console? | No, and none is planned. There is no central place where vault data or user lists exist |
| How are updates delivered? | Through the platform stores, which sign them — `ASR-05` |
| Can we pin a version? | Per your platform's app-management capability; a superseded line gets critical fixes only |

---

## 3. Cryptography

| Question | Answer |
|----------|--------|
| What protects secrets at rest? | AES-256-GCM, per secret, fresh nonce each time — `CRY-04` |
| Where does the vault key live? | Never at rest unwrapped; wrapped by a non-exportable key in the device security chip or OS keystore — `CRY-01`, `CRY-13` |
| Is the key released without user action? | No, on chip-backed tiers. Presence is required once per app start — `CRY-13` |
| Is it post-quantum? | The transfer handshake uses ML-KEM-768, ephemeral per session — `CRY-06`. The symmetric vault cipher is unaffected by that class of attack |
| What KDF protects a backup file? | Argon2id, memory-hard, parameters carried in the container and bounds-checked before use — `CRY-05` |
| Is it FIPS-validated? | No. Named standards are followed; no validation is claimed — [assurance §3](assurance.md#3-what-is-not-verified) |
| Can you re-key our vault? | No. The vault key is long-lived by design and no escrow exists — `CRY-02` |
| What happens if we drop a device in a lake? | The data is gone. There is no recovery path, by design |

---

## 4. Access control and authentication

| Question | Answer |
|----------|--------|
| How do users authenticate to the vault? | OS biometric, device credential, or an application PIN, depending on the tier the device supports |
| Is SSO or SAML available? | No. There is no server to federate with, and no central identity to assert |
| Is MFA available? | The vault has no password-based remote login to protect. The presence gate is the control; time-based codes exist for the user's own accounts, not for our product |
| How is privilege separation handled? | The app runs as the user; separation is between the user and the security chip boundary, not between app roles — [threat model §2](threat-model.md#2-trust-boundaries) |
| What happens after repeated failed PIN attempts? | A bounded number of failures triggers a cooldown, and a chip-backed tier also hits the hardware retry limit. Exact thresholds are withheld — see the [disclosure model](README.md#disclosure-model) |

---

## 5. Data protection and privacy

| Question | Answer |
|----------|--------|
| What personal data do you collect? | None through the product. No telemetry, no analytics, no advertising identifiers — `DAT-03` |
| Is there telemetry we must disable? | There is none to disable. Crash reporting is opt-in and excludes vault data — `DAT-04` |
| How is data encrypted in transit? | Transfer payloads are sealed under an authenticated post-quantum session — `CRY-07` |
| How is data encrypted at rest? | Per-secret authenticated encryption, plus an encrypted relational store — `CRY-04`, `CRY-11` |
| Do you support data residency requirements? | There is no server-side data to place in a region |
| How do we delete our data? | Locally: delete records, run the explicit reset, or remove app data. An uninstall may leave app data on some platforms, so reset first — `DAT-09` |
| Are you GDPR compliant? | We do not make compliance claims in public. The architecture minimises personal data to near zero; assess that against your own regime — [data protection §7](data-protection.md#7-compliance-posture-stated-plainly) |

---

## 6. Vulnerability management and assurance

| Question | Answer |
|----------|--------|
| Do you have a disclosure policy? | Yes — [SECURITY.md](../SECURITY.md), aligned with ISO/IEC 29147 and ISO/IEC 30111 |
| How fast do you acknowledge a report? | Target 5 business days; assessment 10; high-severity fix 30. Targets, not commitments — [assurance §5](assurance.md#5-vulnerability-handling) |
| Are you audited? | Not yet. No SOC 2, no ISO/IEC 27001, no penetration-test report — `ASR-04` |
| Do you have a bug bounty? | No, and none is implied |
| Can we see your SBOM? | Not published yet; available on request, publication planned — [assurance §3](assurance.md#3-what-is-not-verified) |
| Do you run a secure development lifecycle? | Development follows NIST SP 800-218 vocabulary; no certification is claimed and no exception process is published |
| What happens when a finding contradicts a published claim? | The documentation is corrected along with the code — `ASR-08` |

---

## 7. What we will and will not answer publicly

**Will answer publicly, in these documents**: primitives and parameters at class level, key
custody tiers, threat coverage, egress paths, third parties, residual risk, release status.

**Will answer under a written agreement** — see
[assurance §6](assurance.md#6-evidence-under-nda): per-platform custody detail, test evidence,
schemas and wire formats for an integrator, architecture walkthrough, current known-issue list.

**Will not answer at all**: anything that would let a reader target a specific build, and any
statement of compliance we have not been assessed against.

---

## 8. Commercial and lifecycle

| Question | Answer |
|----------|--------|
| Licensing model | One-time purchase per platform store, restored across reinstalls. No subscription, no licence server |
| Is the licence enforced server-side? | No server exists. Entitlement is verified with the platform store |
| What is the support channel? | The public issue tracker of this repository for documentation questions; the private channel in [SECURITY.md](../SECURITY.md) for vulnerabilities |
| What is the roadmap? | 2.4.0 wallet bank cards, 2.5.0 cryptocurrency backup records, 2.6.0 passkeys. All are design, not shipped — see [milestones](milestones/00-overview.md) |
| What happens if the vendor disappears? | The vault is local and the format is documented at design level; backup containers are self-contained. Long-term readability depends on platform store availability and on the ciphertext format remaining stable — `CRY-02` |

---

## 9. Provenance

Answers consolidate [cryptography](cryptography.md), [threat model](threat-model.md),
[data protection](data-protection.md), [assurance](assurance.md), and the milestone documents.
No sales material, contract, or internal questionnaire response is reproduced.
