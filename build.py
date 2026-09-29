#!/usr/bin/env python3
"""Build the I.T.E.M. Alapítvány website.

    content/ + templates/ + assets/  ->  docs/   (plain static HTML, served by GitHub Pages)

Usage:
    python3 build.py            strict build: every text must exist in HU and EN
    python3 build.py --draft    allow missing translations (falls back to the source language)
    python3 build.py --serve    build, then serve docs/ on http://localhost:8000
    python3 build.py --proof    also write proof/index.html (HU | EN side by side, not published)

Python standard library only. See ARCHITECTURE.md for the content model.
"""
import argparse
import datetime
import html
import http.server
import json
import re
import shutil
import struct
import sys
from html.parser import HTMLParser
from pathlib import Path
from string import Template

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
TEMPLATES = ROOT / "templates"
ASSETS = ROOT / "assets"
OUT = ROOT / "docs"
PROOF = ROOT / "proof"

LANGS = ("hu", "en")
PREFIX = {"hu": "", "en": "/en"}
OG_LOCALE = {"hu": "hu_HU", "en": "en_GB"}
TYPES = {"book-series", "journal", "academy", "residency", "youth", "education", "vet-partnership"}
STATUSES = {"current", "archived"}
ALLOWED_TAGS = {"p", "h2", "h3", "ul", "ol", "li", "a", "em", "strong", "br", "blockquote", "figure", "figcaption", "img"}

# Old URLs that no longer have a page of their own (GitHub Pages has no server redirects).
REDIRECTS = {
    "/a-hatarsertes-technologiai/": "/kijarat/#a-hatarsertes-technologiai",
    "/hibrid-gondolkodas/": "/kijarat/#hibrid-gondolkodas",
    "/transzmedia/": "/kijarat/#transzmedia",
    "/galeria/": "/",
    "/elementor-136/": "/",
    "/kelemen-patrik/": "/",
    "/draft/": "/",
}

errors, warnings = [], []


def err(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


def esc(s):
    return html.escape(s or "", quote=True)


def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        err(f"{path.relative_to(ROOT)}: {e}")
        return None


# ---------------------------------------------------------------- validation helpers

class FragmentChecker(HTMLParser):
    """Checks a body fragment against the allowed tag vocabulary and counts top-level blocks."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.bad, self.depth, self.blocks = set(), 0, 0

    def handle_starttag(self, tag, attrs):
        if tag not in ALLOWED_TAGS:
            self.bad.add(tag)
        if tag in ("br", "img"):
            return
        if self.depth == 0:
            self.blocks += 1
        self.depth += 1

    def handle_endtag(self, tag):
        if tag not in ("br", "img"):
            self.depth = max(0, self.depth - 1)


def check_fragment(text, where):
    c = FragmentChecker()
    c.feed(text)
    if c.bad:
        err(f"{where}: disallowed tags {sorted(c.bad)} (allowed: {sorted(ALLOWED_TAGS)})")
    return c.blocks


def need_langs(obj, where, allow_empty=False):
    if not isinstance(obj, dict) or any(l not in obj for l in LANGS):
        err(f"{where}: needs both 'hu' and 'en'")
        return
    for l in LANGS:
        if not allow_empty and not (obj[l] or "").strip():
            err(f"{where}: '{l}' is empty")


def image_size(path):
    """Width/height of a PNG or JPEG, without third-party libraries."""
    data = path.read_bytes()
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", data[16:24])
    if data[:2] == b"\xff\xd8":
        i = 2
        while i < len(data):
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            if marker in (0xC0, 0xC1, 0xC2):
                h, w = struct.unpack(">HH", data[i + 5:i + 9])
                return w, h
            i += 2 + struct.unpack(">H", data[i + 2:i + 4])[0]
    err(f"{path.relative_to(ROOT)}: not a real PNG or JPEG (convert it, e.g. with tools/prep_images.sh)")
    return None, None


# ---------------------------------------------------------------- loading

def load_bodies(folder, source_lang, where, draft, required=True):
    """Returns {lang: (html, is_fallback, lang_of_text)}."""
    raw = {}
    for l in LANGS:
        f = folder / f"{l}.html"
        raw[l] = f.read_text(encoding="utf-8").strip() if f.exists() else ""
    if required and not raw[source_lang]:
        err(f"{where}/{source_lang}.html: source text is missing or empty")
    counts = {l: check_fragment(raw[l], f"{where}/{l}.html") for l in LANGS if raw[l]}
    if len(counts) == 2 and counts["hu"] != counts["en"]:
        warn(f"{where}: HU has {counts['hu']} blocks, EN has {counts['en']} – keep them paragraph-parallel")
    out = {}
    for l in LANGS:
        if raw[l] or not raw[source_lang]:
            out[l] = (raw[l], False, l)
        elif draft:
            warn(f"{where}/{l}.html missing – using {source_lang} text (draft)")
            out[l] = (raw[source_lang], True, source_lang)
        else:
            err(f"{where}/{l}.html missing – translate it or build with --draft")
            out[l] = ("", False, l)
    return out


def load_content(draft):
    site = load_json(CONTENT / "site.json")
    i18n = load_json(CONTENT / "i18n.json")
    names = load_json(CONTENT / "names.json") or {}
    books = load_json(CONTENT / "books.json") or []
    if site is None or i18n is None:
        return None

    for k, v in i18n.items():
        need_langs(v, f"i18n.json:{k}", allow_empty=True)

    slugs = set()
    for b in books:
        where = f"books.json:{b.get('slug')}"
        for key in ("slug", "title", "year", "shop"):
            if not b.get(key):
                err(f"{where}: '{key}' is required")
        if b.get("slug") in slugs:
            err(f"{where}: duplicate slug")
        slugs.add(b.get("slug"))
        if b.get("cover") and not (CONTENT / "covers" / b["cover"]).exists():
            err(f"{where}: cover file content/covers/{b['cover']} not found")
    books.sort(key=lambda b: -int(b.get("year") or 0))  # stable: keeps file order within a year

    projects = []
    for folder in sorted((CONTENT / "projects").iterdir()):
        if not folder.is_dir():
            continue
        where = f"projects/{folder.name}"
        m = load_json(folder / "meta.json")
        if m is None:
            continue
        m["slug"] = folder.name
        m["dir"] = folder
        if m.get("type") not in TYPES:
            err(f"{where}: type '{m.get('type')}' not one of {sorted(TYPES)}")
        if m.get("status") not in STATUSES:
            err(f"{where}: status must be one of {sorted(STATUSES)}")
        years = m.get("years")
        if not (isinstance(years, list) and 1 <= len(years) <= 2 and all(isinstance(y, int) for y in years)):
            err(f"{where}: years must be [start] or [start, end]")
            m["years"] = [0]
        if m.get("source_lang") not in LANGS:
            err(f"{where}: source_lang must be 'hu' or 'en'")
            m["source_lang"] = "hu"
        need_langs(m.get("title"), f"{where}: title")
        need_langs(m.get("summary"), f"{where}: summary")
        for key in ("place", "dates"):
            if m.get(key) is not None:
                need_langs(m[key], f"{where}: {key}")
        for p in m.get("people", []):
            need_langs(p.get("role"), f"{where}: people role")
        for f in m.get("facts", []):
            need_langs(f.get("label"), f"{where}: facts label")
            need_langs(f.get("value"), f"{where}: facts value")
        for f in m.get("funding", []):
            if f.get("funder") not in site["funders"]:
                err(f"{where}: unknown funder '{f.get('funder')}' (add it to site.json funders)")
        for key in ("logo", "cover"):
            if m.get(key) and not (folder / m[key]).exists():
                err(f"{where}: {key} file '{m[key]}' not found")
        if m.get("color") and not re.fullmatch(r"#[0-9a-fA-F]{6}", m["color"]):
            err(f"{where}: color must look like #1a2b3c")
        m["gallery"] = sorted(p.name for p in (folder / "gallery").glob("*") if p.suffix.lower() in (".jpg", ".jpeg", ".png")) \
            if (folder / "gallery").is_dir() else []
        m["body"] = load_bodies(folder, m["source_lang"], where, draft)
        projects.append(m)

    # Newest first: by end year, then start year, then manual order.
    projects.sort(key=lambda p: (-(p["years"][-1] if not p.get("ongoing") else 9999), -p["years"][0], p.get("order", 99)))

    pages = {}
    for folder in sorted((CONTENT / "pages").iterdir()):
        if not folder.is_dir():
            continue
        where = f"pages/{folder.name}"
        m = load_json(folder / "meta.json")
        if m is None:
            continue
        m["slug"] = folder.name
        need_langs(m.get("title"), f"{where}: title")
        need_langs(m.get("summary"), f"{where}: summary")
        m["body"] = load_bodies(folder, m.get("source_lang", "hu"), where, draft,
                                required=not m.get("show_contact"))
        pages[folder.name] = m

    return {"site": site, "i18n": i18n, "names": names, "books": books, "projects": projects, "pages": pages}


# ---------------------------------------------------------------- rendering helpers

class Ctx:
    def __init__(self, data, lang):
        self.d, self.lang = data, lang
        self.site = data["site"]
        self.base = self.site.get("base_path", "").rstrip("/")

    def t(self, key, **kw):
        s = self.d["i18n"].get(key, {}).get(self.lang)
        if s is None:
            err(f"i18n.json: missing key '{key}'")
            return key
        for k, v in kw.items():
            s = s.replace("{" + k + "}", str(v))
        return s

    def url(self, path, lang=None):
        return f"{self.base}{PREFIX[lang or self.lang]}{path}"

    def asset(self, path):
        return f"{self.base}/assets/{path}"

    def pick(self, obj):
        return obj.get(self.lang, "") if isinstance(obj, dict) else (obj or "")

    def name(self, n):
        return self.d["names"].get(n, n) if self.lang == "en" else n

    def names(self, lst):
        return ", ".join(self.name(n) for n in lst)

    def years(self, p):
        y = p["years"]
        if p.get("ongoing"):
            return f"{y[0]}–"
        return f"{y[0]}–{y[1]}" if len(y) == 2 and y[1] != y[0] else str(y[0])

    def local_links(self, fragment):
        """Root-relative links in content ('/kijarat/') get the base path and language prefix."""
        return re.sub(r'href="/(?!/)', f'href="{self.base}{PREFIX[self.lang]}/', fragment)


def tpl(name):
    return Template((TEMPLATES / f"{name}.html").read_text(encoding="utf-8"))


def fill(name, **kw):
    try:
        return tpl(name).substitute(**kw)
    except KeyError as e:
        err(f"templates/{name}.html: no value for ${e.args[0]}")
        return ""


def img_tag(ctx, rel_path, disk_path, alt, cls, loading="lazy"):
    w, h = image_size(disk_path)
    dims = f' width="{w}" height="{h}"' if w else ""
    return f'<img class="{cls}" src="{esc(ctx.asset(rel_path))}" alt="{esc(alt)}"{dims} loading="{loading}" decoding="async">'


def typo_cover(title, meta="", color=None, cls="typo-cover"):
    style = f' style="--cover-color:{color}"' if color else ""
    meta_html = f'<span class="typo-cover__meta">{esc(meta)}</span>' if meta else ""
    return f'<div class="{cls}"{style} aria-hidden="true"><span class="typo-cover__title">{esc(title)}</span>{meta_html}</div>'


def body_html(ctx, body):
    text, fallback, text_lang = body[ctx.lang]
    if not text:
        return ""
    lang_attr = f' lang="{text_lang}"' if text_lang != ctx.lang else ""
    notice = f'<p class="fallback-notice">{esc(ctx.t("fallback.notice"))}</p>\n' if fallback else ""
    return f'{notice}<div class="prose"{lang_attr}>\n{ctx.local_links(text)}\n</div>'


def page(ctx, *, path, title, description, content, body_class, color=None, scripts="", switch_path=None):
    site = ctx.site
    other = "en" if ctx.lang == "hu" else "hu"
    nav = [("/", "nav.projects", "projects"), ("/kijarat/", "nav.kijarat", "kijarat"),
           ("/rolunk/", "nav.about", "rolunk"), ("/kapcsolat/", "nav.contact", "kapcsolat")]
    current = path.strip("/").split("/")[0] or "projects"
    items = "\n".join(
        f'      <li class="site-nav__item"><a class="site-nav__link" href="{ctx.url(p)}"'
        f'{" aria-current=\"page\"" if current == key else ""}>{esc(ctx.t(k))}</a></li>'
        for p, k, key in nav)
    domain = site["domain"].rstrip("/")
    alternates = "\n".join(
        f'<link rel="alternate" hreflang="{l}" href="{domain}{PREFIX[l]}{path}">' for l in LANGS
    ) + f'\n<link rel="alternate" hreflang="x-default" href="{domain}{path}">'
    full_title = title if title == ctx.pick(site["short"]) else f"{title} · {ctx.pick(site['short'])}"
    return fill(
        "base",
        lang=ctx.lang, page_title=esc(full_title), description=esc(description),
        canonical=f"{domain}{PREFIX[ctx.lang]}{path}", alternates=alternates, og_locale=OG_LOCALE[ctx.lang],
        asset_base=f"{ctx.base}/assets", body_class=body_class,
        body_style=f' style="--project-color:{color}"' if color else "",
        skip=esc(ctx.t("skip")), home_url=ctx.url("/"), site_short=esc(ctx.pick(site["short"])),
        nav_label=esc(ctx.t("nav.projects")), nav_items=items,
        switch_url=ctx.url(switch_path or path, other), other_lang=other,
        switch_label=esc(ctx.t("nav.switch_label")), switch_text=esc(ctx.t("nav.switch")),
        content=content, site_name=esc(ctx.pick(site["name"])), address=esc(ctx.pick(site["address"])),
        email=esc(site["email"]),
        reg_label=esc(ctx.t("footer.reg")), reg_no=esc(site["legal"]["registration_no"]),
        tax_label=esc(ctx.t("footer.tax")), tax_no=esc(site["legal"]["tax_no"]),
        public_benefit=esc(ctx.t("footer.public_benefit")),
        founded=site["founded"], year=datetime.date.today().year, scripts=scripts,
    )


# ---------------------------------------------------------------- page builders

def project_media(ctx, p, eager=False):
    """Cover > logo > typographic cover. Returns (html, kind)."""
    title = ctx.pick(p["title"])
    for key, kind in (("cover", "cover"), ("logo", "logo")):
        if p.get(key):
            rel = f"projects/{p['slug']}/{p[key]}"
            return img_tag(ctx, rel, p["dir"] / p[key], title, f"project-{kind}", "eager" if eager else "lazy"), kind
    return typo_cover(title, ctx.years(p), p.get("color")), "typo"


def build_home(ctx):
    d = ctx.d
    current = [p for p in d["projects"] if p["status"] == "current"]
    cards = []
    for p in current:
        media, kind = project_media(ctx, p)
        cards.append(
            f'    <li class="project-card project-card--{kind}"'
            f'{f" style=\"--project-color:{p["color"]}\"" if p.get("color") else ""}>\n'
            f'      <a class="project-card__link" href="{ctx.url("/" + p["slug"] + "/")}">\n'
            f'        <div class="project-card__media">{media}</div>\n'
            f'        <p class="project-card__kicker"><span>{esc(ctx.t("type." + p["type"]))}</span> <span>{ctx.years(p)}</span></p>\n'
            f'        <h3 class="project-card__title">{esc(ctx.pick(p["title"]))}</h3>\n'
            f'        <p class="project-card__summary">{esc(ctx.pick(p["summary"]))}</p>\n'
            f'      </a>\n    </li>')
    current_section = ""
    if cards:
        current_section = (
            '<section class="current-projects" aria-labelledby="current-title">\n'
            f'  <h2 id="current-title" class="section-title">{esc(ctx.t("home.current"))}</h2>\n'
            '  <ul class="current-projects__list">\n' + "\n".join(cards) + "\n  </ul>\n</section>")

    rows = []
    for i, p in enumerate(d["projects"], 1):
        media, kind = project_media(ctx, p)
        color = f' data-color="{p["color"]}" style="--project-color:{p["color"]}"' if p.get("color") else ""
        rows.append(
            f'    <li class="project-row" data-type="{p["type"]}"{color}>\n'
            f'      <a class="project-row__link" href="{ctx.url("/" + p["slug"] + "/")}">\n'
            f'        <span class="project-row__num">{i:02d}</span>\n'
            f'        <span class="project-row__title">{esc(ctx.pick(p["title"]))}</span>\n'
            f'        <span class="project-row__type">{esc(ctx.t("type." + p["type"]))}</span>\n'
            f'        <span class="project-row__years">{ctx.years(p)}</span>\n'
            f'        <span class="project-row__summary">{esc(ctx.pick(p["summary"]))}</span>\n'
            f'        <span class="project-row__preview" hidden>{media}</span>\n'
            f'      </a>\n    </li>')

    strip = []
    for b in [b for b in d["books"] if b.get("cover")][:6]:
        cover = img_tag(ctx, f"covers/{b['cover']}", CONTENT / "covers" / b["cover"], b["title"], "book-strip__cover")
        strip.append(f'    <li class="book-strip__item"><a href="{ctx.url("/kijarat/")}#{b["slug"]}">{cover}</a></li>')

    content = fill(
        "home", site_name=esc(ctx.pick(ctx.site["name"])), tagline=esc(ctx.pick(ctx.site["tagline"])),
        intro=esc(ctx.pick(ctx.site["intro"])), current_section=current_section,
        index_title=esc(ctx.t("home.index")), index_rows="\n".join(rows),
        kijarat_url=ctx.url("/kijarat/"), books_title=esc(ctx.t("home.books")),
        book_strip="\n".join(strip), books_more=esc(ctx.t("home.books_more", n=len(d["books"]))))
    return page(ctx, path="/", title=ctx.pick(ctx.site["short"]), description=ctx.pick(ctx.site["intro"]),
                content=content, body_class="home", scripts=f'<script src="{ctx.asset("preview.js")}" defer></script>')


def fact(label, value_html, cls):
    return f'        <div class="facts__item facts__item--{cls}"><dt>{esc(label)}</dt><dd>{value_html}</dd></div>'


def link_list(items):
    lis = "".join(
        f'<li><a href="{esc(u)}">{esc(n)}</a></li>' if u else f"<li>{esc(n)}</li>" for n, u in items)
    return f'<ul class="facts__list">{lis}</ul>'


def build_books(ctx, books):
    items = []
    for b in books:
        people = []
        for key, label in (("authors", "book.author"), ("editors", "book.editor"), ("translators", "book.translator")):
            if b.get(key):
                people.append(f'<div><dt>{esc(ctx.t(label))}</dt><dd>{esc(ctx.names(b[key]))}</dd></div>')
        people.append(f'<div><dt>{esc(ctx.t("book.year"))}</dt><dd>{b["year"]}</dd></div>')
        if b.get("isbn"):
            people.append(f'<div><dt>{esc(ctx.t("book.isbn"))}</dt><dd>{esc(b["isbn"])}</dd></div>')
        if b.get("cover"):
            cover = img_tag(ctx, f"covers/{b['cover']}", CONTENT / "covers" / b["cover"], b["title"], "book__cover")
        else:
            cover = typo_cover(b["title"], ctx.names(b.get("authors") or b.get("editors") or []), cls="typo-cover typo-cover--book")
        hu_attr = ' lang="hu"' if ctx.lang != "hu" else ""
        gloss = f'<p class="book__gloss">{esc(b["title_en"])}</p>' if ctx.lang == "en" and b.get("title_en") else ""
        subtitle = f'<p class="book__subtitle"{hu_attr}>{esc(b["subtitle"])}</p>' if b.get("subtitle") else ""
        items.append(
            f'    <li class="book" id="{b["slug"]}">\n'
            f'      <div class="book__media">{cover}</div>\n'
            f'      <div class="book__text">\n'
            f'        <h3 class="book__title"{hu_attr}>{esc(b["title"])}</h3>\n'
            f'        {subtitle}{gloss}\n'
            f'        <dl class="book__meta">{"".join(people)}</dl>\n'
            f'        <p class="book__shop"><a href="{esc(b["shop"])}">{esc(ctx.t("book.shop"))}</a></p>\n'
            f'      </div>\n    </li>')
    note = f'  <p class="books__note">{esc(ctx.t("book.hu_only"))}</p>\n' if ctx.t("book.hu_only") else ""
    return ('<section class="books" id="books" aria-labelledby="books-title">\n'
            f'  <h2 id="books-title" class="section-title">{esc(ctx.t("section.books"))} <span class="books__count">{len(books)}</span></h2>\n'
            f'{note}  <ol class="books__list">\n' + "\n".join(items) + "\n  </ol>\n</section>")


def build_funding(ctx, p):
    if not p.get("funding"):
        return ""
    blocks = []
    for f in p["funding"]:
        fd = ctx.site["funders"][f["funder"]]
        logo = ""
        if fd.get("logo"):
            light = img_tag(ctx, fd["logo"], ASSETS / fd["logo"], ctx.pick(fd["name"]), "funder__logo")
            if fd.get("logo_dark"):
                logo = (f'<picture><source srcset="{esc(ctx.asset(fd["logo_dark"]))}" media="(prefers-color-scheme: dark)">'
                        f'{light}</picture>')
            else:
                logo = light
            if fd.get("url"):
                logo = f'<a class="funder__link" href="{esc(fd["url"])}">{logo}</a>'
        ref = (f'<p class="funder__ref">{esc(ctx.t("fact.reference"))}: {esc(f["reference"])}</p>'
               if f.get("reference") else "")
        blocks.append(f'    <div class="funder funder--{f["funder"]}">{logo}'
                      f'<p class="funder__statement">{esc(ctx.pick(fd["statement"]))}</p>{ref}</div>')
    return ('<section class="funding" aria-labelledby="funding-title">\n'
            f'  <h2 id="funding-title" class="section-title">{esc(ctx.t("section.funding"))}</h2>\n'
            + "\n".join(blocks) + "\n</section>")


def build_project(ctx, p, prev, nxt):
    facts = [fact(ctx.t("fact.type"), esc(ctx.t("type." + p["type"])), "type"),
             fact(ctx.t("fact.years"), esc(ctx.years(p) + (" " + ctx.t("fact.ongoing") if p.get("ongoing") else "")), "years")]
    if p.get("dates"):
        facts.append(fact(ctx.t("fact.dates"), esc(ctx.pick(p["dates"])), "dates"))
    if p.get("place"):
        facts.append(fact(ctx.t("fact.place"), esc(ctx.pick(p["place"])), "place"))
    for f in p.get("facts", []):
        facts.append(fact(ctx.pick(f["label"]), esc(ctx.pick(f["value"])), "extra"))
    for f in p.get("funding", []):
        if f.get("reference"):
            facts.append(fact(ctx.t("fact.reference"), esc(f["reference"]), "reference"))
    for person in p.get("people", []):
        facts.append(fact(ctx.pick(person["role"]), esc(ctx.names(person["names"])), "people"))
    if p.get("partners"):
        facts.append(fact(ctx.t("fact.partners"), link_list([(x["name"], x.get("url")) for x in p["partners"]]), "partners"))
    if p.get("links"):
        facts.append(fact(ctx.t("fact.links"), link_list([(ctx.pick(x["label"]), x["url"]) for x in p["links"]]), "links"))

    media, kind = project_media(ctx, p, eager=True)
    gallery = ""
    if p["gallery"]:
        figs = "".join(
            f'<figure class="gallery__item">{img_tag(ctx, f"projects/{p["slug"]}/gallery/{g}", p["dir"] / "gallery" / g, "", "gallery__img")}</figure>'
            for g in p["gallery"])
        gallery = f'<section class="gallery"><h2 class="section-title">{esc(ctx.t("section.gallery"))}</h2>{figs}</section>'
    role_note = f'<p class="role-note">{esc(ctx.t("role." + p["role"]))}</p>' if p.get("role") else ""
    pager = []
    for q, key, cls in ((prev, "nav.prev", "prev"), (nxt, "nav.next", "next")):
        if q:
            pager.append(f'    <a class="project-pager__{cls}" href="{ctx.url("/" + q["slug"] + "/")}" rel="{cls}">'
                         f'<span class="project-pager__label">{esc(ctx.t(key))}</span> '
                         f'<span class="project-pager__title">{esc(ctx.pick(q["title"]))}</span></a>')
    content = fill(
        "project", type=p["type"], slug=p["slug"], type_label=esc(ctx.t("type." + p["type"])), years=ctx.years(p),
        title=esc(ctx.pick(p["title"])), summary=esc(ctx.pick(p["summary"])),
        media=f'      <div class="project-hero__frame project-hero__frame--{kind}">{media}</div>',
        facts="\n".join(facts), role_note=role_note, body=body_html(ctx, p["body"]) + gallery,
        books_section=build_books(ctx, ctx.d["books"]) if p["type"] == "book-series" else "",
        funding_section=build_funding(ctx, p), pager_label=esc(ctx.t("nav.projects")), pager="\n".join(pager))
    return page(ctx, path=f"/{p['slug']}/", title=ctx.pick(p["title"]), description=ctx.pick(p["summary"]),
                content=content, body_class=f"project-page project-page--{p['type']}", color=p.get("color"))


def build_page(ctx, pg):
    extra = ""
    site = ctx.site
    if pg.get("show_contact"):
        legal = site["legal"]
        extra = (
            '<dl class="contact">\n'
            f'  <div class="contact__item"><dt>{esc(ctx.t("contact.email"))}</dt><dd><a href="mailto:{esc(site["email"])}">{esc(site["email"])}</a></dd></div>\n'
            f'  <div class="contact__item"><dt>{esc(ctx.t("contact.address"))}</dt><dd>{esc(ctx.pick(site["name"]))}<br>{esc(ctx.pick(site["address"]))}</dd></div>\n'
            '</dl>\n'
            f'<h2 class="section-title">{esc(ctx.t("contact.legal"))}</h2>\n'
            '<dl class="legal">\n'
            f'  <div><dt>{esc(ctx.t("footer.reg"))}</dt><dd>{esc(legal["registration_no"])}</dd></div>\n'
            f'  <div><dt>{esc(ctx.t("contact.court"))}</dt><dd>{esc(ctx.pick(legal["court"]))}</dd></div>\n'
            f'  <div><dt>{esc(ctx.t("footer.tax"))}</dt><dd>{esc(legal["tax_no"])}</dd></div>\n'
            f'  <div><dt>{esc(ctx.t("footer.public_benefit"))}</dt><dd>{legal["public_benefit_since"][:4]}–</dd></div>\n'
            '</dl>')
    if pg.get("show_board"):
        extra += (f'<h2 class="section-title">{esc(ctx.t("contact.board"))}</h2>\n'
                  f'<ul class="board">' + "".join(f"<li>{esc(ctx.name(n))}</li>" for n in site["board"]) + "</ul>")
    content = fill("page", slug=pg["slug"], title=esc(ctx.pick(pg["title"])),
                   body=body_html(ctx, pg["body"]), extra=extra)
    return page(ctx, path=f"/{pg['slug']}/", title=ctx.pick(pg["title"]), description=ctx.pick(pg["summary"]),
                content=content, body_class=f"page-{pg['slug']}")


# ---------------------------------------------------------------- output

def write(rel, text):
    path = OUT / rel.lstrip("/")
    if rel.endswith("/"):
        path = path / "index.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build(draft=False, proof=False, base=None, style=None):
    data = load_content(draft)
    if data is None or errors:
        return data
    if base is not None:
        data["site"]["base_path"] = base
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    # Assets
    shutil.copytree(ASSETS, OUT / "assets")
    if style:
        shutil.copy2(ROOT / style, OUT / "assets" / "style.css")
    shutil.copytree(CONTENT / "covers", OUT / "assets" / "covers")
    for p in data["projects"]:
        dest = OUT / "assets" / "projects" / p["slug"]
        dest.mkdir(parents=True, exist_ok=True)
        for key in ("logo", "cover"):
            if p.get(key):
                shutil.copy2(p["dir"] / p[key], dest / p[key])
        if p["gallery"]:
            shutil.copytree(p["dir"] / "gallery", dest / "gallery")

    paths = []
    for lang in LANGS:
        ctx = Ctx(data, lang)
        pre = PREFIX[lang]
        write(f"{pre}/", build_home(ctx))
        paths.append("/")
        ps = data["projects"]
        for i, p in enumerate(ps):
            write(f"{pre}/{p['slug']}/", build_project(ctx, p, ps[i - 1] if i else None, ps[i + 1] if i + 1 < len(ps) else None))
            paths.append(f"/{p['slug']}/")
        for pg in data["pages"].values():
            write(f"{pre}/{pg['slug']}/", build_page(ctx, pg))
            paths.append(f"/{pg['slug']}/")

    site = data["site"]
    base = site.get("base_path", "").rstrip("/")
    domain = site["domain"].rstrip("/")
    for old, new in REDIRECTS.items():
        write(old, fill("redirect", target=base + new, canonical=domain + new, target_title=esc(domain + new),
                        text_hu=esc(data["i18n"]["redirect.text"]["hu"]), text_en=esc(data["i18n"]["redirect.text"]["en"])))

    ctx = Ctx(data, "hu")
    i = data["i18n"]
    nf = fill("notfound", title_hu=esc(i["404.title"]["hu"]), text_hu=esc(i["404.text"]["hu"]), home_hu=base + "/",
              home_label_hu=esc(i["404.home"]["hu"]), title_en=esc(i["404.title"]["en"]), text_en=esc(i["404.text"]["en"]),
              home_en=base + "/en/", home_label_en=esc(i["404.home"]["en"]))
    write("/404.html", page(ctx, path="/404.html", title=i["404.title"]["hu"], description="", content=nf, body_class="notfound-page", switch_path="/"))

    urls = sorted(set(paths))
    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for u in urls:
        for lang in LANGS:
            alts = "".join(f'<xhtml:link rel="alternate" hreflang="{l}" href="{domain}{PREFIX[l]}{u}"/>' for l in LANGS)
            sitemap.append(f"  <url><loc>{domain}{PREFIX[lang]}{u}</loc>{alts}</url>")
    sitemap.append("</urlset>")
    write("/sitemap.xml", "\n".join(sitemap) + "\n")
    write("/robots.txt", f"User-agent: *\nAllow: /\nSitemap: {domain}/sitemap.xml\n")
    write("/CNAME", domain.split("//", 1)[1] + "\n")
    write("/.nojekyll", "")

    if proof:
        build_proof(data)
    return data


def build_proof(data):
    """Side-by-side HU | EN view of every translatable text, unapproved first. Not published."""
    rows = []

    def row(label, hu, en, ok):
        mark = "✓" if ok else "…"
        rows.append(f'<tr class="{"ok" if ok else "todo"}"><th>{mark} {esc(label)}</th>'
                    f'<td lang="hu">{hu}</td><td lang="en">{en}</td></tr>')

    items = [("projects/" + p["slug"], p) for p in data["projects"]] + [("pages/" + k, v) for k, v in data["pages"].items()]
    items.sort(key=lambda kv: all(kv[1].get("proofread", {}).values()))
    for where, m in items:
        ok = all(m.get("proofread", {}).values())
        rows.append(f'<tr class="group"><th colspan="3">{esc(where)} — HU {"✓" if m["proofread"]["hu"] else "…"} · EN {"✓" if m["proofread"]["en"] else "…"}</th></tr>')
        for key in ("title", "summary", "place", "dates"):
            if m.get(key):
                row(key, esc(m[key]["hu"]), esc(m[key]["en"]), ok)
        block = re.compile(r"<(p|h2|h3|ul|ol|blockquote)[\s>].*?</\1>", re.S)
        # Fallback text is not a translation, so it shows as missing.
        hu_full, en_full = ([x.group(0) for x in block.finditer(m["body"][l][0])] if not m["body"][l][1] else []
                            for l in LANGS)
        for n in range(max(len(hu_full), len(en_full))):
            row(f"¶{n + 1}", hu_full[n] if n < len(hu_full) else '<em class="missing">—</em>',
                en_full[n] if n < len(en_full) else '<em class="missing">—</em>', ok)
    for k, v in data["i18n"].items():
        row(k, esc(v["hu"]), esc(v["en"]), True)
    PROOF.mkdir(exist_ok=True)
    (PROOF / "index.html").write_text(
        '<!doctype html><html><head><meta charset="utf-8"><meta name="robots" content="noindex"><title>Proof HU | EN</title>'
        "<style>body{font:15px/1.5 system-ui;margin:24px}table{border-collapse:collapse;width:100%}"
        "td,th{border-top:1px solid #ddd;padding:8px;vertical-align:top;text-align:left}th{width:12%;font-weight:500;color:#666}"
        "td{width:44%}tr.group th{background:#f3f3f3;color:#000;font-weight:700;padding-top:18px}tr.todo th{color:#b35}"
        ".missing{color:#b35}blockquote{margin:0 0 0 1em}</style></head><body>"
        "<h1>Proofreading: HU | EN</h1><p>Unapproved items first. Set <code>proofread</code> in meta.json when a page is approved.</p>"
        "<table>" + "".join(rows) + "</table></body></html>", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--draft", action="store_true", help="allow missing translations")
    ap.add_argument("--serve", action="store_true", help="serve docs/ after building")
    ap.add_argument("--proof", action="store_true", help="write proof/index.html")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--out", help="output folder instead of docs/ (for design previews)")
    ap.add_argument("--base", help="URL base path, e.g. /a (overrides site.json base_path)")
    ap.add_argument("--style", help="use this stylesheet instead of assets/style.css")
    args = ap.parse_args()

    global OUT
    if args.out:
        OUT = (ROOT / args.out).resolve()
    data = build(draft=args.draft, proof=args.proof, base=args.base, style=args.style)
    for w in warnings:
        print(f"  warning: {w}")
    if errors:
        for e in errors:
            print(f"  ERROR: {e}")
        print(f"Build failed with {len(errors)} error(s). Nothing was written.")
        sys.exit(1)
    done = sum(all(m.get("proofread", {}).values()) for m in list(data["projects"]) + list(data["pages"].values()))
    total = len(data["projects"]) + len(data["pages"])
    print(f"Built {OUT.relative_to(ROOT)}/ · {len(data['projects'])} projects, {len(data['books'])} books, "
          f"{len(data['pages'])} pages × {len(LANGS)} languages · proofread {done}/{total}"
          + (" · DRAFT" if args.draft else ""))
    if args.serve:
        handler = lambda *a, **kw: http.server.SimpleHTTPRequestHandler(*a, directory=str(OUT), **kw)
        print(f"Serving on http://localhost:{args.port}/  (Ctrl+C to stop)")
        http.server.ThreadingHTTPServer(("127.0.0.1", args.port), handler).serve_forever()


if __name__ == "__main__":
    main()
