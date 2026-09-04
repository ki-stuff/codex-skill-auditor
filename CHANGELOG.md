# Änderungsverlauf

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
