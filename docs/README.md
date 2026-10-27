# Zafonyx Local — documentation set

Public technical documentation for **Zafonyx Local**, a local-first password manager and secret
store. It describes the security architecture the product has reached, the guarantees it aims to
provide, and the milestones that remain.

| | |
|---|---|
| **Document status** | Public |
| **Covers** | Releases 2.0 through 2.3.0 (shipped) and 2.4.0 through 2.6.0 (planned) |
| **Audience** | Users, security reviewers, integrators, prospective customers |
| **Not** | An implementation guide, an audit report, or a substitute for your own threat assessment |

New to the set? Start at the [repository front page](../README.md) for the 30-minute evaluation
path, or with [00-overview](milestones/00-overview.md) for the whole architecture in one page.

---

## The document set

| Document | What it covers |
|----------|----------------|
| [cryptography](cryptography.md) | Primitives, key hierarchy, custody tiers, parameter policy, what is not claimed |
| [threat-model](threat-model.md) | Assets, adversaries, trust boundaries, STRIDE summary, residual risk |
| [data-protection](data-protection.md) | Data inventory, egress paths, third parties, retention, deletion |
| [assurance](assurance.md) | What is verified, how, what is not certified, evidence under NDA |
| [enterprise-faq](enterprise-faq.md) | Procurement-shaped answers, the not-applicable list, the NDA boundary |
| [glossary](glossary.md) | Every term used here, defined once |
| [open-questions](open-questions.md) | Open scope decisions, known limitations, how to read a claim |
| [milestones/00-overview](milestones/00-overview.md) | Architecture, dependencies, cross-cutting invariants |
| [milestones/](milestones/) m0–m7 | One document per milestone |

Three of these are the top-level answers a commercial reviewer usually needs first:
**cryptography** (is the design sound), **data-protection** (what leaves the device), and
**assurance** (who checked, and what happens when someone reports a flaw).

---

## Disclosure model

These documents follow the disclosure level commercial security products normally use for public
material: enough for a reader, a reviewer, or a prospective customer to judge the design, and not
enough to write the software or to aim an attack at a specific build.

**Published**

- Product goals, and the security property each milestone establishes.
- Threat model, chosen design, and rejected alternatives.
- Cryptographic primitives and parameters that affect user-facing guarantees.
- Which hardware or OS capability class a platform relies on, at capability level.
- Guarantees that can be checked from outside the implementation.
- Known limitations and residual risk.
- Release timeline and milestone dependencies.

**Withheld**

- Per-platform implementation detail: API choices, call sequences, module and class structure, and native bridges.
- Repository layout, file paths, function names, and test paths.
- Database schemas, table and column definitions, and index design.
- Persisted storage key names, OS key-store item names, and configuration keys.
- Wire formats: field names, byte layouts, associated-data strings, endpoint paths, and status codes.
- Bundle identifiers, store product identifiers, signing configuration, and environment endpoints.
- Exact tuning values for cost parameters, timeouts, retry budgets, and size limits.
- Any credential, secret, or per-device value.

**The line between the two**

- **Standard constants are published exactly.** A default one-time-code period, a cipher key
  size, a tag length — these are fixed by a published standard and hiding them would only obscure
  something already in the public domain.
- **Product tuning values are published as ranges or as qualitative statements.** "A bounded
  number of failures triggers a cooldown" is published; the number is not. A reader can judge the
  behaviour without gaining a precise budget to attack.
- **Capability, not configuration.** "Relies on a device security chip, released after a gesture"
  is published; the API, the item name, and the call sequence are not.
- **The test for any sentence**: does it describe *what is guaranteed*, or *how it is built*? Would
  it help a reader target a specific build? Does it name an internal artefact, document, or
  person? A sentence that fails any of these is rewritten or cut.

**On request**

Deeper implementation material is not published. Where an engagement genuinely needs it, it is
shared only under a written agreement, and never in a public repository — see
[assurance §6](assurance.md#6-evidence-under-nda).

**Security reports**

If you believe you have found a vulnerability, report it privately through the channel in
[SECURITY.md](../SECURITY.md). Do not open a public issue. Include the affected platform and
version, and never include real vault contents.

---

## Milestones

| # | Milestone | Release | Status | Theme |
|---|-----------|---------|--------|-------|
| M0 | [Foundation and product shell](milestones/m0-foundation.md) | 2.0 – 2.1 | Shipped | Cross-platform app, local vault, one-time store unlock |
| M1 | [Secret-safe vault](milestones/m1-secret-safe-vault.md) | 2.2.0 – 2.2.7 | Shipped | Authenticator codes, wipeable secrets, clipboard hygiene |
| M2 | [Hardware root of trust](milestones/m2-hardware-root-of-trust.md) | 2.2.7 | Shipped on four platforms | Presence-gated, hardware-wrapped vault key |
| M3 | [Encrypted data store](milestones/m3-encrypted-data-store.md) | 2.2.8 | Shipped | Encrypted relational store with verified migration |
| M4 | [Zero-trust transfer](milestones/m4-zero-trust-transfer.md) | 2.3.0 | Shipped | Sealed backup container, one-way sharing, post-quantum pairing |
| M5 | [Wallet: bank cards](milestones/m5-wallet-bank-cards.md) | 2.4.0 | Planned | Account / Wallet / Securities split, card records |
| M6 | [Wallet: cryptocurrency](milestones/m6-crypto-wallet.md) | 2.5.0 | Planned | Storage-only crypto backup records |
| M7 | [Passkeys](milestones/m7-passkeys.md) | 2.6.0 | Planned | Passkey storage and platform authenticator |

Read [open-questions.md](open-questions.md) for open scope decisions and the limits of each claim.

## Status legend

| Status | Meaning |
|--------|---------|
| Shipped | Available in a released build |
| In progress | Partly available; not complete on every supported platform |
| Planned | Design exists, implementation has not started |

## Ground rules

1. **Security properties are invariants, not features.** The rules in
   [00-overview](milestones/00-overview.md#3-cross-cutting-invariants) apply to every milestone.
   Weakening one needs an explicit decision record.
2. **Secrets are bytes, not text.** A decrypted secret is never held as an immutable string type;
   it lives in a wipeable buffer that has exactly one owner.
3. **No silent downgrade.** Version and protocol gates refuse an old peer instead of falling back
   to a weaker path.
4. **Metadata is data.** Category names, entry titles, and notes are as confidential as the
   secrets beside them.
5. **One record type per store.** Accounts, authenticator items, cards, crypto backups, and
   passkeys do not share a list or a schema.
6. **Claims are scoped.** A guarantee here covers resting data and network transport. It does not
   claim to survive a compromised operating system or a live injected process.

## Conventions

- "Vault key" means the 32-byte symmetric key that protects the vault contents.
- "Sealed" means authenticated encryption under a key that only the intended party can derive.
- "Hardware-sealed" means the vault key is wrapped by a key that cannot be exported from a
  security chip or OS keystore, and releasing it requires user presence.
- Release numbers refer to the public app versions.
- Claim identifiers (`CRY-nn`, `THR-nn`, `DAT-nn`, `ASR-nn`) are defined once and are citable.
  CI verifies that none dangles.
