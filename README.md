# Codex Skill Auditor

Version 1.1.0. Statische Erstprüfung fremder Agent-Erweiterungen für Codex, bevor du sie installierst oder verwendest.

Geprüft werden Skill-Ordner, Einzeldateien, ZIP/MCPB/DXT/Wheel- und TAR-Archive (direkt gelesen, nie entpackt), Agent-Plugins, npm-/Python-Pakete und MCP-Konfigurationen. Der Auditor führt nichts aus und meldet Prompt Injection, Datenabfluss, Codeausführung, Persistenz und unnötige Berechtigungen.

Das Ergebnis ist eine Ampel mit konkretem nächsten Schritt:

| Farbe | Bedeutung |
|---|---|
| 🟢 | Keine offensichtlichen Befunde im geprüften Textumfang. Kein Sicherheitszertifikat. |
| 🟡 | Vor der Nutzung klären. |
| 🔴 | Nicht verwenden, bis der Befund geklärt ist. |
| ⚪ | Nicht ausreichend geprüft (fehlende Dateien, Format, Grenzen). |

Risiko, Prüfabdeckung und Aktualität werden getrennt ausgewiesen. Gelbe und graue Ergebnisse erhalten einen kopierbaren Hilfsprompt. Erkannte Geheimwerte werden maskiert, Rohbelege zurückgehalten. Ein Warnwort wie „never“ vor einer gefährlichen Anweisung hebt den Befund nicht auf.

Auf Wunsch erstellt der Auditor ein Inventar der installierten Codex Skills, auch als HTML-Dashboard mit Kacheln nach Themen und Filter nach Ergebnis. Die Themen vergibt die KI passend zum Bestand (`--categories`); `--render-inventory` stellt eine gespeicherte Bestandsdatei ohne neuen Scan dar. Berichte entstehen nur an einem ausdrücklich gewählten neuen Ziel außerhalb der geprüften Ordner.

**Voraussetzung:** Python ab 3.11, nur Standardbibliothek, keine automatische Nachinstallation.

**Installation:** Den Ordner `codex-skill-auditor` nach `~/.agents/skills/` kopieren (Windows: `%USERPROFILE%\.agents\skills\`) und in einem neuen Codex-Chat `$codex-skill-auditor` aufrufen.

Einstieg: [SKILL.md](SKILL.md), [Prüfverfahren](references/edition-workflow.md), [Hilfe bei Befunden](references/hilfe-bei-befunden.md). `BUNDLE.json` listet die Datei-Hashes des Pakets. Schwesterfassungen: [skill-auditor](https://github.com/ki-stuff/skill-auditor) für Claude Code, [skill-auditor-desktop](https://github.com/ki-stuff/skill-auditor-desktop) für Claude Desktop und claude.ai.

## English

Version 1.1.0. Static first-pass review of skills, agent plugins, packages and MCP configurations for Codex, before you install or use them. Archives are read directly, nothing is extracted or executed. Results show risk, coverage and freshness separately, with concrete next steps and a copyable help prompt. Optional inventory and HTML dashboard of installed Codex skills. Requires Python 3.11+ (standard library only). Install by copying `codex-skill-auditor` into `~/.agents/skills/`. A clean result is not a security certificate.
