# AI

## Best practices
- Používejte postupné odhalování: místo zahrnutí všech pokynů vytvořte stručný index odkazující na další soubory markdown v .claude/docs/ pro specializovaná témata.
- Důležité:  když pracujete na nové funkci nebo chybě, nejprve vytvořte git braanch. Poté pracujte na změnách v této větvi po zbytek relace
- prozkoumejte, naplánujte, naprogramujte, potvrďte

**Prompty**
- Ptejte se mě na otázky, abyste si ujasnili požadavky na produkt, technické požadavky, technické principy a tvrdá omezení.



## Claude

- <key>Shift+tab</key> - vždy se přepnout do plánovacího režimu! = musí se zamyslet, než aby chrlil nesmysly.

**CLAUDE.md**

CLAUDE.md - persistentní instrukce, umisťuje se do repozitáře. Uvedeny základy projektu, technologie. Velikost na 1-2 stránky.
- popis business projektu pro identifikaci cílů a kontextu
- odkazy na zdroje 
- popis jak spouštět testy např. pro docker
- postup práce např. jak commitovat - jaké jsou naše představy
- `/init` - jak se inicializuje projekt pro vytvoření claude.md
- `Write phased plan to file PLAN.md` - vždy rozdělovat na fáze
  - protože čím je konverzace delší, tím výrazně klesá kvalita výstupu
  - pokud je kontext zaplněn je vhodné spustit příkaz `/clear`
  - míru zaplnění přidat do cli - https://gist.github.com/benabraham/dfa45406d7472827b75d16fed4d8e39c

**New app Prompt**
```
Make a chore app to manage chores at the office. It should
  - Show a calendar view like Outlook to see all our current chores
  - Allow adding/removing chores
  - Be able to make chores recurring on a schedule
  - Assign chores to team members
  - Add/remove team members

Ask me questions to clarify the product requirements, technical requirements, engineering principles, and hard constraints.
```
**Claude.md prompt**
```
Analyze this codebase and create a CLAUDE.md file following these principles:

1. Keep it under 150 lines total - focus only on universally applicable information
2. Cover the essentials: WHAT (tech stack, project structure), WHY (purpose), and HOW (build/test commands)
3. Use Progressive Disclosure: instead of including all instructions, create a brief index pointing to other markdown files in .claude/docs/ for specialized topics
4. Include file:line references instead of code snippets
5. Assume I'll use linters for code style - don't include formatting guidelines

Structure it as: project overview, tech stack, key directories/their purposes, essential build/test commands, and a list of additional documentation files Claude should check when relevant.

Additionally, extract patterns you observe into separate files:
- .claude/docs/architectural_patterns.md - document the architectural patterns, design decisions, and conventions used (e.g., dependency injection, state management, API design patterns). Make sure these are patterns that appear in multiple files.

Reference these files in the CLAUDE.md's "Additional Documentation" section.
```


**Bux fix**
```
Bug fix: when the user clicks on the calendar in weekly view to add a new chore, the time of the new chore doesn’t reflect the cell the user clicked.
```

Architecture Changes
```
Architecture change: Chore changes (add chore, remove chore, change chore) should sync in real time to other clients. For example, if we make the change on one browser it should happen on all other tabs. Read the files related to calendar display to determine 3 options to move forward.
```



## Zdroje
- [Claude Code: Best practices for agentic coding](https://www.anthropic.com/engineering/claude-code-best-practices)
- [Writing a good CLAUDE.md](https://www.humanlayer.dev/blog/writing-a-good-claude-md)

