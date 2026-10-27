# Security policy

How to report a vulnerability in Zafonyx Local, what is in scope, and what happens after you
report it.

| | |
|---|---|
| **Document status** | Public |
| **Applies to** | Releases 2.0 through 2.3.0 |
| **Alternative** | If the private channel is unavailable, open a minimal issue asking for a private contact, containing no technical detail |

---

## Reporting a vulnerability

Report privately through **GitHub Private Vulnerability Reporting** on this repository:

<https://github.com/zafonyx/zafonxy-local/security/advisories/new>

That channel is visible only to you and the maintainers. Do not open a public issue, a public
pull request, or a social-media post describing a suspected vulnerability.

### What to include

- The platform and the app version where you observed the issue.
- A description of the affected security property, not a full exploit chain.
- Reproduction steps sufficient for us to confirm the behaviour.
- Whether you have shared the finding with anyone else.

### What not to include

- Real vault contents, passwords, one-time-code seeds, private keys, or recovery words.
- Your own device credentials or a copy of your vault.
- Personal data belonging to anyone other than yourself.

Reproduce against a vault you created for testing. If a proof of concept needs a secret, use a
throwaway value.

---

## Scope

**In scope**

- Cryptographic design: vault key custody, per-secret encryption, key derivation, the sealed
  backup container.
- Local data at rest: the vault store, the wrap record, and anything left on disk after lock,
  reset, or uninstall.
- Backup, restore, one-way sharing, and LAN transfer, including protocol downgrade and replay.
- Secret handling in the running app: buffers, clipboard, logs, crash reports, screen capture.
- The platform authenticator path, once passkey support is released.
- Anything that lets a process running as the same user obtain vault contents without user
  presence, on a platform where the hardware-backed tier is claimed.

**Out of scope**

- A compromised operating system, a rooted or jailbroken device with the app running, or code
  injected into the app during a cryptographic operation. This is a stated residual risk, not a
  defect — see [the threat model](docs/threat-model.md).
- Physical attacks against an unlocked device or a device whose credential is known.
- Availability nuisance on a LAN while a pairing window is open, without a confidentiality
  impact. This is an accepted risk — see [open questions](docs/open-questions.md).
- Vulnerabilities in third-party libraries or platform SDKs. Report those upstream; tell us only
  if the way we use the library creates a separate impact.
- Missing features, including the absence of cloud sync, account recovery, or server-side
  licence enforcement. These are deliberate.
- Findings that require modifying the app bundle, re-signing it, or disabling OS protections.

---

## Safe harbour

We will not pursue legal action, and we will not report you to a platform, for security research
that:

- stays within the scope above,
- uses accounts, devices, and vaults you own or are authorised to test,
- avoids privacy violations, data destruction, and service degradation,
- gives us reasonable time to fix the issue before public disclosure, and
- does not exfiltrate data beyond the minimum needed to demonstrate the finding.

If you are unsure whether your research falls inside this statement, ask first through the
private channel.

---

## What to expect

Targets, not contractual commitments:

| Stage | Target |
|-------|--------|
| Acknowledge the report | 5 business days |
| Initial assessment and severity | 10 business days |
| Fix or mitigation plan for a confirmed issue | 30 days for high severity |
| Coordinated public disclosure | By agreement, normally 90 days after the report |

We will tell you if a target will be missed, and why. We will credit you in the advisory unless
you ask us not to.

Advisories are published through GitHub Security Advisories on this repository, with a CVE
requested where the finding warrants one.

## No bug bounty

There is no paid bounty programme at this time. We do not want to imply one exists. Reports are
still wanted, are read by the maintainers, and are credited.

---

## Supported versions

| Release line | Status | Security fixes |
|--------------|--------|----------------|
| 2.3.x | Current | Yes |
| 2.2.x | Superseded | Critical fixes only, at our discretion |
| 2.0 – 2.1 | End of life | No |

Update through the platform store. A key-custody change rewrites the wrap record and never the
vault contents, so upgrading does not re-encrypt or risk existing entries — see
[M2](docs/milestones/m2-hardware-root-of-trust.md#36-upgrade-path).
