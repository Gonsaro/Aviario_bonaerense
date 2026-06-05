# Aviario Bonaerense — Documento de referencia v0.3

## Convenciones del modelo de datos

### Tamaños
- **chico**: hasta 20 cm
- **mediano**: 21 a 60 cm
- **grande**: más de 60 cm

### Hábitats disponibles
`urbano` · `pastizal` · `humedal` · `ribereño` · `costa` · `monte` · `bosque` · `agrícola` · `marino` · `aéreo` · `laguna`

### Residencia
`permanente` · `estival` · `invernal` · `migratorio de paso`

### Estados de conservación IUCN
`LC` · `NT` · `VU` · `EN` · `CR` · `EX`

### Convención de nombres de sprites
- `Genus_species_D.png` — default / no reproductivo
- `Genus_species_R.png` — reproductivo
- `Genus_species_M.png` — macho
- `Genus_species_F.png` — hembra
- `Genus_species_J.png` — juvenil
- `Genus_species_V.png` — vuelo

### Tamaños de sprites
- **Default / variantes posadas**: 128×128 px, fondo blanco
- **Vuelo**: 192×128 px, fondo blanco
- **Dirección**: `facing left, beak pointing left` — TODOS los sprites miran a la izquierda
- **Excepción**: estrigidos (búhos, lechuzas) → `facing forward`

### Marco para descripciones
1. Tamaño relativo (solo si aporta)
2. Cabeza — corona, cresta si hay, cara, pico, ojo. Usar **"ceja"** no "supercilio"
3. Partes superiores — dorso, alas, cola
4. Partes inferiores — garganta, pecho, vientre
5. Patas
6. Nota de sexos si difieren
- Tono accesible, ciencia ciudadana, sin tecnicismos

### Colores de hábitats (CSS)
| Hábitat | Light bg | Light text | Dark bg | Dark text |
|---|---|---|---|---|
| humedal | #E6F1FB | #0C447C | #042C53 | #B5D4F4 |
| ribereño | #E1F5EE | #085041 | #04342C | #9FE1CB |
| costa | #EEEDFE | #3C3489 | #26215C | #CECBF6 |
| pastizal | #EAF3DE | #27500A | #173404 | #C0DD97 |
| agrícola | #FAEEDA | #633806 | #412402 | #FAC775 |
| urbano | #F1EFE8 | #444441 | #2C2C2A | #D3D1C7 |
| monte | #FAECE7 | #712B13 | #4A1B0C | #F5C4B3 |
| bosque | #E8F5E0 | #1A4D0A | #0D2E04 | #A8D88A |
| aéreo | #F0EEFB | #3D2D8A | #1E1640 | #C5BCEF |
| laguna | #E6F1FB | #0C447C | #042C53 | #B5D4F4 |

---

## Estado de las 30 especies MVP

### Urbanas / muy comunes
| # | Nombre común | Nombre científico | Fichas | Sprites |
|---|---|---|---|---|
| 001 | Hornero | Furnarius rufus | ✅ | D ⚠️ mira derecha |
| 002 | Tero | Vanellus chilensis | ✅ | D ✅ |
| 003 | Cotorra | Myiopsitta monachus | ✅ | D ⚠️ mira derecha |
| 004 | Paloma doméstica | Columba livia | ⏳ | — |
| 005 | Tordo renegrido | Molothrus bonariensis | ✅ | M/F ⚠️ miran derecha |
| 006 | Zorzal colorado | Turdus rufiventris | ✅ | D ✅ |
| 007 | Gorrión | Passer domesticus | ⏳ | — |
| 008 | Benteveo | Pitangus sulphuratus | ✅ | D ✅ |
| 009 | Calandria | Mimus saturninus | ✅ | D ✅ |
| 010 | Golondrina doméstica | Progne chalybea | ✅ | M/F ⚠️ miran derecha · V ✅ |

### Acuáticas / humedal
| # | Nombre común | Nombre científico | Fichas | Sprites |
|---|---|---|---|---|
| 011 | Garza blanca | Ardea alba | ✅ | D/R/V ✅ |
| 012 | Garza mora | Ardea cocoi | ✅ | D/R ✅ |
| 013 | Martín pescador | Megaceryle torquata | ✅ | M/F ✅ |
| 014 | Macá común | Rollandia rolland | ✅ | D ✅ |
| 015 | Biguá | Nannopterum brasilianus | ✅ | D ✅ |
| 016 | Gallareta ligas rojas | Fulica armillata | ✅ | D ✅ |
| 017 | Chajá | Chauna torquata | ✅ | D ✅ |
| 018 | Pato maicero | Anas georgica | ⏳ | — |
| 019 | Jacana | Jacana jacana | ⏳ | — |
| 020 | Garza bruja | Nycticorax nycticorax | ⏳ | — |

### Rapaces
| # | Nombre común | Nombre científico | Fichas | Sprites |
|---|---|---|---|---|
| 021 | Carancho | Caracara plancus | ✅ | D/J/V ✅ |
| 022 | Chimango | Milvago chimango | ⏳ | — |
| 023 | Gavilán mixto | Parabuteo unicinctus | ⏳ | — |
| 024 | Halconcito colorado | Falco sparverius | ⏳ | — |

### Pastizal / campo
| # | Nombre común | Nombre científico | Fichas | Sprites |
|---|---|---|---|---|
| 025 | Flamenco austral | Phoenicopterus chilensis | ⏳ | — |
| 026 | Torcaza | Zenaida auriculata | ⏳ | — |
| 027 | Chiflón | Syrigma sibilatrix | ⏳ | — |
| 028 | Lechucita de las vizcacheras | Athene cunicularia | ⏳ | — facing forward |

### Costa / ribera
| # | Nombre común | Nombre científico | Fichas | Sprites |
|---|---|---|---|---|
| 029 | Gaviota capucho café | Chroicocephalus maculipennis | ⏳ | — |
| 030 | Gaviota cocinera | Larus dominicanus | ⏳ | — |

---

## Pendientes técnicos
- [ ] Script generación automática con Gemini API + normalización de escala (bounding box)
- [ ] Regenerar sprites que miran a la derecha: hornero_D, cotorra_D, tordo_M/F, golondrina_M/F
- [ ] Corregir encoding "grisáceas" en hornero y cotorra
- [ ] Automatizar provincias via GBIF API
- [ ] Automatizar estado conservación via IUCN API
- [ ] Automatizar audio_ebird_code via eBird API
- [ ] Revisar numeración según orden taxonómico de guías aviares
- [ ] Selector de orden ya implementado en HTML (num, nombre A-Z, científico A-Z)
- [ ] Lightbox con navegación entre variantes ya implementado
- [ ] Navegación entre fichas con flechas teclado ya implementado

---

## Instrucciones para retomar en nuevo chat

1. Subir `aviario_data.json` al nuevo chat
2. Subir `aviario_bonaerense.html` al nuevo chat  
3. Decirle a Claude: *"Retomamos el proyecto Aviario Bonaerense. Te adjunto el JSON de datos y el HTML actual. Lee el JSON para entender el estado del proyecto y continuamos cargando especies."*
4. El JSON contiene todo — fichas, prompts, convenciones y pendientes

