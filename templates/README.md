# Markup contract

The HTML is generated from these templates and is the **same for every design**. A design is a
single stylesheet (`assets/style.css`) and must not require markup changes. Class names below are
stable. Colours of a project arrive as the CSS custom property `--project-color` (set on `<body>`
of a project page, on `.project-card`, and on `.index-preview` by `preview.js`) and `--cover-color`
on `.typo-cover`. Either may be absent, so always provide a fallback.

## Every page (`base.html`)
```
body.home | body.project-page.project-page--<type> | body.page-rolunk | body.page-kapcsolat | body.notfound-page
  a.skip-link
  header.site-header
    a.site-header__brand > img.site-header__logo          (I.T.E.M. logo, 656×200 JPEG, white background)
    nav.site-nav > ul.site-nav__list > li.site-nav__item > a.site-nav__link[aria-current=page]
                 + a.site-nav__lang                        (EN / HU switch)
  main#main.site-main
  footer.site-footer
    .site-footer__org > p.site-footer__name, p.site-footer__address, p.site-footer__email
    dl.site-footer__legal > div > dt + dd                  (registration no., tax no., public benefit)
    p.site-footer__copy
```

## Home (`home.html`)
```
section.home-intro > h1.home-intro__title, p.home-intro__tagline, p.home-intro__text
section.current-projects > h2.section-title, ul.current-projects__list
  li.project-card.project-card--(logo|cover|typo)[style=--project-color] > a.project-card__link
    div.project-card__media > (img.project-logo | img.project-cover | div.typo-cover)
    p.project-card__kicker > span (type) + span (years)
    h3.project-card__title, p.project-card__summary
section.project-index > h2.section-title, ol.project-index__list
  li.project-row[data-type][data-color] > a.project-row__link
    span.project-row__num, .project-row__title, .project-row__type, .project-row__years, .project-row__summary
    span.project-row__preview[hidden]        (copy of the media, used by preview.js)
section.book-strip > h2.section-title > a, ul.book-strip__list > li.book-strip__item > a > img.book-strip__cover
  p.book-strip__more > a
div.index-preview(.is-visible)               (created by preview.js on hover devices; position: fixed; moved via transform)
```

## Project page (`project.html`)
```
article.project.project--<type>[data-slug]
  header.project-hero
    .project-hero__text > p.project-hero__kicker > span.project-hero__type + span.project-hero__years
                          h1.project-hero__title, p.project-hero__summary
    .project-hero__media > div.project-hero__frame.project-hero__frame--(logo|cover|typo) > img | div.typo-cover
  div.project-layout
    aside.project-facts > dl.facts > div.facts__item.facts__item--(type|years|dates|place|extra|reference|people|partners|links) > dt + dd
                                      (partners/links: dd > ul.facts__list > li > a)
    div.project-body > p.role-note?, p.fallback-notice?, div.prose[lang?] (h2 h3 p ul ol li blockquote a em strong)
                       section.gallery?
  section.books#books  (Kijárat only) > h2.section-title > span.books__count, p.books__note?, ol.books__list
    li.book#<slug> > div.book__media > (img.book__cover | div.typo-cover.typo-cover--book)
                     div.book__text > h3.book__title[lang=hu?], p.book__subtitle?, p.book__gloss?,
                                      dl.book__meta > div > dt + dd, p.book__shop > a
  section.funding > h2.section-title, div.funder.funder--<key> > (a.funder__link >)? (picture >)? img.funder__logo,
                    p.funder__statement, p.funder__ref?
  nav.project-pager > a.project-pager__prev / __next > span.project-pager__label + span.project-pager__title
```

## Text pages (`page.html`)
```
article.page.page--(rolunk|kapcsolat) > header.page-header > h1.page-header__title
  div.page-body > div.prose, dl.contact > div.contact__item > dt + dd, h2.section-title, dl.legal > div > dt + dd, ul.board
```

## Fixed rules for any design
- Funder logos (EU, Visegrad) must not be recoloured, filtered, cropped or placed on busy backgrounds.
  The Visegrad logo needs clear space, and a white version is swapped in automatically in dark mode.
- The I.T.E.M. logo is a JPEG on white. Place it on white/near-white or frame it.
- Must work from 320 px wide, with no horizontal page scroll, visible focus states and `prefers-reduced-motion`.
- Hungarian characters (ő ű Ő Ű) must render in the chosen fonts.
