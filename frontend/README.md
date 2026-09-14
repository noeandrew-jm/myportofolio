# Liquid Glass buttons

The portfolio uses the actual React component from the supplied
`liquid-glass-react-master.zip` (package version 1.1.1), vendored under
`vendor/liquid-glass-react/`. Its original MIT license is included there and
in the generated browser bundle. Only source files and the license were copied;
the archive's demo, videos and install scripts are not used.

## Development

The generated `static/js/liquid-glass.js` is included in the project. Running
Django or deploying this bundle does **not** require Node.js or an npm install
on PWS. No CDN or third-party runtime requests are used.

After changing the React source, rebuild locally with Node.js and npm:

```powershell
npm.cmd ci --ignore-scripts
npm.cmd run build
```

Keep `package-lock.json`, the source and the rebuilt browser bundle together
when you choose to commit/deploy. `node_modules/` is ignored.

## Django integration

`templates/base.html` loads the bundle. Navigation and contact links use
`.glass-button` with a `.glass-button__label` span. React renders only the
decorative, `aria-hidden` layer: native hrefs, keyboard navigation and link
context menus are unchanged. CSS supplies a glass-like fallback without JS,
keyboard focus rings, touch/pressed states and reduced-motion support.

The plain white page background is `--paper: #FFFFFF` in `static/css/style.css`.
Button reflections and shadows remain intentionally visible over this light
background. Firefox and Safari have limited SVG refraction support (as noted
by the original library), so their appearance can differ from Chromium/Edge.

## Small local changes to the upstream source

- Each SVG image has a unique ID for multiple buttons on one page.
- Glass dimensions use `ResizeObserver` and untransformed element dimensions,
  so resizing or font changes do not misalign the glass.
- Added the prefixed backdrop filter for compatible WebKit browsers.
- The Firefox filter fallback uses `undefined` instead of `null`.

The adapter supplies pointer positions and resets them on pointer leave; the
native links provide hover/press feedback. Scoped CSS replaces the handful of
Tailwind presentation utilities needed here and softens the library's dark
demo shadow for the light theme. No Tailwind or React app conversion is
required.
