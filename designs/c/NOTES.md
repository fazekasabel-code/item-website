# Direction C: Swiss catalogue / index
- Idea: exhibition catalogue. 12-col grid (faint column guides on desktop via body::before), flush-left, 2px black section rules, hairline rows, no shadows/radii.
- Fonts: Catamaran (variable, 400-800, loaded from fonts/ next to style.css) + ui-monospace for all metadata (kickers, facts, book meta, nav, footer legal).
- Colour: black/white + true dark mode. Only accent is I.T.E.M. mint #7fe3b0, used as a FILL (hover, current nav, :target) always with black text; focus ring is red #c4161b on light, mint on dark. --project-color only as swatch/top bar.
- Logos (I.T.E.M., project logos, funders) sit on white plates in both modes.
- Not solvable in CSS: the project-index column header ("No. / Projekt / Tipus / Ev") is a single ::before string, so it is not aligned to the columns (HU/EN via :lang). typo-cover text is black on --cover-color lightened 50%; very dark project colours may still be low-contrast. Preview showed funder/logo images 404 only because previews use /assets without the /c base.
