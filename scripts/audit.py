#!/usr/bin/env python3
"""Codex Skill Auditor - read-only Sicherheits-Erstpruefung fuer Agent Skills."""

import argparse
import html
import sys
import os
import re
import json
import datetime
import hashlib
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

SCANNER_VERSION = "1.0.3"
SCANNER_BASE_COMMIT = "f41dd61225fc056049ab0d909c3c3c442263474b"

# Windows: UTF-8 Output erzwingen
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ─── Pattern-Definitionen ────────────────────────────────────────────────────

PATTERNS = {
    "A_NETWORK": {
        "risk": "HIGH",
        "label": "Netzwerk / Datenexfiltration",
        "patterns": [
            (r"\bcurl\b",                         "curl-Aufruf"),
            (r"\bwget\b",                         "wget-Aufruf"),
            (r"requests\.(get|post|put|delete)",  "Python requests"),
            (r"\burllib\b",                       "urllib"),
            (r"fetch\(",                          "JS fetch()"),
            (r"\baxios\b",                        "axios"),
            (r"XMLHttpRequest",                   "XHR"),
        ],
        # Beide Seiten der Kombi-Regex nutzen dieselben Wortgrenzen wie die
        # "patterns"-Liste oben (\bcurl\b, requests\.(get|post|...), etc.) statt
        # loser Bare-Words - sonst matcht z. B. "unformed requests only" als
        # Netzwerkaufruf. "token"/"secret" bleiben bewusst ohne \b, weil sie so
        # auch UNTERSTRICH-geschriebene Env-Var-Namen wie SECRET_TOKEN treffen
        # (\b wuerde davor keine Wortgrenze finden, da "_" ein Wortzeichen ist);
        # Bindestrich-Komposita wie "brand-token" bleiben ein bekanntes Restrisiko
        # fuer False Positives - das faengt Phase 4 (manuelle Pruefung) ab, nicht
        # der Scanner (siehe SKILL.md "Wann NICHT aktivieren"-Philosophie: lieber
        # ein Feature/Praezision weglassen als ein irrefuehrendes Signal geben).
        "reject_if": [
            r"(~/.ssh|~/.aws|\.env\b|\bapi[_-]?key\b|\bpassword\b|token|secret).*?"
            r"(\bcurl\b|fetch\(|requests\.(get|post|put|delete)|\burllib\b|\bwget\b)",
            r"(\bcurl\b|fetch\(|requests\.(get|post|put|delete)|\burllib\b|\bwget\b).*?"
            r"(~/.ssh|~/.aws|\.env\b|\bapi[_-]?key\b|\bpassword\b|token|secret)",
            r"base64\.(encode|b64encode).*?(\bsend\b|\bpost\b|\bupload\b|\bcurl\b|fetch\()",
            r"\b(whoami|hostname)\b.*?(\bcurl\b|fetch\(|\bpost\b|\bsend\b)",
        ],
    },
    "B_ENCODING": {
        "risk": "HIGH",
        "label": "Obfuskierung / Encoding",
        "patterns": [
            (r"\bbase64\b",                       "base64"),
            (r"\batob\(",                         "atob()"),
            (r"String\.fromCharCode",             "fromCharCode"),
            (r"\\x[0-9a-fA-F]{2}",               "Hex-Escape"),
            (r"\\u[0-9a-fA-F]{4}",               "Unicode-Escape"),
            (r"\beval\s*\(",                       "eval()"),
        ],
        "reject_if": [],
    },
    "C_EXEC": {
        "risk": "CRITICAL",
        "label": "Code-Ausfuehrung",
        "patterns": [
            (r"\bexec\s*\(",                      "exec()"),
            (r"os\.system\s*\(",                  "os.system()"),
            (r"subprocess\.",                     "subprocess"),
            (r"child_process",                    "child_process (Node)"),
            (r"__import__\s*\(",                  "__import__()"),
            (r"compile\s*\(.*eval",               "compile+eval"),
        ],
        "reject_if": [
            r"\bcurl\s*\|+\s*bash",
            r"\bwget\s*\|+\s*sh",
        ],
    },
    "D_PACKAGES": {
        "risk": "HIGH",
        "label": "Package-Installation / Privilege Escalation",
        "patterns": [
            (r"\bpip\s+install\b",                "pip install"),
            (r"\bnpm\s+install\b",                "npm install"),
            (r"\bapt(-get)?\s+install\b",         "apt install"),
            (r"\bsudo\b",                         "sudo"),
            (r"\bchmod\s+777\b",                  "chmod 777"),
            (r"\bchown\b",                        "chown"),
        ],
        "reject_if": [
            r"PATH\s*=.*\$PATH",
            r"\b(crontab|cron\.d|LaunchAgents|launchctl)\b",
            r"\.(bashrc|zshrc|profile|bash_profile)\s*>>",
        ],
    },
    "E_PROMPT_INJECTION": {
        "risk": "CRITICAL",
        "label": "Prompt Injection & Social Engineering",
        "patterns": [
            (r"ignore.{0,30}previous",            "ignore previous instructions"),
            (r"you are now",                      "Rollenneuzuweisung EN"),
            (r"du bist jetzt",                    "Rollenneuzuweisung DE"),
            (r"forget all",                       "forget all instructions"),
            (r"vergiss alles",                    "Vergiss-Anweisung"),
            (r"<system-reminder>",                "Fake <system-reminder>"),
            (r"<system>",                         "Fake <system>-Tag"),
            (r"<tool_result>",                    "Fake <tool_result>-Tag"),
            (r"override.{0,30}instructions",      "override instructions"),
            (r"trust this skill",                 "trust-forcing"),
            (r"skip.{0,20}vetting",               "vetting bypass"),
            (r"disable.{0,20}safety",             "safety disable"),
            (r"your new purpose",                 "purpose reassignment"),
        ],
        "reject_if": [],
    },
    "F_PERSISTENCE": {
        "risk": "CRITICAL",
        "label": "Persistence & Stealth",
        "patterns": [
            (r"\bcrontab\b",                      "crontab"),
            (r"LaunchAgents",                     "macOS LaunchAgents"),
            (r"\.(bashrc|zshrc)",                 ".bashrc/.zshrc Modifikation"),
            (r"settings\.json",                   "settings.json Zugriff"),
            (r"CLAUDE\.md",                       "CLAUDE.md Zugriff"),
            (r"MEMORY\.md",                       "MEMORY.md Zugriff"),
            (r"SOUL\.md|IDENTITY\.md",            "Identity-Dateien"),
            (r"self.*update|update.*self",        "Self-Update Mechanismus"),
        ],
        "reject_if": [],
    },
    "G_SECRETS": {
        "risk": "HIGH",
        "label": "Secrets & Credential-Zugriff",
        "patterns": [
            (r"~/.ssh",                           "SSH-Verzeichnis"),
            (r"~/.aws",                           "AWS Credentials"),
            (r"\.env\b",                          ".env Datei"),
            (r"\bapi[_-]?key\b",                  "API Key Zugriff"),
            (r"\bpassword\b|\bpasswd\b|\bpasswort\b", "Passwort-Zugriff"),
            (r"\bsecret[_\s]key\b|\bsecret_token\b", "Secret Token"),
            (r"\bprivate[_-]?key\b",              "Private Key"),
        ],
        "reject_if": [],
    },
    "H_TIMEBOMB": {
        "risk": "MEDIUM",
        "label": "Time Bombs / Bedingte Logik",
        "patterns": [
            (r"datetime\.now\(\)|Date\.now\(\)|time\.time\(\)", "Zeitabfrage"),
            (r"if.{0,50}date.{0,30}>",           "Datums-Bedingung"),
            (r"if.{0,50}version.{0,30}[><=]",   "Versions-Bedingung"),
        ],
        "reject_if": [],
    },
    "I_CODEX_CONTROL": {
        "risk": "HIGH",
        "label": "Codex-Konfiguration / Steuerung",
        "patterns": [
            (
                r"(write|modify|edit|append|create|install|register|enable|disable|"
                r"schreib\w*|aender\w*|änder\w*|erstell\w*|installier\w*|aktivier\w*|deaktivier\w*)"
                r".{0,60}(AGENTS\.md|\.codex[/\\\\]config\.toml|\.codex-plugin[/\\\\]plugin\.json|hooks?)",
                "Will Codex-Steuerdatei oder Hook verändern",
            ),
            (
                r"(AGENTS\.md|\.codex[/\\\\]config\.toml|\.codex-plugin[/\\\\]plugin\.json|hooks?)"
                r".{0,60}(write|modify|edit|append|create|install|register|enable|disable|"
                r"schreib\w*|aender\w*|änder\w*|erstell\w*|installier\w*|aktivier\w*|deaktivier\w*)",
                "Codex-Steuerdatei oder Hook mit Änderungsanweisung",
            ),
            (r"\bmcp_servers?\b", "MCP-Konfiguration"),
        ],
        "reject_if": [],
    },
    "L_EXTERNAL_CONTENT": {
        "risk": "MEDIUM",
        "label": "Externe Fremdinhalte / indirekte Prompt Injection",
        "patterns": [
            (
                r"\b(x-api|twitter[ -]?api|social[ -]?media[ -]?api)\b",
                "Externe Social-Media-Schnittstelle oder Live-Quelle",
            ),
            (
                r"\b(pull|fetch|retrieve|collect|gather|scrape|abruf\w*|lad\w*|sammel\w*)\b"
                r".{0,100}\b(posts?|threads?|site copy|website content|user-generated|"
                r"public(?:ly)? available (?:text|content|sources?)|fremdinhalte?)\b",
                "Externe oder nutzergenerierte Inhalte sollen eingelesen werden",
            ),
        ],
        "reject_if": [],
    },
}

READABLE_EXTENSIONS = {
    ".md", ".txt", ".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx",
    ".sh", ".bash", ".zsh", ".fish", ".ps1", ".psm1", ".bat", ".cmd",
    ".json", ".yaml", ".yml", ".toml", ".html", ".css", ".xml", ".ini",
    ".cfg", ".rb", ".php", ".pl",
}
READABLE_FILENAMES = {".gitignore", "LICENSE", "Makefile", "Dockerfile"}
MAX_SCAN_FILE_BYTES = 2_000_000

RISK_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "CONTEXT": 4}
RISK_EMOJI = {
    "CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🔵", "CONTEXT": "⚪"
}

# ─── Datenstrukturen ──────────────────────────────────────────────────────────

@dataclass
class Finding:
    category: str
    risk: str
    label: str
    file: str
    line: int
    description: str
    snippet: str
    is_reject: bool = False
    in_code_fence: bool = False
    original_risk: Optional[str] = None
    context_reason: Optional[str] = None

@dataclass
class SkillAuditResult:
    skill_path: str
    skill_name: str
    findings: list[Finding] = field(default_factory=list)
    files_scanned: list[str] = field(default_factory=list)
    skipped_files: list[dict] = field(default_factory=list)
    content_hash: Optional[str] = None
    source_commit: Optional[str] = None
    source_commit_note: Optional[str] = None
    error: Optional[str] = None

    @property
    def verdict_findings(self) -> list[Finding]:
        return [f for f in self.findings if f.risk != "CONTEXT"]

    @property
    def verdict(self) -> str:
        if any(f.is_reject or f.risk == "CRITICAL" for f in self.verdict_findings):
            return "🔴 NICHT VERWENDEN"
        if any(f.risk in ("HIGH", "MEDIUM") for f in self.verdict_findings):
            return "🟡 MANUELL PRÜFEN"
        return "🟢 KEINE OFFENSICHTLICHEN BEFUNDE"

    @property
    def scanner_verdict(self) -> str:
        return self.verdict

    @property
    def short_verdict(self) -> str:
        if any(f.is_reject or f.risk == "CRITICAL" for f in self.verdict_findings):
            return "🔴 REJECT"
        if any(f.risk in ("HIGH", "MEDIUM") for f in self.verdict_findings):
            return "🟡 PRÜFEN"
        return "🟢 KEINE OFFENSICHTLICHEN BEFUNDE"

    @property
    def max_risk(self) -> str:
        if not self.verdict_findings:
            return "NONE"
        # RISK_ORDER: lower number = more severe (CRITICAL=0). min() surfaces the worst one.
        return min(self.verdict_findings, key=lambda f: RISK_ORDER.get(f.risk, 99)).risk

# ─── Scanner ─────────────────────────────────────────────────────────────────

# Eigene Output-Artefakte, die kein wiederholter Scan-Lauf als Input fressen
# darf - sonst matcht der Scanner auf seinen eigenen vorherigen Findings (z. B.
# der Text "REJECT-Pattern: (...curl|fetch|requests...)" landet als Snippet in
# audit-result.json und wird beim naechsten Lauf selbst wieder als Treffer gezaehlt).
OWN_ARTIFACT_FILES = {"audit-result.json", "skill-inventory-cache.json", "skill-inventory-raw.json"}


def collect_files_and_skipped(skill_dir: Path) -> tuple[list[Path], list[Path], list[dict]]:
    """Liefert Scan-Dateien, Hash-Dateien und transparent ausgelassene Inhalte."""
    scan_files = []
    hash_files = []
    skipped = []
    for dirpath, dirnames, filenames in os.walk(skill_dir, followlinks=False):
        kept_dirs = []
        for dirname in dirnames:
            directory = Path(dirpath) / dirname
            rel = directory.relative_to(skill_dir).as_posix()
            if dirname == ".git":
                skipped.append({
                    "file": f"{rel}/",
                    "reason": "Git-Metadaten werden nicht als Skill-Inhalt gescannt",
                })
            elif directory.is_symlink():
                # Symlinks werden separat bewertet und in den Inhalts-Hash aufgenommen.
                continue
            else:
                kept_dirs.append(dirname)
        dirnames[:] = kept_dirs

        for filename in filenames:
            f = Path(dirpath) / filename
            rel = f.relative_to(skill_dir).as_posix()
            if f.name in OWN_ARTIFACT_FILES:
                skipped.append({
                    "file": rel,
                    "reason": "Eigenes Audit-Artefakt; zum Schutz vor Selbsttreffern ausgeschlossen",
                })
                continue
            if f.is_symlink():
                # Symlinks werden separat bewertet und in den Inhalts-Hash aufgenommen.
                continue
            if not f.is_file():
                skipped.append({"file": rel, "reason": "Kein regulärer Dateityp"})
                continue

            hash_files.append(f)
            if f.suffix.lower() in READABLE_EXTENSIONS or f.name in READABLE_FILENAMES:
                scan_files.append(f)
                try:
                    oversized = f.stat().st_size > MAX_SCAN_FILE_BYTES
                except OSError:
                    oversized = False
                if oversized:
                    skipped.append({
                        "file": rel,
                        "reason": (
                            f"Größer als {MAX_SCAN_FILE_BYTES} Bytes; Inhalt wird gehasht, "
                            "aber nicht vollständig automatisch geprüft"
                        ),
                    })
            else:
                skipped.append({
                    "file": rel,
                    "reason": "Dateityp wird nicht automatisch inhaltlich geprüft; Inhalt wird nur gehasht",
                })

    return sorted(scan_files), sorted(hash_files), sorted(skipped, key=lambda item: item["file"])


def collect_files(skill_dir: Path) -> list[Path]:
    """Kompatibilitätshelfer für Inventar und bestehende Aufrufer."""
    scan_files, _, _ = collect_files_and_skipped(skill_dir)
    return scan_files


def content_hash(files: list[Path], skill_dir: Path) -> str:
    digest = hashlib.sha256()
    for filepath in files:
        rel = filepath.relative_to(skill_dir).as_posix().encode("utf-8")
        digest.update(len(rel).to_bytes(4, "big"))
        digest.update(rel)
        try:
            size = filepath.stat().st_size
            digest.update(size.to_bytes(8, "big"))
            with filepath.open("rb") as handle:
                while chunk := handle.read(1024 * 1024):
                    digest.update(chunk)
        except OSError:
            digest.update((12).to_bytes(8, "big"))
            digest.update(b"<UNREADABLE>")

    symlinks = []
    for dirpath, dirnames, filenames in os.walk(skill_dir, followlinks=False):
        for name in [*dirnames, *filenames]:
            path = Path(dirpath) / name
            if path.is_symlink():
                try:
                    target = os.readlink(path)
                except OSError:
                    target = "<UNREADABLE>"
                symlinks.append((path.relative_to(skill_dir).as_posix(), target))
    for rel_path, target in sorted(symlinks):
        digest.update(f"SYMLINK:{rel_path}->{target}".encode("utf-8", errors="replace"))
    return f"sha256:{digest.hexdigest()}"


def detect_git_commit(skill_dir: Path) -> tuple[Optional[str], str]:
    """Liest HEAD direkt und führt dabei weder Git noch Code des Prüfobjekts aus."""
    for repository_root in (skill_dir, *skill_dir.parents):
        marker = repository_root / ".git"
        if not marker.exists():
            continue
        if marker.is_file():
            return None, (
                "Ausgelagerte Git-Metadaten erkannt; der externe gitdir-Verweis wird "
                "aus Sicherheitsgründen nicht verfolgt"
            )
        if not marker.is_dir():
            return None, "Git-Metadaten haben einen unerwarteten Dateityp"

        try:
            head = (marker / "HEAD").read_text(encoding="utf-8", errors="replace").strip()
        except OSError as exc:
            return None, f"Git-HEAD konnte nicht gelesen werden: {exc}"

        if re.fullmatch(r"[0-9a-fA-F]{40,64}", head):
            return head.lower(), "Direkt aus .git/HEAD gelesen (detached HEAD)"

        if not head.startswith("ref: "):
            return None, "Git-HEAD enthält weder eine Commit-SHA noch eine gültige Referenz"
        ref_name = head[5:].strip()
        if not re.fullmatch(r"refs/[A-Za-z0-9._/-]+", ref_name) or ".." in ref_name:
            return None, "Git-HEAD enthält eine nicht unterstützte Referenz"

        ref_path = marker.joinpath(*ref_name.split("/"))
        try:
            commit = ref_path.read_text(encoding="ascii", errors="replace").strip()
        except OSError:
            commit = ""
        if re.fullmatch(r"[0-9a-fA-F]{40,64}", commit):
            return commit.lower(), f"Direkt aus .git/{ref_name} gelesen"

        try:
            packed_refs = (marker / "packed-refs").read_text(
                encoding="ascii", errors="replace"
            ).splitlines()
        except OSError:
            packed_refs = []
        for line in packed_refs:
            if not line or line.startswith(("#", "^")):
                continue
            parts = line.split(" ", 1)
            if len(parts) == 2 and parts[1] == ref_name and re.fullmatch(
                r"[0-9a-fA-F]{40,64}", parts[0]
            ):
                return parts[0].lower(), f"Direkt aus .git/packed-refs gelesen ({ref_name})"
        return None, f"Git-Referenz {ref_name} konnte nicht aufgelöst werden"

    return None, "Kein umgebendes Git-Repository gefunden"


def inspect_symlinks(skill_dir: Path) -> list[Finding]:
    findings = []
    root = skill_dir.resolve()
    for dirpath, dirnames, filenames in os.walk(skill_dir, followlinks=False):
        for name in [*dirnames, *filenames]:
            path = Path(dirpath) / name
            if not path.is_symlink():
                continue
            target = path.resolve(strict=False)
            try:
                target.relative_to(root)
                outside = False
            except ValueError:
                outside = True
            findings.append(Finding(
                category="J_SYMLINK",
                risk="CRITICAL" if outside else "MEDIUM",
                label="Symbolischer Link",
                file=str(path.relative_to(skill_dir)),
                line=0,
                description=("Link verweist außerhalb des Skill-Ordners" if outside
                             else "Link verweist innerhalb des Skill-Ordners"),
                snippet=f"{path.name} -> {target}",
            ))
    return findings


def _code_fence_mask(lines: list[str]) -> list[bool]:
    """Returns a bool list: True = line is inside a fenced code block."""
    inside = False
    mask = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            inside = not inside
        mask.append(inside)
    return mask


def _strip_code_blocks(content: str) -> str:
    """Remove fenced code blocks (``` or ~~~) from markdown content."""
    result = []
    inside = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            inside = not inside
            result.append("")
        elif not inside:
            result.append(line)
        else:
            result.append("")
    return "\n".join(result)


DOCUMENTATION_CONTEXT_CUES = re.compile(
    r"\b(must\s+not|do\s+not|don't|never|avoid|prevent|unsafe|dangerous|"
    r"vulnerab\w*|bad\s+patterns?|red\s+flags?|search\s+for|look\s+for|"
    r"instead\s+of|rather\s+than|no\s+shell\s+by\s+default|guidance|"
    r"nicht\s+verwenden|niemals|vermeid\w*|verhinder\w*|unsicher\w*|"
    r"gefährlich\w*|verboten\w*|suche\s+nach|prüfe\s+auf)\b",
    re.IGNORECASE,
)


def _documentation_context_mask(lines: list[str]) -> list[bool]:
    """Markiert ausdrückliche Warnungen und Negativbeispiele in Markdown.

    Ein bloßes Wort wie "Beispiel" reicht absichtlich nicht. Nur starke
    Warnsignale im lokalen Vier-Zeilen-Kontext stufen einen Treffer als
    Dokumentationskontext ein; die manuelle Prüfung bleibt erforderlich.
    """
    mask = []
    example_section = False
    contextual_heading = False
    for index in range(len(lines)):
        stripped = lines[index].strip()
        heading = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if heading:
            heading_text = heading.group(2)
            contextual_heading = bool(re.search(
                r"\b(practical\s+scanning|scanning\s+heuristics|sources|"
                r"audit\s+checklist|detection\s+checklist)\b",
                heading_text,
                re.IGNORECASE,
            ))
            example_section = False

        if re.match(
            r"^(insecure|unsafe|bad|dangerous|vulnerable)\s+"
            r"(patterns?|examples?|code)\s*:?$|^detection\s+hints?\s*:?$",
            stripped,
            re.IGNORECASE,
        ):
            example_section = True
        elif re.match(
            r"^(required|fix|mitigation|safe\s+patterns?|notes?|references?)\s*:?$",
            stripped,
            re.IGNORECASE,
        ):
            example_section = False

        window = " ".join(lines[max(0, index - 3):index + 1])
        mask.append(
            contextual_heading
            or example_section
            or bool(DOCUMENTATION_CONTEXT_CUES.search(window))
        )
    return mask


def _markdown_section_ranges(lines: list[str]) -> list[tuple[int, int, str]]:
    """Liefert Überschriftenabschnitte inklusive ihrer Unterabschnitte.

    Ein Abschnitt endet an der nächsten Überschrift gleicher oder höherer
    Ebene. Dadurch kann eine Kombination auch über Leerzeilen und untergeordnete
    Überschriften hinweg erkannt werden, ohne benachbarte Hauptabschnitte
    miteinander zu vermischen.
    """
    if not lines:
        return []

    headings = []
    for index, line in enumerate(lines):
        match = re.match(r"^(#{1,6})\s+(.+)$", line.strip())
        if match:
            headings.append((index, len(match.group(1)), match.group(2).strip()))

    if not headings:
        return [(0, len(lines), "Dokument ohne Überschriften")]

    ranges = []
    if headings[0][0] > 0:
        ranges.append((0, headings[0][0], "Vorspann"))

    stack = []
    for index, level, title in headings:
        while stack and stack[-1][1] >= level:
            start, _, previous_title = stack.pop()
            ranges.append((start, index, previous_title))
        stack.append((index, level, title))

    while stack:
        start, _, title = stack.pop()
        ranges.append((start, len(lines), title))

    return sorted(ranges, key=lambda item: (item[1] - item[0], item[0]))


def scan_file(filepath: Path, skill_dir: Path) -> list[Finding]:
    findings = []
    rel_path = str(filepath.relative_to(skill_dir))

    try:
        if filepath.stat().st_size > MAX_SCAN_FILE_BYTES:
            return [Finding(
                category="K_COVERAGE",
                risk="MEDIUM",
                label="Prüfabdeckung",
                file=rel_path,
                line=0,
                description=f"Datei größer als {MAX_SCAN_FILE_BYTES} Bytes; Inhalt nicht automatisch geprüft",
                snippet="Manuelle Prüfung erforderlich",
            )]
        content = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return [Finding(
            category="K_COVERAGE",
            risk="MEDIUM",
            label="Prüfabdeckung",
            file=rel_path,
            line=0,
            description="Datei konnte nicht automatisch gelesen werden",
            snippet=type(exc).__name__,
        )]

    lines = content.splitlines()
    is_md = filepath.suffix.lower() == ".md"
    fence_mask = _code_fence_mask(lines) if is_md else [False] * len(lines)
    documentation_mask = _documentation_context_mask(lines) if is_md else [False] * len(lines)
    markdown_sections = _markdown_section_ranges(lines) if is_md else []
    if is_md and fence_mask and fence_mask[-1]:
        findings.append(Finding(
            category="K_COVERAGE",
            risk="HIGH",
            label="Prüfabdeckung",
            file=rel_path,
            line=len(lines),
            description="Nicht geschlossener Markdown-Codeblock kann nachfolgenden Inhalt verdecken",
            snippet="Codeblock endet nicht mit ``` oder ~~~",
        ))
    for cat_key, cat in PATTERNS.items():
        risk = cat["risk"]
        label = cat["label"]

        for pat_str, description in cat["patterns"]:
            try:
                pat = re.compile(pat_str, re.IGNORECASE)
            except re.error:
                continue
            for lineno, line in enumerate(lines, start=1):
                if pat.search(line):
                    in_fence = is_md and fence_mask[lineno - 1]
                    in_documentation = is_md and documentation_mask[lineno - 1]
                    is_context = in_fence or in_documentation
                    snippet = line.strip()[:120]
                    findings.append(Finding(
                        category=cat_key,
                        risk="CONTEXT" if is_context else risk,
                        label=label,
                        file=rel_path,
                        line=lineno,
                        description=description,
                        snippet=snippet,
                        is_reject=False,
                        in_code_fence=in_fence,
                        original_risk=risk if is_context else None,
                        context_reason=(
                            "markdown_code_fence" if in_fence else
                            "sicherheitswarnung_oder_negativbeispiel" if in_documentation else None
                        ),
                    ))

        for reject_str in cat.get("reject_if", []):
            try:
                reject_pat = re.compile(reject_str, re.IGNORECASE)
            except re.error:
                continue
            # Stufe 1: Ein enger lokaler Block bleibt ein hochpräziser
            # automatischer Ablehnungsbefund.
            local_reject_lines = []
            for start in range(len(lines)):
                end = min(len(lines), start + 3)
                window_parts = []
                for index in range(start, end):
                    if (is_md and fence_mask[index]) or (is_md and documentation_mask[index]):
                        window_parts.append("")
                    else:
                        window_parts.append(lines[index])
                window = " ".join(window_parts)
                if reject_pat.search(window):
                    findings.append(Finding(
                        category=cat_key,
                        risk="CRITICAL",
                        label=label,
                        file=rel_path,
                        line=start + 1,
                        description="Gefährliche Musterkombination im lokalen Kontext",
                        snippet=window.strip()[:120],
                        is_reject=True,
                    ))
                    local_reject_lines.append(start)
                    break

            if not is_md:
                continue

            # Stufe 2: In Markdown können zusammengehörige Anweisungen über
            # Leerzeilen, Absätze und Unterüberschriften verteilt sein. Solche
            # Abschnittstreffer werden sichtbar, aber wegen des größeren
            # Kontexts nicht automatisch als REJECT gewertet.
            section_matches = []
            for section_start, section_end, section_title in markdown_sections:
                section_parts = []
                for index in range(section_start, section_end):
                    if fence_mask[index] or documentation_mask[index]:
                        section_parts.append("")
                    else:
                        section_parts.append(lines[index])
                section_text = " ".join(section_parts)
                match = reject_pat.search(section_text)
                if match:
                    section_matches.append((
                        section_start,
                        section_end,
                        section_title,
                        match.group(0).strip(),
                    ))

            # Unterabschnitte zuerst behalten. Ein übergeordneter Abschnitt
            # wird nur zusätzlich gemeldet, wenn die Kombination erst über
            # mehrere Unterabschnitte hinweg entsteht.
            minimal_matches = []
            for candidate in section_matches:
                start, end, _, _ = candidate
                if any(
                    start <= kept_start and end >= kept_end
                    for kept_start, kept_end, _, _ in minimal_matches
                ):
                    continue
                minimal_matches.append(candidate)

            for section_start, section_end, section_title, matched_text in minimal_matches:
                if any(
                    section_start <= local_line < section_end
                    for local_line in local_reject_lines
                ):
                    continue
                findings.append(Finding(
                    category=cat_key,
                    risk="HIGH",
                    label=label,
                    file=rel_path,
                    line=section_start + 1,
                    description=(
                        "Gefährliche Musterkombination im selben Markdown-Abschnitt; "
                        "manuelle Prüfung erforderlich"
                    ),
                    snippet=f"Abschnitt „{section_title}“: {matched_text}"[:120],
                    is_reject=False,
                ))

    return findings


def audit_skill(skill_path: str) -> SkillAuditResult:
    skill_dir = Path(skill_path).resolve()
    skill_name = skill_dir.name
    result = SkillAuditResult(skill_path=str(skill_dir), skill_name=skill_name)

    if not skill_dir.exists():
        result.error = f"Verzeichnis nicht gefunden: {skill_dir}"
        return result

    files, hash_files, result.skipped_files = collect_files_and_skipped(skill_dir)
    if not files:
        result.error = "Keine lesbaren Dateien gefunden"
        return result

    for f in files:
        rel = str(f.relative_to(skill_dir))
        result.files_scanned.append(rel)
        result.findings.extend(scan_file(f, skill_dir))

    result.content_hash = content_hash(hash_files, skill_dir)
    result.source_commit, result.source_commit_note = detect_git_commit(skill_dir)
    result.findings.extend(inspect_symlinks(skill_dir))
    result.findings.sort(key=lambda f: (RISK_ORDER.get(f.risk, 99), f.file, f.line))
    return result

# ─── Inventar-Modus ──────────────────────────────────────────────────────────
# Sammelt Codex-Skills aus Benutzer-, Repository- und Plugin-Verzeichnissen.
# Plugin-Herkunft ist nur Provenienz und niemals ein Sicherheitsurteil.

DEFAULT_CODEX_HOME = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))


def find_skill_md(skill_dir: Path) -> Optional[Path]:
    for candidate in ("SKILL.md", "skill.md"):
        p = skill_dir / candidate
        if p.exists():
            return p
    return None


def parse_frontmatter(md_path: Path) -> dict:
    """Liest 'name:' und 'description:' aus dem YAML-Frontmatter einer SKILL.md."""
    meta = {"name": md_path.parent.name, "description": ""}
    try:
        text = md_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return meta
    if not text.lstrip().startswith("---"):
        return meta
    parts = text.split("---", 2)
    if len(parts) < 3:
        return meta

    lines = parts[1].splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if ":" not in line:
            i += 1
            continue
        key, _, value = line.partition(":")
        key = key.strip().lower()
        value = value.strip()
        if key in ("name", "description") and value in ("|", ">"):
            # YAML block scalar: following indented lines are the value.
            block = []
            i += 1
            while i < len(lines) and (lines[i].startswith((" ", "\t")) or not lines[i].strip()):
                block.append(lines[i].strip())
                i += 1
            value = " ".join(l for l in block if l)
            if key == "name":
                meta["name"] = value
            else:
                meta["description"] = value
            continue
        value = value.strip('"').strip("'")
        if key == "name" and value:
            meta["name"] = value
        elif key == "description" and value:
            meta["description"] = value
        i += 1
    return meta


def _deduplicate_paths(paths: list[Path]) -> list[Path]:
    result = []
    seen = set()
    for path in paths:
        resolved = path.expanduser().resolve(strict=False)
        key = os.path.normcase(str(resolved))
        if key not in seen:
            seen.add(key)
            result.append(resolved)
    return result


def default_skill_roots(cwd: Optional[Path] = None) -> list[Path]:
    start = (cwd or Path.cwd()).resolve(strict=False)
    roots = [Path.home() / ".agents" / "skills", DEFAULT_CODEX_HOME / "skills"]
    roots.extend(parent / ".agents" / "skills" for parent in (start, *start.parents))
    if os.name != "nt":
        roots.append(Path("/etc/codex/skills"))
    return _deduplicate_paths(roots)


def default_plugin_roots() -> list[Path]:
    return _deduplicate_paths([DEFAULT_CODEX_HOME / "plugins"])


def _direct_skill_dirs(root: Path) -> list[Path]:
    if not root.exists() or not root.is_dir():
        return []
    if find_skill_md(root):
        return [root]
    try:
        return sorted(p for p in root.iterdir() if p.is_dir() and find_skill_md(p))
    except OSError:
        return []


def _plugin_skill_dirs(root: Path) -> list[Path]:
    if not root.exists() or not root.is_dir():
        return []
    found = []
    try:
        for skill_md in root.rglob("SKILL.md"):
            if ".git" not in skill_md.parts:
                found.append(skill_md.parent)
    except OSError:
        return []
    return _deduplicate_paths(found)


def load_audit_status(skill_dir: Path, reports_dir: Optional[Path] = None) -> dict:
    """Liest einen Report und kennzeichnet geänderte Inhalte als veraltet."""
    current_hash = content_hash(collect_files(skill_dir), skill_dir)
    candidates = [skill_dir / "audit-result.json"]
    if reports_dir and reports_dir.exists():
        try:
            candidates.extend(sorted(
                reports_dir.glob("*-audit.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            ))
        except OSError:
            pass

    for report in candidates:
        if not report.exists():
            continue
        try:
            data = json.loads(report.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        stored_path = data.get("path")
        if not stored_path:
            continue
        report_path = Path(stored_path).resolve(strict=False)
        if report_path != skill_dir.resolve(strict=False):
            continue
        stored_hash = data.get("content_hash")
        if not stored_hash or stored_hash != current_hash:
            status = "stale"
        else:
            risk = data.get("max_risk", "NONE")
            stored_verdict = data.get("scanner_verdict") or data.get("overall_risk")
            if risk == "CRITICAL" or "REJECT" in (stored_verdict or ""):
                status = "reject"
            elif risk in ("HIGH", "MEDIUM"):
                status = "caution"
            else:
                status = "clear"
        return {
            "status": status,
            "verdict": data.get("scanner_verdict") or data.get("overall_risk"),
            "audited_at": data.get("audited_at"),
            "content_hash": current_hash,
            "report": str(report),
        }

    return {
        "status": "unaudited",
        "verdict": None,
        "audited_at": None,
        "content_hash": current_hash,
        "report": None,
    }


def scan_installed_skills(
    skill_roots: Optional[list[Path]] = None,
    plugin_roots: Optional[list[Path]] = None,
    reports_dir: Optional[Path] = None,
) -> list[dict]:
    """Sammelt Codex-Skills; Herkunft und Auditstatus bleiben getrennte Felder."""
    entries_by_path = {}

    def add_skill(skill_dir: Path, source: str) -> None:
        resolved = skill_dir.resolve(strict=False)
        key = os.path.normcase(str(resolved))
        if key in entries_by_path:
            if source not in entries_by_path[key]["sources"]:
                entries_by_path[key]["sources"].append(source)
            return
        md = find_skill_md(resolved)
        if not md:
            return
        meta = parse_frontmatter(md)
        entries_by_path[key] = {
            "name": meta["name"],
            "description": meta["description"],
            "path": str(resolved),
            "sources": [source],
            **load_audit_status(resolved, reports_dir),
        }

    selected_skill_roots = default_skill_roots() if skill_roots is None else skill_roots
    selected_plugin_roots = default_plugin_roots() if plugin_roots is None else plugin_roots

    for root in _deduplicate_paths(selected_skill_roots):
        for skill_dir in _direct_skill_dirs(root):
            add_skill(skill_dir, f"skill-root:{root}")

    for root in _deduplicate_paths(selected_plugin_roots):
        for skill_dir in _plugin_skill_dirs(root):
            add_skill(skill_dir, f"plugin:{root}")

    return sorted(entries_by_path.values(), key=lambda entry: entry["name"].lower())


def write_inventory_json(entries: list[dict], output_path: Path) -> None:
    output_path.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")


INVENTORY_STATUS_META = {
    "reject": ("🔴", "Nicht verwenden", "status-reject"),
    "caution": ("🟡", "Manuell prüfen", "status-caution"),
    "stale": ("🟠", "Veraltet – erneut prüfen", "status-stale"),
    "unaudited": ("⚪", "Nicht geprüft", "status-unaudited"),
    "clear": ("🟢", "Keine offensichtlichen Befunde", "status-clear"),
}


def render_inventory_html(entries: list[dict], template_path: Optional[Path] = None) -> str:
    """Erzeugt ein selbstenthaltenes, HTML-escaped Status-Dashboard."""
    selected_template = template_path or Path(__file__).with_name("inventory_template.html")
    template = selected_template.read_text(encoding="utf-8")
    sections = []

    for status, (symbol, label, css_class) in INVENTORY_STATUS_META.items():
        matching = [entry for entry in entries if entry.get("status") == status]
        if not matching:
            continue
        cards = []
        for entry in matching:
            name = html.escape(str(entry.get("name") or "Unbenannter Skill"))
            description = html.escape(str(entry.get("description") or "Keine Beschreibung verfügbar."))
            path = html.escape(str(entry.get("path") or "Unbekannter Pfad"))
            sources = html.escape(", ".join(str(source) for source in entry.get("sources", [])) or "unbekannt")
            verdict = html.escape(str(entry.get("verdict") or label))
            cards.append(
                "<article class=\"card\">"
                "<div class=\"card-head\">"
                f"<h3>{name}</h3><span class=\"badge {css_class}\" title=\"{html.escape(label)}\">{symbol}</span>"
                "</div>"
                f"<p>{description}</p>"
                f"<p class=\"meta\"><b>Status:</b> {verdict}<br><b>Quelle:</b> {sources}<br>"
                f"<b>Pfad:</b> <code>{path}</code></p>"
                "</article>"
            )
        sections.append(
            "<section class=\"category\">"
            f"<h2>{symbol} {html.escape(label)} <span class=\"count\">{len(matching)} Skills</span></h2>"
            f"<div class=\"grid\">{''.join(cards)}</div>"
            "</section>"
        )

    if not sections:
        sections.append('<p class="empty">Keine installierten Skills gefunden.</p>')

    generated_at = datetime.datetime.now().astimezone().strftime("%d.%m.%Y, %H:%M %Z")
    return (
        template.replace("{{GENERATED_AT}}", html.escape(generated_at))
        .replace("{{TOTAL}}", str(len(entries)))
        .replace("{{STATUS_SECTIONS}}", "\n".join(sections))
    )


def write_inventory_html(entries: list[dict], output_path: Path) -> Path:
    """Schreibt das Dashboard nur an das ausdrücklich gewählte Ziel."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_inventory_html(entries), encoding="utf-8")
    return output_path


def print_inventory_summary(entries: list[dict]) -> None:
    total = len(entries)
    unaudited = sum(1 for e in entries if e.get("status") == "unaudited")
    caution = sum(1 for e in entries if e.get("status") == "caution")
    reject = sum(1 for e in entries if e.get("status") == "reject")
    stale = sum(1 for e in entries if e.get("status") == "stale")
    clear = sum(1 for e in entries if e.get("status") == "clear")
    print(f"Skills gefunden: {total}")
    print(f"  🟢 keine offensichtlichen Befunde: {clear}")
    print(f"  🟡 Hinweise:       {caution}")
    print(f"  🔴 nicht verwenden: {reject}")
    print(f"  🟠 veraltet, erneut prüfen: {stale}")
    print(f"  ⚪ nicht geprüft:   {unaudited}")

# ─── Report-Ausgabe ──────────────────────────────────────────────────────────

def print_report(result: SkillAuditResult) -> None:
    sep = "═" * 60

    if result.error:
        print(f"\n{sep}")
        print(f"Skill-Audit: {result.skill_name}")
        print(f"FEHLER: {result.error}")
        print(sep)
        return

    print(f"\n{sep}")
    print(f"Skill-Audit: {result.skill_name}")
    print(sep)
    print(f"Pfad:             {result.skill_path}")
    print(f"Geprüfte Dateien: {len(result.files_scanned)}")
    print(f"Inhalts-Hash:     {result.content_hash or 'nicht verfügbar'}")
    if result.source_commit:
        print(f"Commit-SHA:       {result.source_commit}")
    print(f"Commit-Hinweis:   {result.source_commit_note or 'nicht verfügbar'}")
    for f in result.files_scanned:
        print(f"  · {f}")
    print(f"Scanner-Rohurteil: {result.scanner_verdict}")
    if result.skipped_files:
        print(f"Nicht vollständig automatisch geprüft: {len(result.skipped_files)}")
        for skipped in result.skipped_files:
            print(f"  · {skipped['file']}: {skipped['reason']}")
    print()

    if not result.findings:
        print("Keine Auffälligkeiten gefunden.")
    else:
        print(f"{'#':<4} {'Risiko':<10} {'Kategorie':<35} {'Datei:Zeile':<30} {'Beschreibung'}")
        print("─" * 120)
        for i, f in enumerate(result.findings, 1):
            emoji = RISK_EMOJI.get(f.risk, "")
            loc = f"{f.file}:{f.line}" if f.line else f.file
            reject_marker = " [REJECT]" if f.is_reject else ""
            context_marker = (
                f" [Codeblock-Kontext; ursprüngliche Stufe {f.original_risk}]"
                if f.in_code_fence else ""
            )
            print(
                f"{i:<4} {emoji}{f.risk:<9} {f.label:<35} {loc:<30} "
                f"{f.description}{reject_marker}{context_marker}"
            )
            if f.snippet and f.snippet != "(ganzer Dateiinhalt)":
                print(f"     └─ {f.snippet}")

    print()
    print("Scanner-Empfehlung:", result.scanner_verdict)
    print("Hinweis: Das Scanner-Rohurteil ist keine manuelle Gesamtbewertung und kein Security-Zertifikat.")
    print(sep)


def result_to_dict(result: SkillAuditResult) -> dict:
    return {
        "schema_version": 1,
        "scanner_version": SCANNER_VERSION,
        "scanner_base_commit": SCANNER_BASE_COMMIT,
        "skill": result.skill_name,
        "path": result.skill_path,
        "scanner_verdict": result.scanner_verdict,
        "max_risk": result.max_risk,
        "audited_at": datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat(timespec="seconds"),
        "content_hash": result.content_hash,
        "source_commit": result.source_commit,
        "source_commit_note": result.source_commit_note,
        "files_scanned": result.files_scanned,
        "skipped_files": result.skipped_files,
        "total_findings": len(result.findings),
        "verdict_findings": len(result.verdict_findings),
        "findings": [
            {
                "category": f.category,
                "label": f.label,
                "risk": f.risk,
                "original_risk": f.original_risk,
                "file": f.file,
                "line": f.line,
                "description": f.description,
                "snippet": f.snippet,
                "is_reject": f.is_reject,
                "in_code_fence": f.in_code_fence,
                "context_reason": f.context_reason,
            }
            for f in result.findings
        ],
        "limitations": (
            "Automatisches Scanner-Rohurteil; die manuelle Gesamtbewertung bleibt separat "
            "und ist kein vollständiges Security-Review."
        ),
    }


def report_filename(result: SkillAuditResult) -> str:
    safe_name = re.sub(r"[^a-zA-Z0-9._-]+", "-", result.skill_name).strip("-") or "skill"
    digest = (result.content_hash or "sha256:unbekannt").split(":", 1)[-1][:12]
    return f"{safe_name}-{digest}-audit.json"


def write_json_report(result: SkillAuditResult, out_path: Path) -> Optional[Path]:
    """Schreibt nur an den explizit per --output gewählten Ort."""
    if result.error:
        return None
    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(result_to_dict(result), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return out_path
    except OSError:
        return None


def print_batch_summary(results: list[SkillAuditResult]) -> None:
    print("\n")
    print("BATCH-AUDIT")
    print("═" * 55)
    print(f"{'Skill':<30} {'Risiko':<10} {'Verdict'}")
    print("─" * 55)
    for r in results:
        risk = r.max_risk if not r.error else "ERROR"
        print(f"{r.skill_name:<30} {risk:<10} {r.short_verdict}")
    print("─" * 55)
    total = len(results)
    flags = sum(1 for r in results if r.findings)
    rejects = sum(1 for r in results if "REJECT" in r.short_verdict)
    print(f"Gesamt: {total} Skills | {flags} mit Flags | {rejects} Rejections")
    print("═" * 55)

# ─── Einstiegspunkt ──────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Codex Skills read-only auf auffällige Muster prüfen.",
    )
    parser.add_argument("skill_paths", nargs="*", help="Zu prüfende Skill-Verzeichnisse")
    parser.add_argument("--inventory", action="store_true", help="Installierte Codex Skills inventarisieren")
    parser.add_argument("--output", type=Path, help="Explizites Ziel für JSON; ohne Option wird nichts gespeichert")
    parser.add_argument(
        "--inventory-html",
        type=Path,
        help="Explizites Ziel für ein selbstenthaltenes HTML-Dashboard; nur mit --inventory",
    )
    parser.add_argument("--json", action="store_true", dest="json_stdout", help="JSON nur auf stdout ausgeben")
    parser.add_argument("--skills-root", action="append", type=Path, default=[], help="Zusätzliches Skill-Verzeichnis")
    parser.add_argument("--plugins-root", action="append", type=Path, default=[], help="Zusätzliches Plugin-Verzeichnis")
    parser.add_argument("--reports-dir", type=Path, help="Ordner mit früheren Audit-Reports")
    return parser


def _audit_output_path(requested: Path, result: SkillAuditResult, batch: bool) -> Path:
    if not batch and requested.suffix.lower() == ".json":
        return requested
    return requested / report_filename(result)


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.inventory_html and not args.inventory:
        parser.error("--inventory-html kann nur zusammen mit --inventory verwendet werden")

    if args.inventory:
        skill_roots = args.skills_root or default_skill_roots()
        plugin_roots = args.plugins_root or default_plugin_roots()
        entries = scan_installed_skills(skill_roots, plugin_roots, args.reports_dir)
        if args.output:
            output_path = args.output
            if output_path.suffix.lower() != ".json":
                output_path = output_path / "skill-inventory-raw.json"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            write_inventory_json(entries, output_path)
            print(f"Rohdaten geschrieben: {output_path}")
        if args.inventory_html:
            html_path = args.inventory_html
            if html_path.suffix.lower() != ".html":
                html_path = html_path / "skill-inventar.html"
            write_inventory_html(entries, html_path)
            print(f"HTML-Dashboard geschrieben: {html_path}")
        if args.json_stdout:
            print(json.dumps(entries, indent=2, ensure_ascii=False))
        else:
            print_inventory_summary(entries)
        return 0

    if not args.skill_paths:
        build_parser().print_help()
        return 2

    results = [audit_skill(path) for path in args.skill_paths]
    if args.json_stdout:
        payload = [result_to_dict(r) for r in results]
        print(json.dumps(payload[0] if len(payload) == 1 else payload, indent=2, ensure_ascii=False))
    else:
        for result in results:
            print_report(result)
        if len(results) > 1:
            print_batch_summary(results)

    if args.output:
        for result in results:
            json_path = write_json_report(
                result,
                _audit_output_path(args.output, result, len(results) > 1),
            )
            if json_path and not args.json_stdout:
                print(f"JSON-Report: {json_path}")

    has_reject = any("REJECT" in r.short_verdict for r in results)
    has_error = any(r.error for r in results)
    return 2 if has_error else (1 if has_reject else 0)


if __name__ == "__main__":
    raise SystemExit(main())
