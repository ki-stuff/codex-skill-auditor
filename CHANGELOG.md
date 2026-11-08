# Änderungsverlauf

## 1.1.0 – 2026-11-08

### Gemeinsamer Kern, sichere Auswertung

- **Gemeinsamer Scanner-Kern 1.1.0** für Codex, Claude Code und Claude Desktop. Neben Skill-Ordnern werden jetzt auch Einzeldateien, ZIP/MCPB/DXT/Wheel- und TAR-Archive (direkt gelesen, nie entpackt), Agent-Plugins, npm-/Python-Pakete und MCP-Konfigurationen statisch geprüft.
- **Getrennte Aussagen:** Risiko, Prüfabdeckung (was wurde tatsächlich gelesen) und Aktualität werden einzeln ausgewiesen. Grau bedeutet „nicht ausreichend geprüft“ und wird nie zu Grün.
- **Konkrete nächste Schritte** und ein kopierbarer Hilfsprompt für gelbe und graue Ergebnisse.
- **HTML-Auswertung** mit Überblick, Kennzahlen, „Hier solltest du zuerst hinsehen“ und aufklappbaren technischen Details. Passives HTML ohne Skripte und ohne externe Ressourcen.
- **Schutz beim Lesen:** Größen-, Zeit- und Speichergrenzen, keine Links/Reparse-Punkte, keine Ausführung von Prüfobjektcode. Erkannte Geheimwerte werden in Berichten maskiert, Rohbelege zurückgehalten.
- **Keine automatische Ablage mehr im geprüften Skill:** Berichte entstehen nur noch an einem ausdrücklich gewählten neuen Ziel (`--output`, `--html`, `--inventory-html`).
- **Warnwörter sind kein Freifahrtschein:** Steht vor einer gefährlichen Anweisung ein Satz mit „never“, „avoid“ oder „do not“, bleibt eine gefährliche Musterkombination ein automatisches Rot. Treffer neben Warnwörtern oder in Codeblöcken der SKILL.md werden höchstens auf Gelb gesenkt, nie auf Grün. Codeblöcke in README und Referenzen bleiben reiner Dokumentationskontext.
- **Altberichte:** Eine `audit-result.json` früherer Fassungen im Skill-Ordner wird am exakten Format erkannt, als Ausnahme ausgewiesen und nicht mehr als Skill-Inhalt gescannt. Vorher verursachten ihre alten Fundstellen-Auszüge falsche Treffer und graue Abdeckung. Verweist eine andere Datei des Skills auf die `audit-result.json`, wird sie trotzdem vollständig geprüft, damit sich darin keine Anweisung verstecken lässt.
- **Verweise auf Codebeispiele:** Eine gefährliche Musterkombination in einem Codeblock von README oder Referenzdateien wird gelb, sobald eine andere Datei auf diese Datei verweist (z. B. „folge dem Setup in README.md“). Ohne Verweis bleibt sie Dokumentationskontext. In der SKILL.md selbst ist eine solche Kombination immer mindestens gelb.
- **Inventar robuster:** Die Maskierung arbeitet pro Skill. Erreicht ein einzelner Skill die Grenze, wird nur dieser Eintrag zurückgehalten, statt das ganze Inventar abzubrechen. Das Ausgabeziel wird vor dem Scan geprüft, Fehlermeldungen nennen den Grund im Klartext.
- Python ab 3.11 erforderlich, nur Standardbibliothek, keine automatische Nachinstallation.
- **Codex-Profile** für Kommandozeile, App und IDE (`--surface`). Das Profil dokumentiert den Kontext, beweist aber keine App-Rechte.

## 1.0.3 – 2026-09-04

### Visuelles Skill-Inventar für Menschen

- Der Inventar-Modus kann mit `--inventory-html <ziel>` ein selbstenthaltenes HTML-Dashboard erzeugen.
- Das Dashboard gruppiert Skills nach Prüfstatus und zeigt Kurzbeschreibung, Herkunft, Pfad und den zugehörigen Statuspunkt.
- Die Legende unterscheidet 🟢 keine offensichtlichen Befunde, 🟡 manuell prüfen, 🔴 nicht verwenden, 🟠 veraltet und ⚪ nicht geprüft.
- Namen, Beschreibungen, Quellen und Pfade aus fremden Skills werden vor der HTML-Ausgabe escaped.
- Die Vorlage verweist nicht mehr fälschlich auf Claude und wird jetzt direkt vom Scanner befüllt.
- Ohne ausdrücklich gewähltes HTML-Ziel bleibt der Inventar-Modus read-only.
- Die README ist vollständig zweisprachig aufgebaut: Deutsch zuerst, Englisch darunter. Beide Fassungen erklären das visuelle Inventar und seine fünf Statuspunkte.
- Ein neuer Regressionstest prüft Platzhalterersetzung, HTML-Escaping, Statusdarstellung und Dateiausgabe. Die Testsuite umfasst damit 21 Tests.

## 1.0.2 – 2026-09-04

### Umgehung über größere Abstände erschwert

- Die präzise Erkennung gefährlicher Kombinationen in höchstens drei zusammenhängenden Zeilen bleibt erhalten und erzeugt weiterhin einen automatischen Ablehnungsbefund.
- Zusätzlich werden Kombinationen innerhalb desselben Markdown-Abschnitts erkannt, auch wenn Leerzeilen, mehrere Absätze oder untergeordnete Überschriften dazwischenliegen.
- Abschnittsweite Treffer werden wegen ihres größeren Kontextes als `HIGH` zur manuellen Prüfung gemeldet, nicht automatisch als `REJECT`.
- Benachbarte Hauptabschnitte werden nicht miteinander kombiniert.
- Vier neue Regressionstests decken verteilte Anweisungen, Unterüberschriften, getrennte Hauptabschnitte und dokumentierte Negativbeispiele ab.
- Die Testsuite umfasst damit 20 Tests. Sie ist eine Regression-Basis und kein Nachweis vollständiger Erkennung.

## 1.0.1 – 2026-09-03

### Aus realen Praxistests gelernt

- `security-best-practices` aus `openai/skills`: V1.0.0 meldete bei 13 reinen Dokumentationsdateien 177 Treffer und ein rotes Scanner-Rohurteil. Die manuelle Prüfung zeigte, dass Sicherheitsbegriffe und Negativbeispiele über lange Dateien hinweg fälschlich kombiniert wurden.
- `brand-voice` aus `affaan-m/ECC` über `skills.sh`: V1.0.0 meldete grün und keine Treffer. Die manuelle Prüfung erkannte dennoch das Einlesen öffentlicher X- und Webseiteninhalte als Risiko für indirekte Prompt-Injection. Auf `skills.sh` bewerteten zwei Dienste den Skill mit „Pass“, Snyk dagegen mit „Medium“.
- Mindestens ein auf `skills.sh` sichtbarer Audit bezog sich auf einen anderen Commit als der aktuell geprüfte Download. Audit-Badges gelten daher nur zusammen mit einem passenden Inhaltsstand.

### Verbessert

- Gefährliche Musterkombinationen werden nur noch in einem lokalen Block von höchstens drei Zeilen gebildet, nicht mehr über eine komplette Datei hinweg.
- Ausdrückliche Sicherheitswarnungen und Negativbeispiele in Markdown werden als nicht automatisch wertender `CONTEXT` gekennzeichnet.
- Neue Kategorie `L_EXTERNAL_CONTENT` für externe Social-Media-, Web- und nutzergenerierte Inhalte sowie das Risiko indirekter Prompt-Injection.
- Prüfverfahren und Reportformat um Versionsvergleich fremder Audit-Badges und Fremdinhaltsrisiken ergänzt.

## 1.0.0 – 2026-09-03

- Erste eigenständige Codex-Version auf Basis des Skill-Auditors 2.4.
- Codex-Skill-, Repository- und Plugin-Verzeichnisse ergänzt.
- Standardlauf vollständig read-only; Schreiben nur mit `--output`.
- Inhalts-Hash und optionale Commit-SHA in Reports aufgenommen.
- Veraltete Reports nach Inhaltsänderungen erkennbar.
- Plugin-Herkunft vom Sicherheitsstatus getrennt.
- Treffer in Markdown-Codeblöcken als nicht wertender Kontext klassifiziert.
- Prüfung externer Symlink-Ziele ergänzt.
- Deutsche Skill-Anweisungen, Metadaten und Dokumentation ergänzt.
- Scanner-Rohurteil und manuelle Gesamtbewertung klar getrennt.
- Nicht oder nur teilweise geprüfte Dateien werden samt Grund ausgewiesen und mitgehasht.
- Commit-Ermittlung ohne Ausführung der Git-CLI; Herkunft und Ausfallgrund werden dokumentiert.
- `scanner_base_commit` eindeutig vom `source_commit` des Prüfobjekts getrennt.

Ausgangsstand: `ki-stuff/skill-auditor`, Commit `f41dd61225fc056049ab0d909c3c3c442263474b`.
