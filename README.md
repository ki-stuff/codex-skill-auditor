# Codex Skill Auditor

Version 1.0.3

Der Codex Skill Auditor prüft fremde oder unbekannte Agent-Skills, bevor du sie installierst oder verwendest. Er sucht nach auffälligen Mustern wie Prompt Injection, Datenabfluss, versteckter Codeausführung und dauerhaften Änderungen an deiner Codex-Konfiguration.

Der automatische Scan ist eine **Erstprüfung**, kein Sicherheitszertifikat. Ein grünes Ergebnis bedeutet ausschließlich: Im exakt geprüften Stand wurden keine offensichtlichen Befunde erkannt.

[Hier mehr Infos mit einem Beispiel](https://online-marketing49.de/skill-auditor/codex/)

## Auf einen Blick

Der Inventar-Modus stellt gefundene Codex Skills als visuelles HTML-Dashboard dar:

| Status | Bedeutung |
|---|---|
| 🟢 | Keine offensichtlichen Befunde im geprüften Stand |
| 🟡 | Hinweise vorhanden – manuell im Kontext prüfen |
| 🔴 | Kritischer Befund oder gefährliche Kombination – nicht verwenden |
| 🟠 | Seit dem letzten Report verändert – erneut prüfen |
| ⚪ | Noch nicht geprüft |

Das Dashboard zeigt Name, Kurzbeschreibung, Herkunft und Pfad jedes Skills. Es ist selbstenthalten, lädt keine externen Ressourcen und wird nur an ein ausdrücklich gewähltes Ziel geschrieben.

## Was ist ein Skill?

Ein Skill ist ein Ordner mit einer `SKILL.md`. Darin stehen Anweisungen für Codex. Zusätzlich kann der Ordner Skripte, Referenzen, Konfigurationen oder andere Dateien enthalten. Deshalb reicht es nicht, nur den sichtbaren Beschreibungstext zu lesen.

## Was V1 prüft

- Prompt Injection und gefälschte Systemanweisungen
- Netzwerkzugriffe und mögliche Datenübertragung
- Codeausführung und nachgeladene Programme
- Paketinstallationen und Rechteausweitung
- dauerhafte Änderungen an `AGENTS.md`, Codex-Konfigurationen, Hooks oder Plugins
- Zugriffe auf Schlüssel, Passwörter und Umgebungsdateien
- zeit- oder versionsabhängiges Verhalten
- Symlinks, die aus dem Skill-Ordner hinausführen
- Codex-Skills in Benutzer-, Repository- und Plugin-Verzeichnissen

## Sicherheitsprinzipien

- Der zu prüfende Skill wird nicht ausgeführt.
- Ohne `--output` wird keine Datei geschrieben.
- GitHub-, Marketplace- oder Plugin-Herkunft gilt nicht automatisch als vertrauenswürdig.
- Treffer in Markdown-Codeblöcken und klaren Sicherheitswarnungen oder Negativbeispielen werden als `CONTEXT` angezeigt und nicht automatisch als Angriff gewertet.
- Gefährliche Kombinationen werden zweistufig geprüft: im engen Drei-Zeilen-Kontext mit hoher Präzision und zusätzlich innerhalb desselben Markdown-Abschnitts als Hinweis zur manuellen Prüfung.
- Das Einlesen externer Web- oder Social-Media-Inhalte löst eine manuelle Prüfung auf indirekte Prompt-Injection aus.
- Reports enthalten einen Inhalts-Hash und – wenn sicher direkt lesbar – die Commit-SHA samt Herkunftshinweis.
- Nicht oder nur teilweise automatisch geprüfte Dateien werden mit Begründung aufgelistet und müssen manuell geprüft werden.

## Voraussetzungen

- Python 3
- optional Git, damit eine Commit-SHA ermittelt werden kann
- keine weiteren Python-Pakete

## Installation

### Am einfachsten mit Codex

Bitte Codex:

```text
$skill-installer Installiere den Skill aus https://github.com/ki-stuff/codex-skill-auditor
```

Der Installer kann Skills auch aus anderen GitHub-Repositories laden. Codex erkennt neu installierte oder geänderte Skills normalerweise automatisch. Falls der Skill danach nicht erscheint, starte Codex einmal neu.

### Manuell unter Windows

Lade das Repository über **Code → Download ZIP** herunter, entpacke es und kopiere den Ordner nach:

```text
C:\Users\DEIN-NAME\.agents\skills\codex-skill-auditor
```

Der Zielordner muss direkt die Datei `SKILL.md` enthalten. Die offiziellen Codex-Hinweise zu Aufbau, Installation und Speicherorten findest du unter [Skills erstellen und verwenden](https://developers.openai.com/codex/skills).

## Mit Codex verwenden

Nach der Installation kannst du beispielsweise schreiben:

```text
$codex-skill-auditor Prüfe den Skill in C:\Pfad\zum\fremden-skill, bevor ich ihn installiere.
```

Oder natürlicher:

```text
Prüfe diesen heruntergeladenen Codex Skill auf Sicherheitsrisiken. Nimm keine Änderungen vor.
```

## Scanner direkt ausführen

Read-only prüfen, ohne etwas zu speichern:

```powershell
python .\scripts\audit.py "C:\Pfad\zum\fremden-skill"
```

Maschinenlesbares JSON nur in der Konsole ausgeben:

```powershell
python .\scripts\audit.py "C:\Pfad\zum\fremden-skill" --json
```

Report bewusst an einem gewählten Ort speichern:

```powershell
python .\scripts\audit.py "C:\Pfad\zum\fremden-skill" --output ".\reports"
```

Installierte Codex Skills inventarisieren, ohne zu schreiben:

```powershell
python .\scripts\audit.py --inventory
```

Für eigene Installationsorte kannst du `--skills-root` oder `--plugins-root` mehrfach angeben.

Ein selbstenthaltenes HTML-Dashboard für Menschen erzeugen:

```powershell
python .\scripts\audit.py --inventory --inventory-html ".\reports\skill-inventar.html"
```

Das Dashboard gruppiert installierte Skills nach ihrem Status und zeigt Herkunft, Pfad und Kurzbeschreibung. Die Legende unterscheidet 🟢 keine offensichtlichen Befunde, 🟡 manuell prüfen, 🔴 nicht verwenden, 🟠 veraltet und ⚪ nicht geprüft. Fremde Skill-Texte werden vor dem Einsetzen in HTML escaped. Ohne ein ausdrücklich gewähltes Ziel wird keine HTML-Datei geschrieben.

## Ergebnisse verstehen

Der Scanner erzeugt zuerst ein **Scanner-Rohurteil**. Erst nachdem die tatsächliche Absicht, der Berechtigungsumfang, die Herkunft und alle ausgelassenen Dateien gelesen wurden, folgt die **Gesamtbewertung nach manueller Prüfung**. Beides darf nicht gleichgesetzt werden.

- 🔴 **Nicht verwenden:** mindestens ein kritischer Direktbefund oder eine gefährliche Musterkombination
- 🟡 **Manuell prüfen:** auffälliger Befund, der im Kontext erklärt werden muss
- 🟢 **Keine offensichtlichen Befunde:** kein direkt wertender Treffer im geprüften Stand
- ⚪ **Kontext:** Muster steht in einem Codeblock oder einer klaren Sicherheitswarnung und beeinflusst das Urteil nicht automatisch
- 🟠 **Veraltet:** Der Skill wurde nach dem früheren Report verändert und muss erneut geprüft werden

Ein abschnittsweiter Kombinationstreffer wird bewusst gelb beziehungsweise `HIGH` eingestuft. Er schließt Umgehungen über Leerzeilen und Unterüberschriften nicht blind als Angriff ein, macht sie aber für die manuelle Prüfung sichtbar.

## Enthaltene Dateien

```text
codex-skill-auditor/
├── SKILL.md
├── agents/openai.yaml
├── references/
│   ├── pruefverfahren.md
│   └── reportformat.md
├── scripts/
│   ├── audit.py
│   └── inventory_template.html
├── tests/test_audit.py
├── CHANGELOG.md
├── LICENSE
└── README.md
```

## Herkunft

V1 basiert auf dem MIT-lizenzierten Repository `ki-stuff/skill-auditor`, Commit `f41dd61225fc056049ab0d909c3c3c442263474b`. Dieser Wert heißt im maschinenlesbaren Report `scanner_base_commit`; die `source_commit` bezeichnet dagegen den Git-Stand des jeweils geprüften Skills. Die Codex-spezifischen Anpassungen werden getrennt dokumentiert.

Die Codex-Edition ist eine eigenständige Weiterentwicklung für Codex. Sie teilt die Grundidee und die MIT-lizenzierte Ausgangsbasis mit der Claude-Code-Edition, besitzt aber eigene Plattformpfade, Sicherheitsregeln, Dokumentation und Tests.

## Lizenz

MIT – siehe `LICENSE`.

---

# Codex Skill Auditor — English

Version 1.0.3

Codex Skill Auditor reviews new, external, or unfamiliar agent skills before you install or use them. It looks for prompt injection, data exfiltration, hidden code execution, persistence, unnecessary permissions, and unsafe external-content workflows.

The automated scan is a **first-pass review**, not a security certificate. A green result only means that no obvious findings were detected in the exact version that was scanned.

[German landing page with real-world examples](https://online-marketing49.de/skill-auditor/codex/)

## At a glance

Inventory mode can present installed Codex skills in a visual, self-contained HTML dashboard:

| Status | Meaning |
|---|---|
| 🟢 | No obvious findings in the scanned version |
| 🟡 | Findings require manual review in context |
| 🔴 | Critical finding or dangerous combination — do not use |
| 🟠 | Changed since the previous report — scan again |
| ⚪ | Not reviewed yet |

The dashboard shows each skill's name, short description, source, and path. It loads no external fonts, scripts, or CDNs and is written only when you explicitly choose an output path.

## What is a skill?

A skill is a folder containing a `SKILL.md` file with instructions for Codex. It may also ship scripts, references, configuration, and other files. Reviewing only the visible description is therefore not enough.

## What it checks

- prompt injection and forged system instructions
- network access and possible data transfer
- code execution and dynamically loaded programs
- package installation and privilege escalation
- persistent changes to `AGENTS.md`, Codex configuration, hooks, or plugins
- access to keys, passwords, and environment files
- time- or version-dependent behavior
- symlinks that lead outside the skill directory
- external web, social-media, or user-generated content
- Codex skills in user, repository, and plugin directories

## Safety principles

- The reviewed skill is never executed.
- No file is written unless you explicitly provide `--output` or `--inventory-html`.
- GitHub, marketplace, or plugin origin is provenance, not proof of safety.
- Matches inside code fences, explicit security warnings, and negative examples are shown as `CONTEXT` instead of being treated as attacks automatically.
- Dangerous combinations are checked in two stages: a precise three-line window may trigger an automatic rejection, while a wider match in the same Markdown section becomes a high-priority manual-review finding.
- External content sources trigger a manual review for indirect prompt injection.
- Reports include a content hash and, when it can be read safely, a commit SHA with provenance information.
- Files that cannot be scanned completely are listed with a reason and still contribute to the content hash.

## Requirements

- Python 3
- optional Git metadata for commit identification
- no additional Python packages

## Installation

### Install with Codex

Ask Codex:

```text
$skill-installer Install the skill from https://github.com/ki-stuff/codex-skill-auditor
```

Codex normally detects newly installed or changed skills automatically. Restart Codex once if the skill does not appear.

### Manual installation on Windows

Download the repository with **Code → Download ZIP**, extract it, and copy the folder to:

```text
C:\Users\YOUR-NAME\.agents\skills\codex-skill-auditor
```

The target directory must contain `SKILL.md` directly. See the [official Codex skill documentation](https://developers.openai.com/codex/skills) for current locations and structure.

## Use with Codex

```text
$codex-skill-auditor Review the skill at C:\path\to\external-skill before I install it.
```

Or use natural language:

```text
Review this downloaded Codex skill for security risks. Do not modify anything.
```

## Run the scanner directly

Read-only scan without saving a report:

```powershell
python .\scripts\audit.py "C:\path\to\external-skill"
```

Print machine-readable JSON to the console:

```powershell
python .\scripts\audit.py "C:\path\to\external-skill" --json
```

Write reports to an explicitly selected directory:

```powershell
python .\scripts\audit.py "C:\path\to\external-skill" --output ".\reports"
```

## Visual skill inventory

List installed skills without writing a file:

```powershell
python .\scripts\audit.py --inventory
```

Create the visual HTML dashboard at an explicitly selected path:

```powershell
python .\scripts\audit.py --inventory --inventory-html ".\reports\skill-inventory.html"
```

Use `--skills-root`, `--plugins-root`, or `--reports-dir` for custom locations and previously stored reports. Skill-controlled text is HTML-escaped before it enters the dashboard.

## Understanding the result

The scanner produces an automated **scanner verdict** first. A separate **manual overall assessment** follows only after reviewing intent, permissions, provenance, external sources, and every skipped or partially scanned file.

- 🔴 **Do not use:** at least one critical direct finding or dangerous combination
- 🟡 **Review manually:** a finding needs context and human judgment
- 🟢 **No obvious findings:** no verdict-relevant match in the scanned version
- ⚪ **Context:** documentation, code example, or explicit warning that does not affect the verdict automatically
- 🟠 **Stale:** the skill changed after the previous report and must be scanned again

A section-wide combination is deliberately classified as `HIGH`, not an automatic rejection. This makes instructions split across paragraphs or subheadings visible without treating every long document as malicious.

## Included files

```text
codex-skill-auditor/
├── SKILL.md
├── agents/openai.yaml
├── references/
│   ├── pruefverfahren.md
│   └── reportformat.md
├── scripts/
│   ├── audit.py
│   └── inventory_template.html
├── tests/test_audit.py
├── CHANGELOG.md
├── LICENSE
└── README.md
```

## Origin

Version 1 started from the MIT-licensed `ki-stuff/skill-auditor` repository at commit `f41dd61225fc056049ab0d909c3c3c442263474b`. The Codex edition is a separate development line with Codex-specific paths, safety rules, documentation, dashboard generation, and tests.

## License

MIT — see `LICENSE`.
