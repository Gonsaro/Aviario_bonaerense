# Project Instructions for AI Agents

This file provides instructions and context for AI coding agents working on this project.

<!-- BEGIN BEADS INTEGRATION v:1 profile:minimal hash:7510c1e2 -->
## Beads Issue Tracker

This project uses **bd (beads)** for issue tracking. Run `bd prime` to see full workflow context and commands.

### Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work
bd close <id>         # Complete work
```

### Rules

- Use `bd` for ALL task tracking — do NOT use TodoWrite, TaskCreate, or markdown TODO lists
- Run `bd prime` for detailed command reference and session close protocol
- Use `bd remember` for persistent knowledge — do NOT use MEMORY.md files

**Architecture in one line:** issues live in a local Dolt DB; sync uses `refs/dolt/data` on your git remote; `.beads/issues.jsonl` is a passive export. See https://github.com/gastownhall/beads/blob/main/docs/SYNC_CONCEPTS.md for details and anti-patterns.

## Session Completion

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds
<!-- END BEADS INTEGRATION -->


## Build & Test

```bash
python build_html.py   # Regenera index.html desde aviario_data.json
```

## Architecture Overview

PWA estática (un solo `index.html`) deployada en GitHub Pages. Sin backend ni framework — JavaScript vanilla. Datos en `aviario_data.json` (fuente de verdad); `index.html` contiene una copia hardcodeada generada por `build_html.py`.

## Conventions & Patterns

### Workflow obligatorio para cambios de datos

**NUNCA editar `index.html` a mano para cambiar datos de especies, sprites o el mapa SP.**
El flujo correcto es:

1. Editar `aviario_data.json`
2. Ejecutar `python build_html.py`
3. Bumppear `const CACHE = 'aviario-vN'` en `sw.js` (incrementar N)
4. Verificar, commitear y pushear

Editar `index.html` directamente causó bugs graves (SP map mal cerrado → pantalla en blanco).

### Sprites

- Generación: `python generar_sprites.py -s <id|nombre|num>`
- Salida: `Sprites/Genus_species_VARIANTE.png`, 1024×1024 px (vuelo: 1536×1024)
- Orientación: todos facing LEFT — excepción: estrigidos (#027 Athene, #028 Asio) facing FORWARD
- Después de agregar sprites nuevos: correr `build_html.py` para que el mapa SP se actualice solo

### Nomenclatura

Sigue `lista_especies_aves_argentinas_oficial.md` (lista Monteleone & Pagano 2022).
