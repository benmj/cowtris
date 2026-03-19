# Cowtris — Agent Instructions

## Overview
Cowtris is a Tetris variant with cow breeds as pieces, served at `cowtris.benbybenjacobs.com`.
- Game: `web/index.html` (single-file HTML5 canvas app)
- API + static server: `web/api/server.ts` (Bun, port 3210)
- Changelog page: `web/changelog.html`
- Live files: `/srv/benbybenjacobs.com/cowtris/` on Benito (Mac Mini, Tailscale `100.99.252.37`)

## After every commit

**Always update `web/changelog.html`** to include the new commit. Add an entry under the correct date group (or create a new group if the date is different), following the existing format:

```html
<li><a class="commit-link" href="https://github.com/benmj/cowtris/commit/HASH" target="_blank" rel="noopener">HASH</a> Brief plain-English description of the change</li>
```

- Use the short (7-char) commit hash
- Keep descriptions brief and user-facing (what changed, not how)
- Newest entries go at the top (newest date group first, newest entry first within a group)
- After updating changelog.html, also sync it to the live server:
  `cp ~/code/cowtris/web/changelog.html /srv/benbybenjacobs.com/cowtris/changelog.html`

## Deploying changes

After editing any file under `web/`, sync it to the live server before committing:
```
cp ~/code/cowtris/web/<file> /srv/benbybenjacobs.com/cowtris/<file>
```

Then commit and push:
```
cd ~/code/cowtris
git add web/
git commit -m "..."
git push origin master
```

Use SSH remote: `git@github.com:benmj/cowtris.git`
