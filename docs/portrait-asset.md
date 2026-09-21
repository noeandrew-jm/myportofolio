# Profile portrait asset

- Source: `static/image/noe.png` (1414 × 2000, opaque RGB).
- Website asset: `static/image/noe-cutout.png` (1055 × 1491, RGBA with transparent background).
- Method: built-in imagegen, background extraction edit. The original is retained.
- Display: a centered portrait layered in front of live SVG typography in the
  profile section; desktop framing emphasizes the upper body.

## Edit prompt

Use case: background-extraction. Edit target: the supplied local noe.png photograph.
Remove ONLY the white background and large empty white canvas around this person.
Produce an actual transparent PNG alpha cutout of the EXACT same photographed
person, with a tight portrait crop around his existing silhouette and a small 2%
transparent margin. Keep his identity, facial features, skin texture, original
lighting, haircut, pose, hand position, black leather jacket, white top, hanging
sunglasses, necklaces, blue jeans and red bandana EXACTLY as photographed. Preserve
the white top as opaque clothing; remove only the background surrounding him
including the negative spaces around the arms. No beautification, no relighting,
no regenerated face, no new body parts, no new clothing. Preserve the original
bottom crop. No text, no graphics, no shadow or ground, no frame, no scene behind
him. This cutout will be layered in front of large type on a dark portfolio webpage.
