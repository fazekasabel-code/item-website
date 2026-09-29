# I.T.E.M. Alapítvány — rebuild blueprint

Status: plan only, nothing built yet. v2, 2026-09-29.

Fixed constraints (from Ábel):
- **Plain HTML** output, as little machinery as possible. Claude Code builds it later.
- **GitHub Pages** hosting, custom domain `itemalapitvany.hu` (Ábel controls DNS).
- **Full HU/EN translation.** Claude translates, Ábel proofreads.
- **Kelemen Patrik page is scrapped.**

---

## 1. What the sketches get wrong

The problems are mostly **structural**, not visual.

| Problem | Where | Consequence |
|---|---|---|
| **Wrong content model.** Three books (*A határsértés technológiái*, *Hibrid gondolkodás*, *Transzmédia*) are shown as projects next to the Kijárat series they belong to, and the other 11 books are missing. | Sketches 1, 3, 4 | What the foundation actually has is **8 projects + 1 book series of 14 volumes**. |
| **Content hard-coded into layout**, sometimes twice (slide + filmstrip in sketch 3). | All | Adding a project means editing markup in several places, and with two languages that becomes four. |
| **Invented / inconsistent facts.** Years differ between sketches (Hangzavart 2024 in #4, 2023 in the source), and category tags don't match the source pages. | 1, 3, 4 | Placeholder copy leaks into production. |
| **The slideshow is the navigation.** No deep links, `overflow:hidden`, search engines and screen readers can't see the content, and it stops working well past ~15 items. | 3 | Nice as a demo, bad as a site. |
| **Missing images improvised** (hatched boxes, giant initials, colour blocks). | All | Needs one automatic rule. |
| **Funding logos pasted loosely.** No mandatory disclaimer text. | 3 | Compliance risk. |

---

## 2. Design principles

1. **Content is data; layout is templates.** Every fact is typed once. Nav, footer and
   funding blocks exist in one place. With two languages this matters twice as much.
2. **The foundation is the frame, the projects are the picture.** Neutral typographic
   chrome. Colour, logos and covers come *from each project* (the About text itself calls
   I.T.E.M. an *ernyőszervezet*, an umbrella organisation).
3. **One template per content type, optional blocks inside it.** A block with no data
   doesn't render. No bespoke page layouts.
4. **The project list is the backbone.** It scales, works on phones, and is honest.
   Hover previews are an enhancement on top.
5. **Missing images have a designed fallback.** A typographic cover (title + project
   colour) is generated in CSS. No broken images, ever.
6. **Plain HTML/CSS, near-zero JS.** Every page works without JavaScript and has a real URL.
7. **Language parity is enforced.** Every piece of content exists in HU and EN, or the build
   stops and says what's missing.
8. **Simple and durable.** Plain files in git, no database, no npm, no CMS. Anyone can open
   the repo and understand it in ten minutes.
9. **No placeholder copy ships.** An empty field means the section doesn't render.

---

## 3. "Plain HTML": what that means here

| | A. Hand-written HTML | **B. Content + tiny generator → plain HTML** (recommended) |
|---|---|---|
| What's deployed | plain HTML/CSS | plain HTML/CSS, identical in kind |
| Files to maintain | ~22 pages × 2 languages ≈ 44 full HTML files | content files + 6 templates + 1 script |
| Changing the nav/footer | edit 44 files | edit 1 template |
| Keeping HU and EN in sync | manual, and they drift | checked automatically |
| Tooling | none | `python3 build.py`: Python standard library only, **no installs** |

**Recommendation: B.** The live site is 100 % static HTML with no framework or
client-side runtime. The generator is a single readable Python script (roughly 300 lines,
stdlib only: `json`, `string`, `pathlib`, `html`). Python is already on the Mac and was
used for the recovery scripts. The generated HTML is **committed to the repo**, so what's
in `docs/` is exactly what's live. There's no CI pipeline to debug, and if the script ever
dies the site still exists as plain files.

---

## 4. Information architecture & URLs

HU stays at the root and **keeps the old URLs**. EN mirrors it under `/en/` with the
**same slugs**, so the language switcher is a pure prefix swap.

```
HU                                   EN
/                                    /en/                     Home
/rolunk/                             /en/rolunk/              About
/kapcsolat/                          /en/kapcsolat/           Contact
/kijarat/                            /en/kijarat/             Book series (14 volumes, anchors per book)
/<project>/                          /en/<project>/           8 project pages:
  hangzavart · freshfabrik · holy-week · neurodiverz-xyz · meszoly-100 ·
  hibiki · a-computational-stylistic-group-bemutatasa · (kijarat is the 8th, above)
```

Nav: `Projektek · Kijárat · Rólunk · Kapcsolat · EN` / `Projects · Kijárat · About · Contact · HU`.
The switcher always links to the counterpart of the *current* page. Every page carries
`<html lang>` and `<link rel="alternate" hreflang="hu|en">`.

**Old URLs that disappear.** GitHub Pages has no server redirects, so the generator writes
tiny stub pages (`<meta http-equiv="refresh">` + `rel=canonical` + a visible link):

```
/a-hatarsertes-technologiai/  → /kijarat/#a-hatarsertes-technologiai
/hibrid-gondolkodas/          → /kijarat/#hibrid-gondolkodas
/transzmedia/                 → /kijarat/#transzmedia
/galeria/  /elementor-136/  /kelemen-patrik/  /draft/  → /
```
Plus a real `404.html` in both languages (GitHub Pages serves it automatically).

Dropped from the old nav: Galéria (empty), Partnereink, Aktualitások. "Current" comes from
each project's `status`, and partners are listed on each project page.

---

## 5. Content model

Four kinds of content, all plain text. **Language-neutral facts live once; translatable
text lives in paired HU/EN files.**

### 5.1 Projects: one folder each

```
content/projects/hangzavart/
  meta.json      ← facts + short translated fields
  hu.html        ← body text, Hungarian
  en.html        ← body text, English
  cover.jpg      ← optional
  logo.png       ← optional
  gallery/       ← optional; every image here becomes the gallery
```

`meta.json`:
```json
{
  "order": 3,
  "type": "academy",
  "years": [2023],
  "status": "archived",
  "color": "#a63b2e",
  "source_lang": "en",
  "title":   { "hu": "HANGZAVART?", "en": "HANGZAVART?" },
  "summary": { "hu": "Nem akadémiai zeneakadémia…", "en": "A non-academic music academy…" },
  "place":   { "hu": "Zebegény", "en": "Zebegény, Hungary" },
  "dates": "2023-06-21/2023-06-30",
  "people": [
    { "role": { "hu": "Mentorok", "en": "Mentors" },
      "names": ["János Bali", "Eszter Bodnár", "John Duncan", "Péter Márton", "István Rimóczi"] },
    { "role": { "hu": "Koncepció és szervezés", "en": "Concept and organising" },
      "names": ["Sanna Bo", "Ábel Fazekas"] }
  ],
  "partners": [],
  "funding": [{ "funder": "eu-erasmus", "reference": null }],
  "links": [],
  "proofread": { "hu": false, "en": false }
}
```

Body files (`hu.html`, `en.html`) are **HTML fragments** limited to a small vocabulary
(`p h2 h3 ul ol li a em strong blockquote figure img`), paragraph for paragraph parallel,
so the two can be read side by side. No Markdown, which means no parser and no dependency.

`type` enum (labels in HU/EN live in `i18n.json`, not in content):
`book-series` (Kijárat) · `journal` (Hibiki, CSG special issue) · `academy` (Hangzavart) ·
`residency` (Holy Week) · `youth` (neurodiverz.xyz) · `education` (Mészöly 100) ·
`vet-partnership` (Freshfabrik).

### 5.2 Books: `content/books.json` + `content/covers/`

```json
{ "slug": "hibrid-gondolkodas",
  "title": "Hibrid gondolkodás",
  "title_en": "Hybrid Thinking",
  "authors": ["Bruno Latour"], "translators": ["Keresztes Balázs"], "editors": [],
  "year": 2021, "cover": "latour_1.jpg", "shop": "https://kijarat.hu/…" }
```
Books are published in Hungarian only, so the EN site shows the **original title** with
the English gloss beneath (*Hybrid Thinking*) and labels such as "Translated by". Titles
are never replaced.

### 5.3 Pages: `content/pages/{rolunk,kapcsolat}/{meta.json,hu.html,en.html}`

### 5.4 Site-wide: `content/site.json` + `content/i18n.json`

- `site.json`: name (HU/EN), address, email, legal data, and the **funders** table
  (logo + mandatory disclaimer in both languages. The EU provides official HU/EN wording,
  so use theirs verbatim, not our translation).
- `i18n.json`: every UI string (nav, "Megjelenés"/"Published", "Szerző"/"Author", type
  labels, 404 text…).
- `glossary.json`: fixed terminology for translation consistency
  (e.g. *Alapítvány → Foundation*, *Kijárat Kiadó* stays untranslated,
  *ernyőszervezet → umbrella organisation*, name order rules). Claude reads it before every
  translation; Ábel edits it when a proofread correction should apply everywhere.

---

## 6. Templates

Plain HTML files with `$placeholders` (Python `string.Template`); loops are done in the
script.

| Template | Blocks (only rendered if data exists) |
|---|---|
| `base.html` | head/meta/hreflang, header, nav + language switch, footer |
| `home.html` | 2-line intro → **current** projects as large cards → **full project index** (sketch 4) → Kijárat cover strip |
| `project.html` | **hero in project colour** with cover/logo (sketch 3's idea as a header, not a carousel) → facts (years, place, type, people, partners, links) → body → gallery → book list if `book-series` → funding block → prev/next |
| `kijarat.html` | intro + cover grid, one anchor per book |
| `page.html` | editorial single column (sketch 1 typography) for About and Contact |
| `redirect.html`, `404.html` | stubs |

Sketch 4's index becomes the backbone, sketch 3's colour and media become the project
header, and sketch 1's typography is used for reading. Sketch 2 is dropped.

**Visual system:** one `style.css` with tokens on `:root`. Two typefaces at most, both with
full Hungarian coverage (ő ű Ő Ű), and self-hosted (Catamaran, already recovered, passes
and gives continuity). Neutral paper/ink chrome; the only saturated colour on a page is the
project's `color`. Fluid type scale, light/dark via `prefers-color-scheme`.
Images: the build script **doesn't** resize. Images are exported once at 2 sizes
(`-800`, `-1600`) with `sips` (built into macOS) and used via `srcset`.
The only JavaScript is one small optional file for the index hover preview.

---

## 7. Repository layout

```
item-website/                 ← git repo, pushed to GitHub
  ARCHITECTURE.md
  README.md                   ← "how to add a project / book / fix a translation"
  build.py                    ← the generator (stdlib only)
  templates/                  ← base, home, project, kijarat, page, redirect, 404
  assets/                     ← style.css, fonts/, funders/, preview.js
  content/
    site.json  i18n.json  glossary.json  books.json
    covers/
    pages/rolunk/  pages/kapcsolat/
    projects/<slug>/
  docs/                       ← GENERATED, committed, served by GitHub Pages
    CNAME                     ← itemalapitvany.hu
    index.html  kijarat/  rolunk/  …  en/…
  legacy/                     ← recovered WP mirror, found_images, rip scripts (archive)
```

`build.py` does:
1. Load and **validate** all content. Required fields, both languages present, image files
   exist, slugs unique, `type`/`funder` keys known. It fails loudly and names the file.
2. Render every page × {hu, en} into `docs/`, plus redirects, 404s, `sitemap.xml` and
   `robots.txt`.
3. Write `proof.html` (not linked, `noindex`, **not** in `docs/`): every translatable text
   in two columns, HU | EN, paragraph-aligned, grouped by page. Items not yet marked
   `proofread` come first.
4. `python3 build.py --serve` → builds and serves locally on port 8000 for preview.

iCloud: no `node_modules` anymore, but a `.git` folder inside iCloud Drive can still get
corrupted by sync. Put the repo in a non-iCloud folder (e.g. `~/code/item-website`); GitHub
is the backup.

---

## 8. Translation & proofreading workflow

1. **Source of truth per item** is its original language (`source_lang`). Most pages are
   HU originals, while Hangzavart, Freshfabrik and Holy Week are EN originals, so Claude
   translates *into* HU for those.
2. Claude translates using `glossary.json` and writes the fragment paragraph for paragraph.
   `proofread.<lang>` stays `false`.
3. Ábel opens `proof.html` (or the local preview) and edits either the file directly or
   tells Claude "in holy-week/hu.html paragraph 3 → …".
4. When a page is approved, `proofread.hu/en` is set to `true`. `build.py` prints a summary
   such as "12 / 18 texts proofread".
5. When source text changes later, Claude updates the counterpart in the same commit and
   resets its `proofread` flag. **A commit never changes one language only.**

Names follow each language's convention (HU: *Fazekas Ábel*, EN: *Ábel Fazekas*), as a
glossary rule rather than case-by-case.

---

## 9. Hosting & DNS (GitHub Pages)

- Repo Settings → Pages → *Deploy from branch* `main` / `/docs`. No Actions needed.
- **First, verify the domain** in GitHub account settings → Pages → Verified domains
  (adds a TXT record). This prevents domain takeover.
- DNS at your registrar:
  - apex `itemalapitvany.hu`: `A` → `185.199.108.153`, `185.199.109.153`,
    `185.199.110.153`, `185.199.111.153` (and the matching `AAAA` records `2606:50c0:8000::153`…`8003::153`)
  - `www`: `CNAME` → `<github-user>.github.io`
  - ⚠️ **Don't touch the `MX` / mail records.** `info@itemalapitvany.hu` must keep working.
    Screenshot the current DNS zone before changing anything, and lower the TTL a day
    ahead of time.
- Enable *Enforce HTTPS* once the certificate appears (minutes to an hour).
- The old host can be cancelled after a week of the new site running cleanly.

---

## 10. Everyday handling

| Task | What happens |
|---|---|
| Add a project | Claude copies a project folder, fills `meta.json`, writes both language files, runs `build.py`, commits. You proofread. |
| Add a book | One entry in `books.json` + cover. It appears on /kijarat/ and on the home strip in both languages. |
| Project finished | `status: "archived"`. It moves from the highlight area to the index. |
| Found a missing image | Drop it in the project folder, rebuild. The typographic cover disappears. |
| New EU-funded project | `"funding": [{"funder": "eu-erasmus", "reference": "…"}]`. The logo + official disclaimer appear in both languages. |
| Fix a typo | Edit the fragment, `python3 build.py`, commit, push. Live in ~1 min. |
| Mistake in data | The build stops and names the file and field. Nothing broken goes live. |

---

## 11. Build plan (for the later Claude Code session)

1. Create the repo outside iCloud and move `site/`, `found_images/`, `scripts/` into `legacy/`.
2. **Extract content** from `legacy/site/` into the §5 structure. Strip the Word-paste junk
   (`Normal 0 21 false … X-NONE`) and parse the 14 books from the Kijárat page. Do **not**
   carry over Kelemen Patrik.
3. Write `build.py` + unstyled templates, and verify every page renders with real data in HU.
4. **Translate** all texts (glossary first), then generate `proof.html` → Ábel proofreads.
5. **Design pass** on `style.css` using real content (one round, comparing 2 directions at most).
6. Assets: export covers/logos at 2 sizes and chase the missing items from `CHECKLIST.md`.
7. Redirect stubs, 404, sitemap, hreflang, OG images; accessibility + Lighthouse check.
8. GitHub Pages + domain verification + DNS switch (§9).

---

## 12. Researched facts (2026-09-29)

**Foundation:** founded **2020**. Legal data from the court register extract (version 10,
supplied by Ábel), all confirmed:

| Field | Value |
|---|---|
| Name | I.T.E.M. Kulturális és Oktatási Alapítvány |
| Short name | I.T.E.M. Alapítvány (no registered foreign-language name, so the EN site uses the HU name plus the gloss "Cultural and Educational Foundation") |
| Seat | 1068 Budapest, Király utca 112. (the mailing address on the old site adds "2. em. 6a") |
| Registration no. | **01-01-0012935** (Fővárosi Törvényszék, 0100/Pk.60148/2020) |
| Tax no. | **19250409-1-42** (registered 2020-06-11) · EU VAT: HU19250409 |
| Status | **Közhasznú** (public benefit) since 2023-06-02 |
| Board (kuratórium) | Bódi Zsuzsanna (representative), Szemes Botond Bálint, Fazekas Ábel |

→ Goes into `site.json`. The footer shows name, seat, registration no., tax no. and email in both
languages. Because the foundation is **közhasznú**, it can receive the **SZJA 1 %**. An optional
"Támogatás / Support" line with the tax number is cheap to add (decide at build time).
The bank account in the register is public, but it is **not** put on the site unless Ábel
asks for it.

**Holy Week (PAIKKA)**: took place. **I.T.E.M. was the official organisation behind PAIKKA**
(grant holder), which PAIKKA's partners don't mention, so the page must say it explicitly, e.g.
"PAIKKA, a platform of the I.T.E.M. Foundation…". Sources: [paikka.xyz/holy-week](https://paikkaxyz.wordpress.com/holy-week/),
[zdruzenie.ooo](https://zdruzenie.ooo/en/projekty/holy-week/), [Terén Brno](https://jasuteren.cz/en/program/holy-week).
- PAIKKA: Budapest platform for impermanent collectives at the intersection of art and science.
  Keep the (now redirecting) link `paikka.xyz` → `paikkaxyz.wordpress.com`.
- Week-long residency in Hungary, then a participatory, multisensory performance tour:
  13 Apr 2025 DDK Węglin, Lublin (PL) · 15 Apr Terén, Brno (CZ) · 16 Apr LOM, Bratislava (SK) · 17 Apr 1111, Budapest (HU).
- Creators: Jana Ambrózová (SK), Jeries AbuJaber (PS), Csilla Bartus (HU), Magdalena Franczak (PL),
  Kasha Potrohosh (SK/UA), Maciej Polynko (PL), Yu En-Ping (TW). Facilitator: Bíborka Béres.
- Coordination: Sanna Bo · Graphic design: Dániel Kophelyi · Photos: Jacek Świerczyński (Lublin), Simon Lupták (Bratislava).
- Partners: Združenie OOO, Cross Attic, Dzielnicowy Dom Kultury „Węglin”.
- `years: [2025]`, `status: archived`, funder key `visegrad`.

**Visegrad Fund (funder key `visegrad`)**: official files are downloaded to `found_images/visegrad/`
(from [visegradfund.org/about-us/logo](https://www.visegradfund.org/about-us/logo)):
`VF-logotype-{black,blue,white}.pdf` originals, plus `.svg` (vector conversion via pdftocairo)
and `.png` (1200 px) derivatives, and `VF-Logo-Acknowledgement.pdf` (the grantee guide).
Rules from the guide that the build must respect:
- The logo **must not be recoloured or altered**. Use the black version on light backgrounds,
  the **official white version** on dark mode / dark project heroes (allowed "reversed" use),
  never CSS `filter`/`currentColor` tricks. Allowed text colours: blue #03BFD7, grey #666666, black.
- Clear space: 1× the "n" height above and below, 2× left and right. Minimum 72 dpi on screen.
- Mandatory statement on all digital communication (EN, verbatim):
  *"The project is co-financed by the governments of Czechia, Hungary, Poland and Slovakia
  through Visegrad Grants from the International Visegrad Fund. The mission of the fund is to
  advance ideas for sustainable regional cooperation in Central Europe."*
- Official Hungarian name: **Nemzetközi Visegrádi Alap** (short: Visegrádi Alap). The guide gives
  no official HU statement, so Claude translates it and Ábel proofreads, keeping the name exact.

**Hibiki**: first issue (I. évf. 1. sz.) **2020**. Latest issue on hibiki.hu is **October 2023**,
and the site is still online. The [impresszum](https://www.hibiki.hu/impress/) lists I.T.E.M. Alapítvány as a
**partner** (with Nihon-Go and Japan Cuccok), not as publisher. Editor-in-chief: Varga Lilla ·
editorial associate: Vadász Fruzsina · design: Varga Zoltán · web: Király Attila.
→ `years: [2020, 2023]`, `role: partner`.

**neurodiverz.xyz**: **2022–2023** (confirmed by Ábel). EU co-financed ("az Európai Unió
társfinanszírozásával"). Programme name and project number are **deliberately left blank**
(Ábel's decision). The funding block shows the generic EU emblem + disclaimer only, with
no `reference`. The domain **no longer resolves**, so `links: []`.

## 13. Decide at build time

1. Book `title_en` glosses: Claude drafts them, Ábel approves (they appear publicly).
2. Whether the About page lists the board (kuratórium), and whether to add an SZJA 1 % line.
