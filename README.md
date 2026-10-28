# Zafonyx Local — Public Security Documentation

[Zafonyx Local](https://www.zafonyx.com) is a local-first password manager and secret store for
Windows, macOS, iOS, and Android. This repository is its public security documentation: what the product protects, how it
is designed to protect it, and what it does not claim.

| | |
|---|---|
| **Document status** | Public |
| **Applies to** | Releases 2.0 through 2.3.0 (shipped) and 2.4.0 through 2.6.0 (planned) |
| **Audience** | Security reviewers, procurement teams, integrators, users |
| **Licence** | [CC BY-ND 4.0](LICENSE) |

---

## Evaluate this product in 30 minutes

You do not need an NDA, a sales call, or a questionnaire to reach a first-pass opinion. Read in
this order and stop wherever your review standard is satisfied.

| Time | Read | The question it answers |
|------|------|-------------------------|
| 5 min | This page | What is it, and what is it honestly not? |
| 10 min | [Cryptography](docs/cryptography.md) | Which primitives, which keys, where they rest, what is unproven |
| 5 min | [Threat model](docs/threat-model.md) | Who we defend against, and who we explicitly do not |
| 5 min | [Data protection](docs/data-protection.md) | What can leave the device (very little) and under whose control |
| 5 min | [Assurance](docs/assurance.md) and [open questions](docs/open-questions.md) | What is verified, what is merely designed, what is unproven |

Then use the [enterprise FAQ](docs/enterprise-faq.md) to map the above onto a procurement
questionnaire, and [SECURITY.md](SECURITY.md) if you are reporting a vulnerability.

---

## What the product is

- **Local-first.** The vault and its key stay on the device. There is no server that holds
  either, no cloud sync, and no account required to use the vault.
- **Four platforms** from one shared user interface: Windows, macOS, iOS, and Android. Linux is
  planned; web is not supported and is not planned for the near term.
- **One-time purchase** through the platform stores. There is no subscription and no licence
  server.
- **Shipped** through 2.3.0: hardware-wrapped vault key released only after user presence,
  encrypted relational store with verified migration, sealed backup container, authenticated
  post-quantum transfer, built-in authenticator.
- **Planned**: bank cards in a Wallet section (2.4.0), cryptocurrency backup records (2.5.0),
  passkeys as a platform authenticator (2.6.0). Planned material is design, not shipped
  behaviour, and is labelled as such everywhere it appears.

---

## Document map

| Document | Answers | Read it if you are |
|----------|---------|--------------------|
| [docs/cryptography.md](docs/cryptography.md) | Primitives, parameters, key hierarchy, custody tiers, claim identifiers | A cryptographer or a security architect |
| [docs/threat-model.md](docs/threat-model.md) | Assets, adversaries, trust boundaries, residual risk | Doing a risk assessment or a design review |
| [docs/data-protection.md](docs/data-protection.md) | Data inventory, egress paths, third parties, retention | A privacy officer, DPO, or legal reviewer |
| [docs/assurance.md](docs/assurance.md) | What is verified, how, and what is not certified | Auditing our claims rather than reading them |
| [docs/enterprise-faq.md](docs/enterprise-faq.md) | Procurement-shaped answers, N/A list, NDA boundary | Filling in a vendor questionnaire |
| [docs/glossary.md](docs/glossary.md) | Every term used across these documents | New to the product or to the domain |
| [docs/milestones/00-overview.md](docs/milestones/00-overview.md) | Architecture, dependencies, cross-cutting invariants | Wanting the whole system in one page |
| [docs/milestones/](docs/milestones/) m0–m7 | One document per milestone: goal, problem, design, rejected alternatives, properties, risks | Reviewing a specific guarantee |
| [docs/open-questions.md](docs/open-questions.md) | Open scope decisions, known limitations, how to read a claim | Deciding how far each claim reaches |
| [SECURITY.md](SECURITY.md) | How to report a vulnerability | A researcher, or triaging a finding |
| [docs/README.md](docs/README.md) | The disclosure model: what we publish, what we withhold, and why | Checking whether we are consistent |

---

## What we publish, and what we withhold

These documents are written at the level commercial security products normally publish: enough
for a reader to judge the design and decide whether to trust it, and not enough to reimplement
the product or aim an attack at a specific build.

**Published**: product goals, the security property each milestone establishes, threat model,
design choices and rejected alternatives, cryptographic primitives and the parameter classes
that affect user-facing guarantees, the capability tier a platform relies on, guarantees that
can be checked from outside the implementation, known limitations, and the release timeline.

**Withheld**: per-platform implementation detail, repository layout, function and module names,
schema and wire formats, package and store identifiers, exact tuning thresholds and cost
parameters, and any credential or per-device value.

The full model, including what is available under a written agreement, is in
[docs/README.md](docs/README.md). Product tuning values are published as ranges or as
qualitative statements. Constants fixed by a published standard — a default one-time-code
period, a cipher key size — are published exactly, because withholding them would only obscure
a standard already in the public domain.

---

## What we do not claim

Reviewers should discount any reading stronger than this list:

- **No third-party security audit or certification yet.** No SOC 2, ISO/IEC 27001, FIPS 140-3,
  or Common Criteria validation is held or implied. [Assurance](docs/assurance.md) states what
  is and is not verified.
- **No protection against a compromised operating system**, nor against code injected into the
  running process during a cryptographic operation. Hardware wrapping hardens offline copies
  and resting memory; it is not a runtime sandbox.
- **No cloud, no sync, no recovery.** There is no server-side vault, no key escrow, and no way
  to recover a forgotten backup passphrase. This is a design property, not a missing feature.
- **No server-enforced licence.** There is no server, so entitlement is verified with the
  platform store rather than against a licensing service.
- **Planned milestones are designs.** M5–M7 describe intended scope; they are not shipped
  behaviour and carry no guarantee until released.

---

## Repository layout

```
README.md              this page
LICENSE                CC BY-ND 4.0
SECURITY.md            vulnerability disclosure policy
Makefile               single entry point for the documentation check
docs/                  the document set, starting at docs/README.md
docs/milestones/       one document per milestone, m0 through m7
tools/docs_check.py    disclosure and consistency gate
tools/hooks/           commit-msg hook rejecting an automated co-author trailer
.github/workflows/     runs the gate on every push and pull request
```

The gate runs in CI on every push and pull request, so a document that leaves the disclosure
model — or two documents that disagree — fail the build rather than being caught by review. It
also scans the commit history and rejects a co-author trailer from the tooling that writes
commits, so an agent is never credited as a contributor to this repository. Locally, `make check`
runs the same thing. `make self-test` proves the rules still fire.

The same trailer is rejected before a commit exists by the `commit-msg` hook. Enable it once per
clone:

```bash
git config core.hooksPath tools/hooks
```

A message that carries the trailer is refused outright, so it cannot reach the history and need
not be rewritten afterwards.

## Reporting a vulnerability

Do not open a public issue. See [SECURITY.md](SECURITY.md) for the private channel, scope, and
what to include. Never send real vault contents, passwords, seeds, or private keys.

## Licence

These documents are licensed under [CC BY-ND 4.0](LICENSE): you may redistribute them
unmodified, with attribution. The product itself is proprietary.
