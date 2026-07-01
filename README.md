# dhwani's orbit

A tiny static blog. Pink + yellow, dark space theme. Markdown in, HTML out, hosted free on GitHub Pages.

## How it works

```
blog/
├── posts/            ← you write markdown files here. THIS is "uploading a post."
├── templates/         ← HTML skeleton for pages (rarely touched)
├── static/style.css   ← the pink/yellow theme (rarely touched)
├── build.py            ← converts posts/*.md into docs/*.html
└── docs/                ← the actual generated website (never hand-edit — build.py owns it)
```

There is no login page, no upload button, no backend, no database. The site is just files.
The only way new content appears on the live site is:

1. you write/edit a `.md` file in `posts/`
2. you run `python3 build.py` locally
3. you `git push` to GitHub

That last step is the real gatekeeper. **Only accounts with push access to your GitHub repo
can change the site — by default that's only you.** Nobody can "log in" and post because
there's nothing to log into. If you ever add a collaborator on GitHub, they could also push
posts; until then, it's just you. This is the standard way solo static blogs (Jekyll, Hugo,
Astro, etc.) enforce single-author control — git access *is* the auth system.

## Writing a new post

Create a new file in `posts/`, named like `YYYY-MM-DD-slug.md`, for example:

```
posts/2026-07-15-real-esrgan-notes.md
```

Start it with front matter, then write normally in markdown below it:

```markdown
---
title: Getting Real-ESRGAN to actually converge
date: 2026-07-15
tags: cs, space-tech
excerpt: The one bug that cost me three days and a lot of coffee.
---

Your post content goes here. **Bold**, *italic*, `inline code`,
[links](https://example.com), and:

- bullet
- points

work fine. Also headers with `##` and `###`, code blocks with triple
backticks, and > blockquotes.
```

Tags are freeform — use whatever labels you want (`space-tech`, `gym`, `squash`, `math`,
`cs`, `personal`...). They automatically become filter buttons on the homepage.

## Building and previewing locally

From the `blog/` folder:

```bash
python3 build.py
```

This regenerates everything inside `docs/`. To preview it in a browser before pushing:

```bash
cd docs
python3 -m http.server 8000
```

Then open `http://localhost:8000` in your browser. Stop the server with `Ctrl+C` when done.

## Publishing (first time setup)

1. Create a new **repository** on GitHub (e.g. `blog` or `orbit`). Keep it public if you want
   people to read it, private if you don't (private repos can't use free GitHub Pages though).
2. In this `blog/` folder, run:
   ```bash
   git init
   git add .
   git commit -m "initial site"
   git branch -M main
   git remote add origin https://github.com/<your-username>/<repo-name>.git
   git push -u origin main
   ```
3. On GitHub: go to your repo → **Settings** → **Pages** → under "Build and deployment",
   set **Source** to "Deploy from a branch", branch `main`, folder `/docs`. Save.
4. GitHub gives you a URL like `https://dhwanibro.github.io/dhwani-orbit/` — that's your
   live blog, usually live within a minute or two.

## Publishing a new post after that (every time)

```bash
python3 build.py
git add .
git commit -m "post: real-esrgan notes"
git push
```

That's the entire "upload" flow. A minute later the new post is live.

## Customizing

- **Colors**: edit the `:root` variables at the top of `static/style.css` (`--pink`, `--yellow`, `--bg`).
- **Fonts**: swap the Google Fonts link in `templates/index.html` and `templates/post.html`.
- **Homepage intro text**: edit the `.intro` section in `templates/index.html`.
- **Site title**: search-and-replace `dhwani's orbit` across the templates.

Never edit files inside `docs/` directly — `build.py` overwrites them every time you run it.
