# Direction B: the frame and the picture
- Idea: neutral off-white/near-black chrome; every project page opens with a full-bleed hero in `--project-color`, home cards are colour tiles.
- Font: Catamaran variable (weights 400-900), loaded via relative `fonts/Catamaran-Variable.ttf`; system-ui fallback.
- Colours: paper #fbfaf7 / ink #16171a (dark: #121316 / #f2f0ea); I.T.E.M. red only as current-nav underline and small marks, mint as dark-mode focus ring. No-colour projects get ink #23252b hero.
- Text on project colour is picked with relative colour syntax `oklch(from var(--c) ...)` (black/white switch at L=0.6). Browsers without it get a darkened colour (55% mix with black) and white text.
- Typo covers have no `--cover-color` in the markup: they use the project colour; in hero/cards they turn white; book covers rotate blue/red/mint/ink via `.book:nth-child`.
- Not solvable in CSS: index rows only carry `data-color` (not a style var), so the row's colour bar is ink, and only the hover preview takes the colour (JS sets it). Setting `style="--project-color"` on `.project-row` would fix it.
- Funder logos sit on white plates (Visegrad dark-mode white logo on a dark plate); never filtered.
