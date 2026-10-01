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
- Después de agregar sprites nuevos: correr `build_html.py` para que el mapa SP se actualice solo
- Modo recolor (image-to-image): `python generar_sprites.py -s <especie> -v <V> --base-image Sprites/base.png --overwrite`

### Convenciones para prompts de sprites

Aplicar SIEMPRE que se genere o edite un `prompts_pixelart`.

**§0 Validar antes de escribir**
Verificar rasgos antes de describir colores de ojo, pico, patas o patrones de pluma. No inventar de memoria. Si un dato no se pudo confirmar, marcarlo como pendiente (campo `pendientes` de la ficha).

**Rasgos (plumaje, iris, pico, patas, medidas): manda la UNL.**
1. **Aves de Argentina — FCV-UNL** (https://www.fcv.unl.edu.ar/aves/). Índice por familia en `/aves/familia-de-aves/`; fichas en `/aves/categorias/<familia>/<nombre-comun-con-guiones>/` (ej. `/aves/categorias/cuculidae/pirincho/`). Describe las aves de Argentina: si la UNL dice algo, es el dato válido aunque otra fuente diga distinto (las fuentes globales pueden describir otras subespecies o poblaciones). No es pendiente: se usa la UNL y listo.
2. Solo para lo que la UNL no dice: oiseaux-birds.com (`/card-<english-name>.html`, basado en HBW), avespampa.com.ar, Wikipedia (en/es), Birds of the World. Si estas se contradicen entre sí y la UNL no lo dice, va a `pendientes`.
3. Avibase (https://avibase.bsc-eoc.org) da 403 desde la nube y desde la PC local: no reintentar.

**Distribución por provincia: mandan los registros, no la UNL.** Usar GBIF, que incluye eBird e iNaturalist: `https://api.gbif.org/v1/occurrence/search?country=AR&limit=0&facet=stateProvince&facetLimit=200&scientificName=<Genus%20species>` (normalizar variantes de nombre de provincia, ej. "Ciudad Autónoma de Buenos Aires" → CABA). 20 o más registros = presencia (se carga); menos de 20 = no se carga, y no es pendiente. Solo van a `pendientes` los sospechosos de escapes o criaderos. La distribución de la UNL no se usa para decidir.

**Residencia en Buenos Aires: mandan los registros GBIF por mes.** Facet `month` con `stateProvince` = Buenos Aires, Ciudad Autónoma de Buenos Aires y Ciudad de Buenos Aires. Normalizar cada mes contra el Benteveo (*Pitangus sulphuratus*, taxonKey 2482755), porque en verano se observa más. Si el índice promedio de jun–ago es menor al 30% del de dic–feb: `estival`; si es más del triple: `invernal`; si no: `permanente`. No es pendiente.

**Envergadura:** solo con dato de la UNL o de Birds of the World. Si no, `null`, y no es pendiente.

**Nomenclatura:** manda la lista oficial (ver Nomenclatura); no se anotan como pendiente las diferencias con GBIF.

**Estado de conservación:** categoría global de la UICN (iucnredlist.org). La categoría nacional no se usa.

**Variantes y rasgos:** se crea una variante F, J o R solo si cambia algo visible a 128 px (color de cabeza, pecho u ojo, o patrón general). Si no, el rasgo se menciona en la descripción y no es pendiente. Lo mismo para rasgos que no se ven en el sprite (coronas escondidas, cara inferior del ala): van en la descripción.

**§1 Solo rasgos visuales**
El prompt contiene únicamente color, forma, posición, contraste, textura. Prohibido: `from a distance`, `striking in flight`, `visible when perched`, `unmistakable`, `typical of the species`. No usar comparaciones de especie (`NOT a wren`) salvo como parche documentado cuando una tirada falla repetidamente en algo concreto.

**§2 Estructura fija**
```
pixel art bird sprite, side profile, bird facing LEFT (beak pointing to the LEFT side of canvas), <pose>, white background, 1024x1024 pixels, bird filling <X>% of canvas height, <plumaje: cabeza→dorso/alas/cola→pecho/vientre→patas>, detailed feather texture with dithering, clean outline, no shadow, no text — IMPORTANT: bird must face LEFT, mirror horizontally if facing right
```
NO usar el formato verboso viejo (`strict left-facing side profile, body pointing left, head pointing left, beak pointing left — bird right side visible`).

**§3 Orientación**
Todas las aves: `bird facing LEFT`. Excepción: estrígidos → `facing forward` (el cierre se adapta).

**§4 Encuadre**
- Default posado: `bird filling 65% of canvas height`
- Ave muy compacta o chica: ~60%
- Cola larga (loros, etc.): `bird including its long tail filling about 75% of canvas width`
- El script recorta al bounding box del ave y centra; el encuadre/padding se resuelve ahí, no peleándole al prompt.

**§5 Orden del plumaje**
Cabeza (corona/cresta → cara → pico → ojo) → partes superiores (dorso → alas → cola) → partes inferiores (garganta → pecho → vientre) → patas. Usar "ceja", no "supercilio".

**§6 Realidades del pixel (128px efectivos)**
- Anillos orbitales finos → omitir. Para el ojo: `small <color> eye with a tiny dark pupil`.
- Moteados difusos no se ven → pedirlos como puntos discretos: `peppered with small distinct dark spots`, NO `diffuse spotting`.
- No apilar instrucciones que compitan. Si dos marcas similares coexisten, secuenciarlas en una frase.

**§7 Variantes**
- D=adulto · R=reproductivo · M=macho · F=hembra · O=morfo oscuro · J=juvenil · V=vuelo
- O (morfo oscuro/melánico): solo si el morfo es muy distinto y se ve en Buenos Aires (ej. Gavilán Planeador casi todo negro). Se hace como recolor §8 del sprite base.
- Hembra/juvenil más apagado: decirlo explícito (`female darker and duskier than the male`)
- Vuelo: `in flight with wings raised mid-flap`, mostrar patrón ala abierta, cuello extendido, patas recogidas
- Orden por convención: dimorfismo sexual → macho primero, hembra después; variabilidad por edad → adulto primero, juvenil después. El orden se decide sobre la marcha según el caso.

**§8 Recolor para sprites de igual estructura**
Usar image-to-image cuando el sujeto a generar comparte la misma estructura con un sprite ya existente: misma especie (otra variante), mismo género, o familia de porte idéntico. El recolor conserva pose y tamaño sin costo extra de generación.
```
recolor this exact sprite, keep the same pose, outline, size and composition unchanged, only change the colors: <cambios concretos>, keep white background, no shadow, no text
```
Cuando la base no es obvia (otra especie u otra variante), se anota en el campo `recolor_base` de la ficha: `{"<variante>": "<archivo base en Sprites/>"}`, ej. Tordo Pico Corto J → `Agelaioides_badius_D.png`. Se pasa con `--base-image Sprites/<archivo>`.
El modo edición también tolera cambios chicos de forma sobre la misma especie si se piden explícitamente (ej. Tijerita J: recolor de la D pidiendo "shorten the tail… remove the long outer streamers" funcionó). Los backups de sprites reemplazados van en `Sprites/backup/` (el build no los toma).
No es una regla de "llamativo vs apagado" — es una regla de estructura compartida. No aplica si difieren proporciones, largo de cola, forma de pico o postura.

### Nomenclatura

Sigue `lista_especies_aves_argentinas_oficial.md` (lista Monteleone & Pagano 2022).

### Orden de las especies

- La app muestra las especies en el orden de la lista oficial (N° de `lista_especies_aves_argentinas_oficial.md`). `build_html.py` ordena y calcula el número visible (`num` = posición correlativa #001, #002…) y `n_lista`; el `num` de `aviario_data.json` no se usa para mostrar.
- El `id` es fijo y nunca se renumera (el historial `aviario_seen` en localStorage depende de él). Las especies nuevas se agregan al final del array con id max+1; el orden lo resuelve el build.
- Toda especie nueva debe estar en la lista oficial (si no, el build falla).
