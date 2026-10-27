#!/usr/bin/env python3
"""Disclosure and consistency gate for the Zafonyx Local public documentation.

Checks that every Markdown document stays inside the disclosure model in docs/README.md
and that cross-references, claim identifiers, links, and status labels agree.

Usage:
    python3 tools/docs_check.py            # check the repository
    python3 tools/docs_check.py --self-test  # prove the rules fire on a known-bad document
"""

from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", "node_modules", ".cache", "tmp"}

# Documents that must declare their audience and status.
STATUS_REQUIRED = {"README.md", "SECURITY.md"}

# (name, pattern, remedy)
RULES: list[tuple[str, re.Pattern[str], str]] = [
    (
        "personal-email",
        re.compile(r"[\w.+-]+@[\w-]+\.[\w.]{2,}"),
        "publish no address; point at the private reporting channel instead",
    ),
    (
        "absolute-path",
        re.compile(r"(/Users/|/home/|/var/|[A-Za-z]:\\\\)"),
        "describe the location, never the path on a builder's machine",
    ),
    (
        "source-layout",
        re.compile(r"\b(lib|src|test)/"),
        "withhold repository layout",
    ),
    (
        "source-file",
        re.compile(r"\.(dart|kt|swift|gradle|plist)\b"),
        "withhold implementation file types",
    ),
    (
        "package-id",
        re.compile(r"\bcom\.[a-z0-9]+\.[a-z0-9]+\b"),
        "withhold bundle and store identifiers",
    ),
    (
        "store-vendor-detail",
        re.compile(
            r"(\bTestFlight\b|\bAPK\b|universal binary"
            r"|\bapplicationId\b|\bbundleId\b|PRODUCT_BUNDLE_IDENTIFIER)",
            re.IGNORECASE,
        ),
        "withhold distribution and signing detail",
    ),
    (
        "tuning-threshold",
        re.compile(
            r"(6[–-]8 digits|five consecutive failures|\b30 seconds\b"
            r"|five wrong pin|5 wrong pin|three or four digits)",
            re.IGNORECASE,
        ),
        "publish the behaviour, not the exact threshold",
    ),
    (
        "secret-material",
        re.compile(r"(-----BEGIN|AKIA[0-9A-Z]{16}|\bghp_[A-Za-z0-9]{10,}|\beyJ[A-Za-z0-9_-]{10,})"),
        "never publish key material or a token",
    ),
    (
        "personal-account",
        re.compile(r"(gmail\.com|outlook\.com|icloud\.com)", re.IGNORECASE),
        "no personal account in public material",
    ),
    (
        "unfinished-marker",
        re.compile(r"\b(TODO|FIXME|TBD|XXX)\b"),
        "resolve the marker before publishing",
    ),
]

LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)\)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
CLAIM_DEF_RE = re.compile(r"\*\*`((?:CRY|THR|DAT|ASR)-\d{2})`\*\*")
CLAIM_REF_RE = re.compile(r"`((?:CRY|THR|DAT|ASR)-\d{2})`")
STATUS_WORDS = ("Shipped", "In progress", "Planned")


# --------------------------------------------------------------------------- helpers


def documents(root: Path = REPO) -> list[Path]:
    paths = [root / "README.md", root / "SECURITY.md", root / "LICENSE"]
    paths += sorted((root / "docs").rglob("*.md"))
    found = []
    for path in paths:
        if not path.is_file():
            continue
        # Judge only the path inside the repository. Checking absolute components
        # would skip every document on a checkout that happens to live under
        # /tmp, /cache, or a node_modules path, and pass while checking nothing.
        if set(path.relative_to(root).parts[:-1]) & SKIP_DIRS:
            continue
        found.append(path)
    return found


# Documents whose absence means the gate is misconfigured rather than satisfied.
REQUIRED = ("README.md", "SECURITY.md", "docs/README.md", "docs/cryptography.md")
MIN_DOCUMENTS = 15


def show(path: Path) -> str:
    """Path as a reader should see it, whether or not it sits inside this repo."""
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return path.name


def slugify(heading: str) -> str:
    text = heading.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    return text.replace(" ", "-")


def anchors(path: Path) -> set[str]:
    found: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        match = HEADING_RE.match(line)
        if match:
            found.add(slugify(match.group(2)))
    return found


# --------------------------------------------------------------------------- checks


def scan_disclosure(path: Path, text: str, label: str | None = None) -> list[str]:
    problems: list[str] = []
    if label is None:
        label = show(path)
    in_fence = False
    for number, line in enumerate(text.splitlines(), start=1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        for name, pattern, remedy in RULES:
            match = pattern.search(line)
            if match:
                problems.append(
                    f"{label}:{number}: [{name}] {match.group(0)!r} — {remedy}"
                )
    return problems


def check_links(path: Path, text: str) -> list[str]:
    problems: list[str] = []
    for target in LINK_RE.findall(text):
        if target.startswith(("http://", "https://", "mailto:", "{{")):
            continue
        location, _, fragment = target.partition("#")
        destination = (path.parent / location).resolve() if location else path
        if not destination.exists():
            problems.append(f"{show(path)}: broken link -> {target}")
            continue
        if fragment and destination.suffix == ".md":
            if fragment not in anchors(destination):
                problems.append(f"{show(path)}: missing anchor -> {target}")
    return problems


def check_claims(texts: dict[Path, str]) -> list[str]:
    problems: list[str] = []
    defined: dict[str, Path] = {}
    referenced: set[str] = set()

    for path, text in texts.items():
        for claim in CLAIM_DEF_RE.findall(text):
            if claim in defined:
                problems.append(
                    f"{show(path)}: claim {claim} already defined in "
                    f"{show(defined[claim])}"
                )
            else:
                defined[claim] = path
        referenced.update(CLAIM_REF_RE.findall(text))

    for claim in sorted(referenced - defined.keys()):
        problems.append(f"claim {claim} is referenced but never defined")
    return problems


def check_status(path: Path, text: str) -> list[str]:
    problems: list[str] = []
    name = path.name
    relative = show(path)
    in_docs = "docs" in path.parts

    if name in STATUS_REQUIRED or (in_docs and path.parent.name != "milestones" and name != "LICENSE"):
        if "Document status" not in text:
            problems.append(f"{relative}: missing a Document status row")
        elif "Public" not in text:
            problems.append(f"{relative}: Document status is not Public")
    return problems


def check_milestones(texts: dict[Path, str]) -> list[str]:
    problems: list[str] = []
    index = texts.get(REPO / "docs" / "README.md", "")
    index_status = {}
    for line in index.splitlines():
        if line.startswith("| M") and "Shipped" in line or line.startswith("| M") and "Planned" in line:
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) >= 4:
                index_status[cells[0]] = cells[3].split()[0]

    for path, text in texts.items():
        if path.parent.name != "milestones" or path.name.startswith("00-"):
            continue
        relative = show(path)
        if "Provenance" not in text:
            problems.append(f"{relative}: missing a Provenance section")
        if "Security properties" not in text:
            problems.append(f"{relative}: missing a Security properties section")
        status = re.search(r"\|\s*\*\*Status\*\*\s*\|\s*([^|]+)\|", text)
        if not status:
            problems.append(f"{relative}: missing a Status row")
            continue
        word = status.group(1).strip().split()[0]
        if word not in STATUS_WORDS:
            problems.append(f"{relative}: status {word!r} is not in the legend")
        milestone = path.name.split("-")[0].upper()
        if milestone in index_status and index_status[milestone] != word:
            problems.append(
                f"{relative}: status {word!r} disagrees with the index "
                f"{index_status[milestone]!r}"
            )
    return problems


def run(root: Path = REPO) -> list[str]:
    docs = documents(root)
    problems: list[str] = []

    # Fail closed: an empty or shrunken document set means the gate is not looking
    # at the repository it thinks it is, not that the repository is clean.
    missing = [name for name in REQUIRED if not (root / name).is_file()]
    if missing:
        problems.append(f"required document(s) missing: {', '.join(missing)}")
    if len(docs) < MIN_DOCUMENTS:
        problems.append(
            f"found only {len(docs)} document(s), expected at least {MIN_DOCUMENTS}"
            " — the gate is misconfigured, not satisfied"
        )

    texts = {path: path.read_text(encoding="utf-8") for path in docs}
    for path, text in texts.items():
        problems += scan_disclosure(path, text)
        problems += check_links(path, text)
        problems += check_status(path, text)
    problems += check_claims(texts)
    problems += check_milestones(texts)
    return problems


# --------------------------------------------------------------------------- self-test


LEAKING_SAMPLE = """# Sample

Contact someone@example.com about it.
The build lives in /Users/someone/src/app and the store id is com.example.app.
A wrong PIN is refused for 30 seconds after five consecutive failures.
TODO: add the missing section.
"""

CLEAN_SAMPLE = """# Sample

Report through the private channel described in the security policy.
A bounded number of failures triggers a short cooldown.
"""


def self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "leaky.md").write_text(LEAKING_SAMPLE, encoding="utf-8")
        (root / "clean.md").write_text(CLEAN_SAMPLE, encoding="utf-8")

        leak_hits = []
        for name in ("leaky.md", "clean.md"):
            text = (root / name).read_text(encoding="utf-8")
            leak_hits += [(name, hit) for hit in scan_disclosure(root / name, text)]

    failures = [hit for hit in leak_hits if hit[0] == "leaky.md"]
    false_positives = [hit for hit in leak_hits if hit[0] == "clean.md"]

    rules_hit = {re.search(r"\[([a-z-]+)\]", text).group(1) for _, text in failures}
    expected = {
        "personal-email",
        "absolute-path",
        "source-layout",
        "package-id",
        "tuning-threshold",
        "unfinished-marker",
    }

    if not expected.issubset(rules_hit):
        print("self-test FAILED: these rules did not fire:", sorted(expected - rules_hit))
        return 1
    if false_positives:
        print("self-test FAILED: false positives on clean input:", false_positives)
        return 1

    # Fail closed. A checkout under /tmp once made the gate report
    # "0 documents, passed". An empty or shrunken repository must be an error.
    with tempfile.TemporaryDirectory() as tmp:
        empty = Path(tmp)
        (empty / "docs").mkdir()
        (empty / "README.md").write_text(CLEAN_SAMPLE, encoding="utf-8")
        shrunk = run(empty)

    if not any("required document" in problem for problem in shrunk):
        print("self-test FAILED: an empty repository was reported as clean")
        return 1
    if not any("misconfigured, not satisfied" in problem for problem in shrunk):
        print("self-test FAILED: a shrunken document set was reported as clean")
        return 1

    print(
        f"self-test passed: {len(failures)} findings on the sample, none on clean text, "
        "empty repository fails closed"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true", help="prove the rules fire")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    problems = run()
    if problems:
        print(f"{len(problems)} problem(s):\n")
        for problem in problems:
            print(" ", problem)
        return 1

    print(f"docs check passed: {len(documents())} documents, no disclosure or link problems")
    return 0


if __name__ == "__main__":
    sys.exit(main())
