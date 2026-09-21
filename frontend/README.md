# Portfolio frontend

Django renders every page and all portfolio content. Small local React bundles
enhance the active navigation button and the homepage personal-name hero. The generated
JavaScript and CSS are included in the project, so running Django or deploying to
PWS does not require Node.js or npm.

## Development

After changing a frontend source or the homepage's Tailwind classes, rebuild
locally with Node.js and npm:

```powershell
npm.cmd ci --ignore-scripts
npm.cmd run build
```

`frontend/build.mjs` produces:

- `static/js/liquid-glass.js` from `frontend/liquid-glass-buttons.tsx`.
- `static/js/about.js` from `frontend/about.tsx` with React and Framer Motion.
- `static/css/about.css` from `frontend/about.css`, using Tailwind CSS and PostCSS.

Tailwind reads only the About component and `templates/index.html`, prefixes
utilities with `tw-`, and disables preflight to avoid changing other Django pages.
Keep `package-lock.json`, source files, and rebuilt assets together when committing
or deploying. `node_modules/` is ignored. Libraries run from the local bundles;
Kanit is requested from Google Fonts with a system sans-serif fallback. The whole
profile uses the same font and purple, pink, blue and black palette.

## Homepage hero and profile

Only `templates/index.html` loads the About bundle and stylesheet. Django renders
a complete static hero, including the real `name`, `bio`, corner artwork and the
Contact Me link. Escaped data attributes supply the name, bio and static asset
URLs to React.
The fallback remains functional when JavaScript is unavailable.

Framer Motion adds the reusable `FadeIn` entrance animation and scroll-driven
character reveal. Characters remain grouped into words for normal line wrapping.
Screen readers receive the complete paragraph once; decorative character layers
are hidden from accessibility APIs. Reduced motion shows the full paragraph and
disables movement. The Contact Me link targets the existing profile's contact
links at `#contact`.

The design uses the shared font and color variables from `static/css/style.css`:
Kanit, background `#0C0C0C`, metallic hero text and blue/purple/pink accents.
The profile inherits those same tokens and the contact buttons use the navbar's
glass surface. The four supplied decorative images are stored in
`static/image/about/`. The profile below the hero uses an editorial layout with
the transparent `noe-cutout.png` portrait centered in front of an oversized `Portofolio`
wordmark. Personal details and contact links remain server-rendered around the
portrait. The former Focus Area section, star seal and extra contact CTA have
been removed. Email, GitHub and LinkedIn share the navigation's liquid-glass
effect in a centered row below the portrait.

The supplied `static/image/noe.png` has an opaque white background. Its transparent
derivative is saved separately at `static/image/noe-cutout.png`; the source file
is unchanged. The built-in imagegen edit tool produced the derivative. See
[`docs/portrait-asset.md`](../docs/portrait-asset.md) for the edit prompt.

## Active navigation glass

The portfolio uses the React component from the supplied
`liquid-glass-react-master.zip` (package version 1.1.1), vendored under
`vendor/liquid-glass-react/`. Its original MIT license is included there and in
the generated browser bundle. Only source files and the license were copied;
the archive's demo, videos and install scripts are not used.

`templates/base.html` loads the glass bundle on each page. All navigation links
share one `.nav-group`, and only the link with `aria-current="page"` receives the
`.glass-button` class. React renders only its decorative `aria-hidden` layer;
native hrefs, keyboard navigation, labels and link context menus remain intact.
CSS supplies the active effect without JavaScript, focus rings, touch states,
and reduced-motion support. The three `.profile-contact-link` anchors explicitly
opt into the same effect; inactive navigation links remain plain.

## Moving cards

Achievements, Experience and Projects extend `showcase_base.html`, which itself
extends the root template and loads `static/css/showcase.css` and
`static/js/showcase.js`. Cards drift left continuously, loop seamlessly and pause
on hover. Keyboard interaction, open confirmation dialogs, touch dragging and
reduced-motion preferences also suspend automatic movement.

Repeated groups are decorative and hidden from screen readers. Their actions
delegate to original links and buttons. Copies contain no forms, IDs or dialogs,
so project deletion keeps one CSRF-protected form and confirmation per record.
Without JavaScript, the original cards are horizontally scrollable.

The esbuild workspace resolver feeds local source through Node. This avoids
native esbuild scanning inaccessible ancestor directories on restricted Windows
environments while keeping the build inside the workspace.

Firefox and Safari have limited SVG refraction support (as noted by the original
library), so their appearance can differ from Chromium/Edge.

## Small local changes to the upstream source

- Each SVG image has a unique ID for multiple buttons on one page.
- Glass dimensions use `ResizeObserver` and untransformed element dimensions,
  so resizing or font changes do not misalign the glass.
- Added the prefixed backdrop filter for compatible WebKit browsers.
- The Firefox filter fallback uses `undefined` instead of `null`.

The adapter supplies pointer positions and resets them on pointer leave; the
native links provide hover/press feedback. The glass bundle uses scoped CSS for
the upstream presentation utilities. React, React DOM and Framer Motion license
notices are retained in the generated bundles.
