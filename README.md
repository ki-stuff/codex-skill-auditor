# Codex Skill Auditor

Version 1.0.2

Der Codex Skill Auditor prüft fremde oder unbekannte Agent-Skills, bevor du sie installierst oder verwendest. Er sucht nach auffälligen Mustern wie Prompt Injection, Datenabfluss, versteckter Codeausführung und dauerhaften Änderungen an deiner Codex-Konfiguration.

Der automatische Scan ist eine **Erstprüfung**, kein Sicherheitszertifikat. Ein grünes Ergebnis bedeutet ausschließlich: Im exakt geprüften Stand wurden keine offensichtlichen Befunde erkannt.

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
