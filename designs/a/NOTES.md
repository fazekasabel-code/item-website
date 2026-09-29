# Direction A: Editorial archive
Idea: printed matter of a small publisher. Hairline-ruled index, plates for media, narrow labelled facts sidebar, 65ch reading column.
Fonts: Catamaran (UI, labels; loaded via relative `fonts/Catamaran-Variable.ttf` from assets/style.css) + system serif stack (Iowan Old Style, Palatino, Charter, Georgia) for text and titles; ui-monospace for numbers/years.
Colours: paper #f5f1e8 / ink #1d1b17; dark #141310 / #ebe5d7; single accent I.T.E.M. red (#c4202a light, #ff7378 dark). `--project-color` only as thin rules (card top, hero type tag, facts top rule, preview top).
Typo cover: printed-cover look, tinted 24% by `--cover-color` over warm grey; stays light in dark mode (it is an object).
Dark mode: header logo and EU funder logos get a white plate; Visegrad gets none because the build swaps in its white PNG.
Gaps: (1) build.py --out did not copy assets/fonts/ into previews (folder was empty), so Catamaran falls back to system sans unless the build copies fonts; (2) the ".project-row__years" is placed by grid-area, no markup changes needed; (3) no burger: nav wraps onto two lines on phones.
