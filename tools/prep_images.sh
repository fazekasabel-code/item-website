#!/bin/zsh
# One-off: copy recovered images from legacy/ into content/ and assets/,
# converting mislabelled WebP files to real JPEG and capping sizes.
# Needs only macOS `sips` (and pdftocairo for nothing here). Safe to re-run.
set -e
cd "${0:A:h}/.."
U=legacy/site/wp-content/uploads
F=legacy/found_images

jpg() { sips -s format jpeg -s formatOptions 82 -Z ${3:-1400} "$1" --out "$2" >/dev/null; }
png() { sips -s format png -Z ${3:-1000} "$1" --out "$2" >/dev/null; }

# Book covers -> content/covers/<book-slug>.jpg
jpg "$U/2024/03/SZEMES_borito_print_VEGLEGES_kivagva-scaled-e1710838483612.jpg" content/covers/digitalis-irodalomtudomany.jpg
jpg "$U/2024/03/11224374-1027x1536.jpg"   content/covers/a-betegseg-kepei.jpg
jpg "$U/2024/03/latour2.jpg"              content/covers/foldkozelben-karantenban.jpg
jpg "$U/2024/03/vörös.jpg"                content/covers/arnyekvers-es-ironia.jpg
jpg "$U/2024/03/lovecraft.jpg"            content/covers/poszthumanista-olvasatok.jpg
jpg "$U/2024/03/ureczky.jpg"              content/covers/kultura-es-kontaminacio.jpg
jpg "$U/2024/03/marjanovics.jpg"          content/covers/orokolt-blende.jpg
jpg "$U/2024/03/tanos.jpg"                content/covers/regenyparhuzamok.jpg
jpg "$U/2020/07/latour_1.jpg"             content/covers/hibrid-gondolkodas.jpg
jpg "$U/2020/07/transzmediajav.jpg"       content/covers/transzmedia.jpg
jpg "$U/2024/03/ser.jpg"                  content/covers/a-termeszeti-szerzodes.jpg
jpg "$U/2020/07/hatar_vegleges_kontrasztos.jpg" content/covers/a-hatarsertes-technologiai.jpg
# NOTE: legacy agamben.jpg is "A nyitott", NOT Studiolo -> deliberately not used.

# Project logos
P=content/projects
png "$U/elementor/thumbs/kijarat-kiado-qlfl7qhid8gkelhd16m7lftg65erbi6vijyw73svp0.png" $P/kijarat/logo.png 500
png "$U/2020/07/Hibiki-Logo-Kicsi.png"     $P/hibiki/logo.png 409
png "$U/2024/03/neurodiverz_logo_honlap-kek_nincs-space.png" $P/neurodiverz-xyz/logo.png 900
png "$U/2024/03/ff.png"                    $P/freshfabrik/logo.png 400
png "$U/2021/11/egyben.png"                $P/a-computational-stylistic-group-bemutatasa/logo.png 540

# Brand + funders
cp "$U/2020/07/cropped-logo_vegleges.jpg"  assets/brand/item-logo.jpg
png "$U/2020/07/cropped-logo_vegleges-1-192x192.jpg" assets/brand/favicon.png 192
png "$U/2024/03/EN-Co-Funded-by-the-EU_BLACK-Outline-2048x430.png" assets/funders/eu-cofunded-en-black.png 1200
jpg "$U/2024/09/EN-Co-funded-by-the-EU_POS-2048x430.jpg"          assets/funders/eu-cofunded-en-pos.jpg 1200
cp $F/visegrad/VF-logotype-black.png assets/funders/visegrad-black.png
cp $F/visegrad/VF-logotype-white.png assets/funders/visegrad-white.png
cp legacy/site/wp-content/themes/zita/third-party/fonts/Catamaran-Regular.ttf assets/fonts/Catamaran-Variable.ttf
echo done
