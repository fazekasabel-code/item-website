# I.T.E.M. Alapítvány — Wayback recovery checklist

The site was recovered from this Wayback Machine snapshot:
https://web.archive.org/web/20260511120733/http://www.itemalapitvany.hu/

Recovered into [`site/`](site/) as a working static mirror — 24 pages, ~105
assets (CSS/JS/images/fonts), ~6 MB total.

After the initial rip, I went back and searched online for replacements for
everything Wayback never archived. **13 of the ~15 missing items were found**
(mostly because I.T.E.M. Alapítvány and the publisher **Kijárat Kiadó** turned
out to be the same organization — same office address — so their live
bookshop at [kijarat.hu](https://kijarat.hu) had official copies of the book
covers). Those replacements are already copied into `site/` at the correct
paths — nothing left to do for the items marked ✅. Raw copies are also kept
in [`found_images/`](found_images/) for reference.

## How to view the site

```bash
cd site && python3 -m http.server 8123
```
Then open http://localhost:8123/ in a browser.

## ✅ Found and already placed in `site/`

- **Custom typeface "Catamaran"** (Bold/Regular/SemiBold) — it's an open
  Google Font; downloaded the current variable-font file from Google's own
  font repo and placed it at all three expected filenames in
  `wp-content/themes/zita/third-party/fonts/`. Visually identical; only
  difference is one variable-weight file instead of three static ones.
- **"Co-funded by the EU" banners**, both the BLACK-outline and POS/color
  variants — official files from the European Commission's own logo
  download centre, exact variant match.
- **8 book covers**, sourced from Kijárat Kiadó's shop (kijarat.hu) and their
  distributor Atlantisz Kiadó — confirmed via matching filenames/IDs on the
  source pages (e.g. `9_latour_borito`, `2_marjanovics_borito`,
  `i1588164709ser`):
  - `hatar_vegleges_kontrasztos` → *Horváth Márk – Lovász Ádám: A
    határsértés technológiái* (used on the home, kijárat, and
    a-hatarsertes-technologiai pages)
  - `transzmediajav` → *Fejes Richárd – Gregor Lilla: Transzmédia* (kijárat,
    transzmédia, elementor-136 pages)
  - `latour_1` → *Bruno Latour: Hibrid Gondolkodás* (kijárat, hibrid-gondolkodás)
  - `agamben` → *Giorgio Agamben: A nyitott. Az ember és az állat* (2024 —
    matches the March-2024 upload date of the surrounding images)
  - `lovecraft` → *H. P. Lovecraft: Poszthumanista olvasatok*
  - `ureczky` → *Ureczky Eszter: Kultúra és kontamináció*
  - `tanos` → *Tanos Márton: Regénypárhuzamok*
  - `ser` → *Michel Serres: A természeti szerződés*
  - `vörös` → *Vörös István: Árnyékvers és irónia*
  - `marjanovics` → *Márjánovics Diána: Örökölt blende*

  Visually verified in-browser — the kijárat page now renders full 3D book
  cover mockups with correct titles/authors instead of broken image icons.

## ❌ Still missing — could not find online

These are bespoke, one-off graphics for small internal projects with no
public footprint (no matching image anywhere I could search), so they're
genuinely gone unless you have a personal/local copy (old email attachments,
a designer's Google Drive, a laptop backup, etc.):

- **Home page**: Szabó R. János "Plateau" artwork, "Mészöly I.T.E.M.
  Projekt" graphic, `11224374.jpg`, Neurodiverz logo (full-size), "Holy
  week" graphic, `output.jpg`
- **Kijárat page**: `arnyekoskek_logo`, `11218673` (all sizes)
- **A Computational Stylistic Group bemutatása**: `2.-sz.-melléklet_FELCZAK_logo_vektoros`,
  `csg` logo, `db` logo, `rn_image_picker_lib_temp_...` (this one is a
  phone-camera filename — literally someone's personal photo upload, not
  something that could ever turn up in a search)
- **Freshfabrik**: `ff` logo/photo, `FF_24_documentation_210x270mm_0529_TELJES_PAGES.pdf`
  — I confirmed Freshfabrik is an Erasmus+ KA210-VET project (that's why the
  EU banner is on that page), but it doesn't appear on the EU's public
  project-results platform, and their Instagram/Facebook pages are
  login-walled so I couldn't pull images from them either. Worth checking
  those accounts yourself while logged in, or asking whoever ran the
  project for their files.
- **Neurodiverz-xyz / Hangzavart**: Neurodiverz logo (full-size) — same file
  as the homepage one
- **Meszöly-100**: "Mészöly I.T.E.M. Projekt" graphic — same file as the
  homepage one
- A handful of **Elementor per-post CSS files** (`post-28.css`,
  `post-52.css`, `post-46.css`, `post-136.css`, `post-270.css`,
  `post-329.css`) — cosmetic only, auto-generated styling that Elementor
  would regenerate from scratch anyway when the page is rebuilt.

## Bonus: an old `/draft/` staging copy

The archive also had a `/draft/` subtree (`draft/rolunk`, `draft/galeria`,
`draft/hibiki`, `draft/kapcsolat`, `draft/kelemen-patrik`, `draft/kijarat`,
`draft/paikka`) — an earlier, pre-launch version of the site from Feb 2023,
distinct from the final live pages. It's included in `site/draft/` for
reference, but most of its own images/CSS/JS were never crawled by Wayback
(it wasn't linked from the live site's navigation). You probably don't need
it — it's superseded by the real pages.

## Not a checklist item, but worth knowing

- The **Kapcsolat (contact) page** had no contact form — just a static
  address/email block (`I.T.E.M. Kulturális és Oktatási Alapítvány, 1068
  Király utca 112. 2 em. 6a, info@itemalapitvany.hu`). Nothing to recover
  there, but if you want a working contact form on the rebuilt site you'll
  need to add one (e.g. Formspree, Netlify Forms) since the old one was
  presumably WordPress's PHP mail handler, which won't work on a static site.
- Google Fonts (Roboto, Roboto Slab) are loaded from `fonts.googleapis.com`
  and will keep working as-is — no action needed.
- The site was built on WordPress + Elementor + a customized "zita/freely"
  theme. The `site/` mirror is static HTML/CSS/JS (no PHP/WordPress backend),
  which is the right starting point for a rebuild.
