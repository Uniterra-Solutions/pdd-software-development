# Browser harness over a built bundle

Depth for any task whose verification drives a real browser against a production build: visual
regression baselines, computed-style sweeps, font readiness, accessible-name snapshots. Load it when a
property's observation is a `getComputedStyle` read, a screenshot, a `document.fonts` query, or a
role/name pair.

## Config that binds where it claims to

```ts
webServer: {
  command: 'npm run build:web && npm run preview:web -- --port 4399 --strictPort --host 127.0.0.1',
  url: 'http://127.0.0.1:4399',
  reuseExistingServer: false,
  timeout: 120000,
},
use: { baseURL: 'http://127.0.0.1:4399' },
```

- **`--host 127.0.0.1` decides whether the readiness check ever answers.** On macOS `vite preview` binds
  `[::1]` alone without it, so a `url` of `http://127.0.0.1:<port>` stays silent and the run dies at the
  readiness timeout with a message blaming the server start rather than the host mismatch. Check the
  listener (`lsof -nP -iTCP:<port> -sTCP:LISTEN`) before diagnosing the application.
- **`--strictPort` plus `reuseExistingServer: false`.** Without both, an occupied port is either silently
  reused — every capture describes a foreign application — or silently shifted, leaving `baseURL`
  pointing at nothing.
- **One builder at a time.** `vite build` empties its out-dir. Two tasks building into it concurrently
  leave a tree missing the other's assets, and both report success.
- **Single browser project, `maxDiffPixels: 0`, explicit `snapshotPathTemplate`.** A second engine brings
  uncontrolled UA drawing (scrollbar shape, form controls) into every diff and the baseline becomes
  unfixable rather than wrong.

## Fonts

`document.fonts.check('<weight> <size> "<family>"')` is **false until that face has loaded**, and nothing
loads a face that no element uses yet. Force it, then check:

```ts
await page.evaluate(() => document.fonts.load('400 13px "Inter"'));
expect(await page.evaluate(() => document.fonts.check('400 13px "Inter"'))).toBe(true);
```

A rejected `load()` means the file is missing or corrupt — exactly the failure the check wants. A
bare `check()` before any element uses the family proves nothing and will fail for the wrong reason.

**A subset webfont carries exactly the glyphs its sources can render.** Subset from the UI source plus the
seeded data, commit the `.woff2` artefacts, and guard the set with a test that recomputes it. Python font
tooling lives in a maintainer command, because the container build usually ships no Python.

**A reproducible rebuild is what makes the committed artefact trustworthy.** Pass `--no-recalc-timestamp`,
pin the upstream font version, and hash the output (`shasum -a 256`) across two runs of the maintainer
command before committing. A subsetter that rewrites bytes on every run leaves "is the shipped font
current?" unanswerable and turns a no-op rebuild into a diff.

## Accessible names in jsdom

`@testing-library/dom` v10 does **not** export `computeAccessibleName`. Use the package it already
depends on:

```ts
import { computeAccessibleName, getRole } from 'dom-accessibility-api';
```

Declare it in devDependencies (it is in the tree as a transitive dependency, so this adds nothing).

Freeze the `role|name` pairs as a literal array in the test, never `toMatchSnapshot()`: a snapshot file
writes itself on first run, so it can never be wrong. Expect `''` names legitimately — name-from-author
roles (`alert`, an unnamed `form`, an unnamed `search`) freeze as `alert|`.

## Chromium control quirks that decide a sweep

A control sweep fails on UA behaviour, not on the stylesheet, until these are normalised. Each one looks
like a styling preference and is actually a precondition for the measurement:

- **`select` reports `line-height: normal` while natively rendered.** No author declaration changes it —
  `!important`, percentages, `calc` and unitless numbers all lose to the UA menulist. Any "line-height
  matches the tier ratio" sweep therefore fails on every `select` and its `option` children until
  `appearance: none`. Normalising appearance is a prerequisite for the measurement, not decoration.
- **Form controls do not inherit text.** `input`, `textarea`, `select` and `button` carry a UA font-size
  of 13.3333px, which is on nobody's scale. `font: inherit` (or an explicit size) belongs in the base
  layer, or the all-element font-size sweep rejects every control on the page.
- **`min-height` alone does not pin a height.** Under `box-sizing: border-box` a control with a UA 2px
  border computes 24.14px for `min-height: 24px`; assert `height`, or set the border, before claiming
  the density number.
- **`:focus-visible` is keyboard-only.** `element.focus()` on a button does not match it (text inputs
  are the exception), so a sweep that calls `focus()` reports the UA ring or nothing and its witness
  never fires. Drive real `page.keyboard.press('Tab')` presses and read `document.activeElement`.
- **`input[type=datetime-local]` emits several tab stops while `activeElement` stays the same input.**
  A loop that stops on a repeated `activeElement` covers one element and passes vacuously. Dedupe by DOM
  path, stop when focus returns to `<body>`, cap the presses, and assert the unique count is non-zero.

## Determinism

- `await page.evaluate(() => document.fonts.ready)` before any capture.
- Stub **every** `/api/**` call with `page.route`; the harness must run with no backend, no database.
- Fixed timestamps in fixtures. Never `Date.now()` in a rendered field.
- `vite preview` also applies `server.proxy` from the Vite config, so an un-stubbed API call logs
  `ECONNREFUSED` to the dev backend. That is noise, not a failure — but treat any un-stubbed request as
  a fixture gap.

## What a sweep proves, and where another primitive is needed

A computed-style sweep proves the properties it reads and nothing else. Where the stylesheet never reached
the document, an empty page passes an "every element" claim vacuously; assert the loading seam first —
`document.styleSheets.length >= 1`, or one token resolving on `:root` — then sweep.

Some claims need a different primitive than `getComputedStyle` on elements:

- **"nothing animates"** — an unused `@keyframes` block changes no element's computed style, so no
  element sweep can see it. Walk `document.styleSheets`, read `sheet.cssRules`, and count rules whose
  `type === CSSRule.KEYFRAMES_RULE`; assert zero. Cross-origin sheets throw on `cssRules`, so read only
  same-origin ones.
- **"no pseudo-element is rounded / shadowed / over-bordered"** — `getComputedStyle(el)` reports the
  element's own box and style and never `el::before` or `el::after`. An element sweep therefore cannot
  see a pseudo-element's border, radius or shadow, and "every border is 1px" silently exempts them.
  Read the pseudo explicitly (`getComputedStyle(el, '::before')`) when that is the claim, and decide on
  purpose whether the invariant covers drawn decoration: a check glyph needs 2px strokes to stay legible
  at 12px, a layout divider never does.
- **"the guard would reject a violation"** — a sweep that has never failed is indistinguishable from one
  that cannot. Inject the violation at runtime (`page.addStyleTag`) or via a temporary stylesheet edit,
  assert the sweep goes red with the offending selector in the message, then restore and re-run green.
  Without that mutation the green is hearsay.
