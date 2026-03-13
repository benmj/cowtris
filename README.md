# Cowtris

A falling block game with cows.

**Play now at [cowtris.benbybenjacobs.com](https://cowtris.benbybenjacobs.com)**

![Cowtris Screenshot](https://raw.github.com/benmj/cowtris/master/resources/images/cowtris_1_lg.gif)

## History

Cowtris was originally coded in Visual Basic by David Glick (davisagli) and published by Nonsense Software circa 2000–2003. NS was four teenagers from Indiana who made computer games, biked, and built model recreations of medieval weaponry. In terms of games, Cowtris was their finest work and its legacy casts the longest shadow.

**Cowtris 3** (2013) ported the game to HTML5/JavaScript by [Ben Jacobs](https://benbybenjacobs.com), preserving the original sprites, sounds, and gameplay.

**Cowtris 2026** is a complete rewrite as a self-contained, mobile-friendly HTML5 canvas game with a shared online scoreboard. Every line of the 2026 port was generated through a conversational prompt session between Ben and [Claude](https://claude.ai) (Anthropic) — layout, game logic, sprite rendering, API server, and deployment. The original game assets (sprites and sound effects) are preserved faithfully.

See [readme-2.1.md](readme-2.1.md) for the original Nonsense Software description.

## 2026 Port

The current version lives in the `web/` directory:

- **`web/index.html`** — Complete game: canvas rendering, touch controls, responsive layout, scoreboard UI
- **`web/api/server.ts`** — Bun server handling game HTML, static assets, and scoreboard API (SQLite)
- **`web/assets/`** — Original sprite sheets and sound effects

### Features

- Faithful to original game mechanics (no ghost piece, no wall kicks, space = fast advance)
- Original cow breed sprites and sound effects
- Responsive side-by-side layout that works on mobile and desktop
- Shared online scoreboard with rate limiting
- Dark mode toggle
- Touch controls with hold-to-repeat

### Running locally

```bash
# Requires Bun (https://bun.sh)
cd web/api
bun run server.ts
# Open http://localhost:3210
```

### How it was built

The entire 2026 port was built in a single Claude Code session. Ben described what he wanted — a mobile-compatible port of the original cowtris with a shared scoreboard — and Claude wrote every file: the game HTML/CSS/JS, the Bun API server, the launchd plist for process management, and the Cloudflare tunnel configuration for deployment. The conversation included iterative visual design passes using headless Chrome screenshots.

## Original Version (2013)

The 2013 HTML5 port is preserved in the root directory (`index.html`, `javascripts/`, `stylesheets/`, `images/`).

To play the original version, open `index.html` in a browser. High scores require serving from a web server (localStorage limitation).

## License

GNU General Public License (see original readme-2.1.md).
