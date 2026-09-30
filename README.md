# Výuková galerie – Python + GitHub Pages

Statický generátor fotogalerie pro dokumentaci výuky. Obsah se spravuje pouze přes adresáře v `topics/` a GitHub Actions po `git push` automaticky vytvoří web v `_site/` a publikuje ho na GitHub Pages.

## Struktura tématu

```text
topics/2026-10-01-zlomky/
├── index.md
├── 001.jpg
├── 002.jpg
└── 003.jpg
```

`index.md`:

```yaml
---
title: Zlomky
date: 2026-10-01
subject: Matematika
class: 7.A
description: Sčítání a odčítání zlomků
cover: 001.jpg
hidden_images:
  - 003.jpg
---

## Cíl hodiny

Text tématu může obsahovat běžný **Markdown**, seznamy, tabulky a další prvky.
```

### Co generátor dělá

- vytvoří úvodní stránku se seznamem témat a thumbnails,
- řadí témata podle `date` sestupně,
- pro každé téma vytvoří samostatnou stránku,
- automaticky vytváří optimalizované fotografie a thumbnails,
- první viditelnou fotografii použije jako cover, pokud není uvedeno `cover`,
- podporuje `hidden_images` pro vynechání jednotlivých fotografií,
- načítá základní EXIF informace (datum pořízení, výrobce/model fotoaparátu),
- vykreslí Markdown z `index.md` nad galerií,
- obsahuje fullscreen lightbox s předchozí/další fotografií,
- podporuje klávesy `←`, `→` a `Esc`,
- generuje `sitemap.xml`, pokud zná URL repozitáře,
- je responzivní pro desktop i mobil.

## Lokální spuštění

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python build.py
```

Výsledek je v `_site/`. Lze ho otevřít přes jednoduchý HTTP server:

```bash
python -m http.server --directory _site 8000
```

## GitHub Pages

V repozitáři nastavte **Settings → Pages → Source: GitHub Actions**. Workflow `.github/workflows/pages.yml` potom při každém pushi do `main` vytvoří a publikuje galerii.

Generátor automaticky odvodí URL ve tvaru:

```text
https://UZIVATEL.github.io/REPOSITORY/
```

Pro vlastní doménu lze nastavit repository/environment variable `SITE_URL`, například:

```text
SITE_URL=https://vyuka.example.cz
```

Název úvodní stránky lze změnit přes `GALLERY_TITLE`.

## Přidání nového tématu

Stačí vytvořit adresář, vložit fotografie a `index.md`:

```bash
mkdir topics/2026-10-15-geometrie
cp fotografie/* topics/2026-10-15-geometrie/
```

Potom:

```bash
git add topics/2026-10-15-geometrie
git commit -m "Geometrie 15. 10. 2026"
git push
```

HTML se ručně neupravuje.
