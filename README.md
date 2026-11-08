# Codex Skill Auditor

Version 1.2.0. Statische Erstprüfung fremder Agent-Erweiterungen für Codex, bevor du sie installierst oder verwendest.

Geprüft werden Skill-Ordner, Einzeldateien, ZIP/MCPB/DXT/Wheel- und TAR-Archive (direkt gelesen, nie entpackt), Agent-Plugins, npm-/Python-Pakete und MCP-Konfigurationen. Der Auditor führt nichts aus und meldet Prompt Injection, Datenabfluss, Codeausführung, Persistenz und unnötige Berechtigungen.

Das Ergebnis ist eine Ampel mit konkretem nächsten Schritt:

| Farbe | Bedeutung |
|---|---|
| 🟢 | Keine offensichtlichen Befunde im geprüften Textumfang. Kein Sicherheitszertifikat. |
| 🟡 | Vor der Nutzung klären. |
| 🔴 | Nicht verwenden, bis der Befund geklärt ist. |
| ⚪ | Nicht ausreichend geprüft (fehlende Dateien, Format, Grenzen). |

Risiko, Prüfabdeckung und Aktualität werden getrennt ausgewiesen. Gelbe, graue und rote Ergebnisse erhalten je einen eigenen kopierbaren Hilfsprompt; bei Rot werden die Fundstellen im Original gelesen und eingeordnet, die rote Ampel bleibt. Jede Sitzung beginnt mit einer Umgebungsprüfung und der Frage „Was möchtest du tun?“ (prüfen, Bestandsübersicht, Hilfe zu einem Ergebnis, kurz erklären). Jedes Ergebnis endet mit „Wie geht es weiter?“ und einem Hilfsangebot. Erkannte Geheimwerte werden maskiert, Rohbelege zurückgehalten. Ein Warnwort wie „never“ vor einer gefährlichen Anweisung hebt den Befund nicht auf.

Auf Wunsch erstellt der Auditor ein Inventar der installierten Codex Skills, auch als HTML-Dashboard mit Kacheln nach Themen und Filter nach Ergebnis. Die Themen vergibt die KI passend zum Bestand (`--categories`); `--render-inventory` stellt eine gespeicherte Bestandsdatei ohne neuen Scan dar. Berichte entstehen nur an einem ausdrücklich gewählten neuen Ziel außerhalb der geprüften Ordner.

**Voraussetzung:** Python ab 3.11, nur Standardbibliothek, keine automatische Nachinstallation.

**Installation:** Den **kompletten** Ordner `codex-skill-auditor` nach `~/.agents/skills/` kopieren (Windows: `%USERPROFILE%\.agents\skills\`) und in einem neuen Codex-Chat `$codex-skill-auditor` aufrufen. Nie nur die `SKILL.md` übernehmen: Ohne `scripts/` und `references/` meldet der Auditor „Installation unvollständig“.

**Welches Modell?** Die Ampel ermittelt der Python-Scanner, unabhängig vom Modell. Das Modell bestimmt, wie gut Ergebnisse erklärt, Themen vergeben und Befunde eingeordnet werden. Empfehlung (Stand November 2026): für Einzelprüfungen ein aktuelles Modell der mittleren Klasse, für Bestandsübersicht und rote Befunde das stärkste verfügbare Modell mit erhöhter Denktiefe. Ein schwächeres Modell ändert keine Ampel.

**Update von 1.0.x:**

1. `python --version` prüfen: Version 1.1 braucht **Python ab 3.11**. Mit älterem Python meldet der Auditor nur „Python ab 3.11 erforderlich“.
2. Den alten Ordner `~/.agents/skills/codex-skill-auditor` außerhalb des Skill-Verzeichnisses sichern, entfernen und den neuen Ordner hineinkopieren, nicht darüberkopieren. Danach Codex neu starten.
3. Berichte entstehen nur noch an einem ausdrücklich gewählten Ziel (`--output`, `--html`, `--inventory-html`), nie im geprüften Ordner. Eine `audit-result.json` früherer Fassungen in Skill-Ordnern wird erkannt und nicht als Skill-Inhalt gewertet; meldete sie Rot, erscheint der Skill als unbestätigte Warnung aus einem früheren Bericht. Fundstellen prüfen und die alte Datei danach löschen.

Einstieg: [SKILL.md](SKILL.md), [Prüfverfahren](references/edition-workflow.md), [Hilfe bei Befunden](references/hilfe-bei-befunden.md). `BUNDLE.json` listet die Datei-Hashes des Pakets. Schwesterfassung für Claude (Claude Code, Claude Desktop, claude.ai und Cowork): [skill-auditor](https://github.com/ki-stuff/skill-auditor).

## English

Version 1.2.0. Static first-pass review of skills, agent plugins, packages and MCP configurations for Codex, before you install or use them. Archives are read directly, nothing is extracted or executed. Results show risk, coverage and freshness separately, with concrete next steps and a copyable help prompt for yellow, grey and red. Each session starts with an environment check and one question; each result ends with an offer to help. Optional inventory and HTML dashboard of installed Codex skills. Requires Python 3.11+ (standard library only). Install by copying the complete `codex-skill-auditor` folder into `~/.agents/skills/`, never just `SKILL.md`. A clean result is not a security certificate.
