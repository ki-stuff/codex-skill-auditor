# Prüfverfahren

## 0. Auftrag und Herkunft

- Was soll der Skill laut Name, Beschreibung und README tun?
- Welche Quelle, welcher Autor und welcher Commit oder Downloadstand werden geprüft?
- Stimmen Repository, Lizenz, Änderungsverlauf und tatsächlicher Ordnerinhalt überein?
- Marketplace-, Plattform- und Plugin-Status sind Herkunftssignale, keine Sicherheitsfreigaben.
- Vergleiche bei fremden Audit-Badges deren Commit, Datum oder Inhalts-Hash mit dem tatsächlich heruntergeladenen Stand. Ein Pass für einen älteren Commit ist kein Pass für den aktuellen Inhalt.

## 1. Dateiinventar

Erfasse mindestens:

- `SKILL.md` und weitere Markdown-Anweisungen,
- Skripte und ausführbare Dateien,
- `agents/openai.yaml`, `.codex-plugin/plugin.json` und Konfigurationsdateien,
- Referenzen und Assets mit aktiven Inhalten,
- Symlinks und deren tatsächliche Ziele,
- externe URLs, Downloads, Pakete und Binärdateien.

Melde nicht lesbare, ungewöhnlich große oder binäre Dateien als nicht geprüft.

## 2. Automatischer Musterscan

Der Scanner unterscheidet:

- `CRITICAL`: direkt hochkritisches Muster oder gefährliche Kombination,
- `HIGH`: hohes Missbrauchspotenzial; Kontextprüfung zwingend,
- `MEDIUM`: auffällig und erklärungsbedürftig,
- `CONTEXT`: Treffer in einem Markdown-Codeblock außerhalb der `SKILL.md`; kein automatisches Urteil.
- Treffer in Codeblöcken der `SKILL.md` oder neben Warnwörtern („never“, „do not“, „vermeiden“ …) werden höchstens auf `MEDIUM` gesenkt, also Gelb, nie Grün. Steht das Warnwort nur in den Zeilen davor, bleibt eine gefährliche Kombination ein automatisches `REJECT`. Warnwörter sind leicht einzufügen und daher kein Harmlosigkeitsbeleg.

Eine Reject-Kombination ist stärker als ein Einzelmuster, etwa Geheimniszugriff und Netzwerkübertragung in einem lokalen Block von höchstens drei Zeilen. Diese zeilennahe Stufe ist auf hohe Präzision ausgelegt.

Zusätzlich prüft der Scanner Markdown-Abschnitte einschließlich ihrer Unterabschnitte. So bleiben Kombinationen sichtbar, die durch Leerzeilen, mehrere Absätze oder untergeordnete Überschriften getrennt wurden. Wegen des größeren Kontexts werden diese Treffer als `HIGH` zur manuellen Prüfung gemeldet, nicht automatisch als `REJECT`. Benachbarte Hauptabschnitte werden dabei nicht verbunden. Prüfe immer die echte Fundstelle, nicht nur den Musternamen.

## 3. Codex-Konfiguration

Prüfe, ob der Skill:

- `AGENTS.md` oder andere dauerhafte Anweisungen verändern will,
- `~/.codex/config.toml` oder Repository-Konfigurationen schreibt,
- implizite Aktivierung ungewöhnlich breit definiert,
- MCP-Server, Hooks oder Plugins hinzufügt oder verändert,
- zusätzliche Berechtigungen oder externe Dienste benötigt,
- außerhalb seines eigenen Ordners schreibt,
- sich selbst oder weitere Komponenten aus dem Netz aktualisiert.

## 4. Manuelle Inhaltsprüfung

- Entspricht das tatsächliche Verhalten der Beschreibung?
- Enthält der Text Rollenwechsel, falsche Systemmeldungen oder Umgehungsrhetorik?
- Werden Codeblöcke nur erklärt oder soll Codex sie später ausführen?
- Gibt es bedingtes, zeitgesteuertes oder während der Prüfung abweichendes Verhalten?
- Werden Daten, Prompts, Dateiinhalte oder Anmeldedaten an Dritte übertragen?
- Werden fremde Webseiten-, Social-Media- oder Nutzerdaten als Inhalt eingelesen? Behandle sie als untrusted input und prüfe das Risiko indirekter Prompt-Injection.
- Sind Fehlerbehandlung und Logging frei von Geheimnissen?

## 5. Berechtigungsumfang

Ordne jeden Zugriff zu:

- Lesen: welche Dateien und Verzeichnisse?
- Schreiben: wohin und warum?
- Ausführen: welche Befehle oder Skripte?
- Netzwerk: welche Domains und Daten?
- Externe Systeme: welche Konten, MCPs oder Plugins?

Bewerte den Umfang als `minimal`, `vertretbar`, `übermäßig` oder `gefährlich`.

## 6. Aktualität

Vergleiche `content_hash` und, falls vorhanden, `source_commit`. Stimmt der aktuelle Inhalt nicht mehr mit dem Report überein, ist der frühere Befund veraltet und darf nicht übernommen werden.

## 7. Entscheidung

- Rot: nicht verwenden, solange kritische Befunde nicht nachvollziehbar behoben sind.
- Gelb: nur nach manueller Klärung beziehungsweise mit Anpassungen verwenden.
- Grün: keine offensichtlichen Befunde im geprüften Stand; verbleibende Grenzen ausdrücklich nennen.
