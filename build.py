#!/usr/bin/env python3
"""
build.py — turns markdown posts into the static site in docs/

How this fits together:
  posts/*.md        <- you write these. this is the ONLY thing you edit
                        to publish a new post.
  templates/*.html  <- page skeletons, rarely touched
  static/style.css  <- theme, rarely touched
  docs/             <- fully generated. never hand-edit. GitHub Pages
                        serves this folder.

Run:
  python3 build.py

Then commit + push. Because this repo lives on GitHub, only people with
push access (i.e. you, unless you add collaborators) can ever change
what's on the site. There is no login form, no upload button, no server —
the "upload" step IS the git push, and git push is already gated by your
GitHub account. That's what makes you the only author.
"""

import os
import re
import shutil
from datetime import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
POSTS_DIR = os.path.join(ROOT, "posts")
TEMPLATES_DIR = os.path.join(ROOT, "templates")
STATIC_DIR = os.path.join(ROOT, "static")
DOCS_DIR = os.path.join(ROOT, "docs")
DOCS_POSTS_DIR = os.path.join(DOCS_DIR, "posts")


# ---------- tiny markdown -> html converter ----------
# Supports: # ## ### headers, **bold**, *italic*, `code`, ```code blocks```,
# [link](url), ![alt](src), > blockquote, - / 1. lists, --- hr, paragraphs.
# Good enough for a personal blog without pulling in a dependency.

def inline(text):
    text = html_escape_keep_tags(text)
    text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img alt="\1" src="\2">', text)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', text)
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    return text


def html_escape_keep_tags(text):
    # escape raw < > & so stray symbols don't break the page,
    # markdown syntax above re-introduces the tags it needs.
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def markdown_to_html(md):
    lines = md.replace('\r\n', '\n').split('\n')
    html = []
    i = 0
    in_ul = False
    in_ol = False

    def close_lists():
        nonlocal in_ul, in_ol
        if in_ul:
            html.append('</ul>')
            in_ul = False
        if in_ol:
            html.append('</ol>')
            in_ol = False

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # fenced code block
        if stripped.startswith('```'):
            close_lists()
            lang = stripped[3:].strip()
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code_lines.append(lines[i])
                i += 1
            code = html_escape_keep_tags('\n'.join(code_lines))
            cls = f' class="language-{lang}"' if lang else ''
            html.append(f'<pre><code{cls}>{code}</code></pre>')
            i += 1
            continue

        # headers
        m = re.match(r'^(#{1,3})\s+(.*)', stripped)
        if m:
            close_lists()
            level = len(m.group(1)) + 1  # h1 reserved for post title, so ## -> h3 etc feels off; map # -> h2
            level = min(level, 4)
            html.append(f'<h{level}>{inline(m.group(2))}</h{level}>')
            i += 1
            continue

        # horizontal rule
        if re.match(r'^-{3,}$', stripped):
            close_lists()
            html.append('<hr>')
            i += 1
            continue

        # blockquote
        if stripped.startswith('>'):
            close_lists()
            quote_lines = []
            while i < len(lines) and lines[i].strip().startswith('>'):
                quote_lines.append(lines[i].strip()[1:].strip())
                i += 1
            html.append(f'<blockquote><p>{inline(" ".join(quote_lines))}</p></blockquote>')
            continue

        # unordered list
        if re.match(r'^[-*]\s+', stripped):
            if not in_ul:
                close_lists()
                html.append('<ul>')
                in_ul = True
            item = re.sub(r'^[-*]\s+', '', stripped)
            html.append(f'<li>{inline(item)}</li>')
            i += 1
            continue

        # ordered list
        if re.match(r'^\d+\.\s+', stripped):
            if not in_ol:
                close_lists()
                html.append('<ol>')
                in_ol = True
            item = re.sub(r'^\d+\.\s+', '', stripped)
            html.append(f'<li>{inline(item)}</li>')
            i += 1
            continue

        # blank line
        if stripped == '':
            close_lists()
            i += 1
            continue

        # paragraph (collect until blank line)
        close_lists()
        para_lines = [stripped]
        i += 1
        while i < len(lines) and lines[i].strip() != '' and not re.match(r'^(#{1,3})\s+', lines[i].strip()) \
                and not lines[i].strip().startswith('```'):
            para_lines.append(lines[i].strip())
            i += 1
        html.append(f'<p>{inline(" ".join(para_lines))}</p>')

    close_lists()
    return '\n'.join(html)


# ---------- front matter parsing ----------

def parse_front_matter(text):
    """
    Expects:
    ---
    title: My Post
    date: 2026-07-01
    tags: space-tech, cs
    excerpt: one line summary
    ---
    body...
    """
    m = re.match(r'^---\n(.*?)\n---\n(.*)$', text, re.DOTALL)
    if not m:
        raise ValueError("Post is missing --- front matter at the top of the file.")
    raw_meta, body = m.group(1), m.group(2)
    meta = {}
    for line in raw_meta.split('\n'):
        if ':' not in line:
            continue
        key, val = line.split(':', 1)
        meta[key.strip().lower()] = val.strip()
    meta['tags'] = [t.strip() for t in meta.get('tags', '').split(',') if t.strip()]
    return meta, body


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'\s+', '-', text)
    return text.strip('-')


def load_template(name):
    with open(os.path.join(TEMPLATES_DIR, name), encoding='utf-8') as f:
        return f.read()


def format_date(raw_date):
    try:
        d = datetime.strptime(raw_date, '%Y-%m-%d')
        return d.strftime('%B %-d, %Y') if os.name != 'nt' else d.strftime('%B %d, %Y')
    except ValueError:
        return raw_date


def main():
    os.makedirs(DOCS_POSTS_DIR, exist_ok=True)

    post_template = load_template('post.html')
    index_template = load_template('index.html')

    posts = []

    for filename in sorted(os.listdir(POSTS_DIR)):
        if not filename.endswith('.md'):
            continue
        path = os.path.join(POSTS_DIR, filename)
        with open(path, encoding='utf-8') as f:
            raw = f.read()

        meta, body = parse_front_matter(raw)
        title = meta.get('title', 'Untitled')
        date_raw = meta.get('date', '1970-01-01')
        tags = meta.get('tags', [])
        excerpt = meta.get('excerpt', '')
        slug = meta.get('slug') or slugify(f"{date_raw}-{title}")

        content_html = markdown_to_html(body)

        posts.append({
            'title': title,
            'date_raw': date_raw,
            'date': format_date(date_raw),
            'tags': tags,
            'excerpt': excerpt,
            'slug': slug,
            'content': content_html,
        })

    # newest first
    posts.sort(key=lambda p: p['date_raw'], reverse=True)

    # build sidebar: tag labels + one link per post (used on every page)
    all_tags = sorted({t for p in posts for t in p['tags']})
    tag_buttons = '\n'.join(f'<span class="tag">{t}</span>' for t in all_tags)
    sidebar_links = '\n'.join(
        f'<a href="posts/{p["slug"]}.html">{p["date"]} — {p["title"]}</a>' for p in posts
    )

    # write individual post pages (sidebar links point back to posts/ so they
    # need a leading "../" prefix relative to a page already inside docs/posts/)
    sidebar_links_from_post = '\n'.join(
        f'<a href="{p["slug"]}.html">{p["date"]} — {p["title"]}</a>' for p in posts
    )
    for post in posts:
        page = post_template
        page = page.replace('{{TITLE}}', post['title'])
        page = page.replace('{{DATE}}', post['date'])
        page = page.replace('{{TAG_BUTTONS}}', tag_buttons)
        page = page.replace('{{POST_CARDS}}', sidebar_links_from_post)
        page = page.replace('{{CONTENT}}', post['content'])
        out_path = os.path.join(DOCS_POSTS_DIR, f"{post['slug']}.html")
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(page)
        print(f"  wrote docs/posts/{post['slug']}.html")

    # write homepage
    index_page = index_template
    index_page = index_page.replace('{{TAG_BUTTONS}}', tag_buttons)
    index_page = index_page.replace('{{POST_CARDS}}', sidebar_links)

    with open(os.path.join(DOCS_DIR, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(index_page)
    print("  wrote docs/index.html")

    # copy stylesheet
    shutil.copyfile(os.path.join(STATIC_DIR, 'style.css'), os.path.join(DOCS_DIR, 'style.css'))
    print("  copied style.css")

    # tell GitHub Pages to serve this as-is, not run it through Jekyll
    open(os.path.join(DOCS_DIR, '.nojekyll'), 'a').close()
    print("  ensured .nojekyll")

    print(f"\nDone. {len(posts)} post(s) built into docs/")


if __name__ == '__main__':
    main()
