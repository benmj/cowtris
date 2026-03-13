import { Database } from "bun:sqlite";
import { resolve } from "path";

const DB_PATH = resolve(import.meta.dir, "cowtris.db");
const db = new Database(DB_PATH);
db.run("PRAGMA journal_mode=WAL");
db.run(`
  CREATE TABLE IF NOT EXISTS scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    score INTEGER NOT NULL,
    rows_cleared INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
  )
`);
db.run(`CREATE INDEX IF NOT EXISTS idx_scores_score ON scores(score DESC)`);

const COWTRIS_DIR = resolve(import.meta.dir, "..");
const GAME_HTML_PATH = resolve(COWTRIS_DIR, "index.html");

const MIME_TYPES: Record<string, string> = {
  ".png": "image/png",
  ".wav": "audio/wav",
  ".jpg": "image/jpeg",
  ".gif": "image/gif",
  ".css": "text/css",
  ".js": "application/javascript",
};

const PORT = 3210;

// Simple rate limiting: max 5 submissions per IP per minute
const rateMap = new Map<string, number[]>();

function isRateLimited(ip: string): boolean {
  const now = Date.now();
  const window = 60_000;
  const max = 5;
  let timestamps = rateMap.get(ip) || [];
  timestamps = timestamps.filter((t) => now - t < window);
  if (timestamps.length >= max) return true;
  timestamps.push(now);
  rateMap.set(ip, timestamps);
  return false;
}

// Clean up rate map every 5 minutes
setInterval(() => {
  const now = Date.now();
  for (const [ip, ts] of rateMap) {
    const filtered = ts.filter((t) => now - t < 60_000);
    if (filtered.length === 0) rateMap.delete(ip);
    else rateMap.set(ip, filtered);
  }
}, 300_000);

const getScores = db.prepare(
  "SELECT name, score, rows_cleared, created_at FROM scores ORDER BY score DESC LIMIT 15"
);

const insertScore = db.prepare(
  "INSERT INTO scores (name, score, rows_cleared) VALUES (?, ?, ?)"
);

Bun.serve({
  port: PORT,
  async fetch(req) {
    const url = new URL(req.url);
    const path = url.pathname.replace(/\/+$/, "") || "/";

    // CORS preflight
    if (req.method === "OPTIONS") {
      return new Response(null, {
        status: 204,
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
          "Access-Control-Allow-Headers": "Content-Type",
        },
      });
    }

    // ── API: GET scores ──
    if (path === "/api/scores" && req.method === "GET") {
      return Response.json(getScores.all());
    }

    // ── API: POST score ──
    if (path === "/api/scores" && req.method === "POST") {
      const ip =
        req.headers.get("x-forwarded-for")?.split(",")[0]?.trim() || "unknown";
      if (isRateLimited(ip)) {
        return Response.json({ error: "Too many requests" }, { status: 429 });
      }

      try {
        const body: any = await req.json();
        const name =
          String(body.name || "")
            .trim()
            .slice(0, 20) || "Anonymous";
        const score = Math.max(0, Math.floor(Number(body.score) || 0));
        const rows = Math.max(0, Math.floor(Number(body.rows_cleared) || 0));

        if (score === 0) {
          return Response.json({ error: "Invalid score" }, { status: 400 });
        }

        insertScore.run(name, score, rows);
        return Response.json(getScores.all(), { status: 201 });
      } catch {
        return Response.json({ error: "Invalid JSON" }, { status: 400 });
      }
    }

    // ── Serve game HTML ──
    if (path === "/" || path === "") {
      const file = Bun.file(GAME_HTML_PATH);
      return new Response(file, {
        headers: { "Content-Type": "text/html; charset=utf-8" },
      });
    }

    // ── Serve static assets (images, sounds) ──
    if (path.startsWith("/assets/")) {
      const safePath = path.replace(/\.\./g, "");
      const filePath = resolve(COWTRIS_DIR, safePath.slice(1));
      const file = Bun.file(filePath);
      if (await file.exists()) {
        const ext = safePath.substring(safePath.lastIndexOf("."));
        const contentType = MIME_TYPES[ext] || "application/octet-stream";
        return new Response(file, {
          headers: {
            "Content-Type": contentType,
            "Cache-Control": "public, max-age=86400",
          },
        });
      }
    }

    return Response.json({ error: "Not found" }, { status: 404 });
  },
});

console.log(`Cowtris running on http://localhost:${PORT}`);
