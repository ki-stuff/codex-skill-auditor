# Reportformat

```markdown
## Skill-Audit: [Name]

**Geprüfter Stand:** [Inhalts-Hash]
**Commit-SHA:** [SHA oder nicht verfügbar]
**Quelle:** [URL, Plugin, lokaler Ordner oder unbekannt]
**Scanner-Rohurteil:** 🔴 Nicht verwenden | 🟡 Manuell prüfen | 🟢 Keine offensichtlichen Befunde
**Gesamtbewertung nach manueller Prüfung:** 🔴 Nicht verwenden | 🟡 Mit Anpassungen verwenden | 🟢 Verwenden

### Befunde

| Nr. | Risiko | Kategorie | Datei:Zeile | Einordnung |
|---:|---|---|---|---|

Treffer mit Risiko `CONTEXT` stammen aus Codeblöcken. Erkläre, ob der umgebende Text sie rein dokumentiert oder ihre Ausführung verlangt.

Ein Befund „Gefährliche Musterkombination im selben Markdown-Abschnitt“ ist ein hoher manueller Prüfhinweis, aber kein automatischer `REJECT`. Prüfe, ob die Fundstellen tatsächlich einen zusammenhängenden Ablauf beschreiben oder nur fachlich verwandte Begriffe dokumentieren.

### Nicht oder nur teilweise automatisch geprüfte Dateien

| Datei | Grund | Manuell geprüft |
|---|---|---|

### Berechtigungsumfang

- Lesen: [...]
- Schreiben: [...]
- Ausführen: [...]
- Netzwerk: [...]
- Externe Systeme: [...]
- Fremdinhalte: keine | lokal bereitgestellt | Web/Social Media | unklar
- Risiko indirekter Prompt-Injection: niedrig | mittel | hoch | nicht verifiziert
- Scope: minimal | vertretbar | übermäßig | gefährlich

### Nicht oder nur teilweise verifiziert

- [...]

### Empfehlung

[Verwenden | Mit Anpassungen verwenden | Nicht verwenden]

[Kurze Begründung und nächster sicherer Schritt]
```

Ein leerer automatischer Scan darf nur als „keine offensichtlichen Befunde im geprüften Stand“ bezeichnet werden. Das Scanner-Rohurteil ist nicht die manuelle Gesamtbewertung. Der Report ist eine Erstprüfung und kein Sicherheitszertifikat.
