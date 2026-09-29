#!/usr/bin/env python3
"""
Concurrent rip of itemalapitvany.hu from the Wayback Machine snapshot
dated 2026-05-11, rebuilt as a local static site under ../site/ with
all internal links, images, css and js rewritten to relative local paths.
"""
import html.parser
import json
import os
import re
import time
import threading
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlsplit, urlunsplit

TARGET_TS = "20260511120733"
CANON_HOST = "www.itemalapitvany.hu"
ROOT_DIR = os.path.join(os.path.dirname(__file__), "..", "site")
LOG_PATH = os.path.join(os.path.dirname(__file__), "rip_log.json")
WORKERS = 10

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; site-recovery-script/1.0)"}

SKIP_PATTERNS = [
    "/wp-admin", "/wp-login", "/xmlrpc.php", "/wp-json", "/feed",
    "/comments/feed", "/author/", "/wp-sitemap", "/.well-known",
    "/hello-world", "/category/", "ver=3.7.1",
]

EXTRA_PAGES = [
    "https://www.itemalapitvany.hu/a-hatarsertes-technologiai/",
    "https://www.itemalapitvany.hu/elementor-136/",
    "https://www.itemalapitvany.hu/hibrid-gondolkodas/",
    "https://www.itemalapitvany.hu/kijarat/",
    "https://www.itemalapitvany.hu/transzmedia/",
    "https://www.itemalapitvany.hu/draft/",
    "https://www.itemalapitvany.hu/draft/galeria/",
    "https://www.itemalapitvany.hu/draft/hibiki/",
    "https://www.itemalapitvany.hu/draft/kapcsolat/",
    "https://www.itemalapitvany.hu/draft/kelemen-patrik/",
    "https://www.itemalapitvany.hu/draft/kijarat/",
    "https://www.itemalapitvany.hu/draft/paikka/",
    "https://www.itemalapitvany.hu/draft/rolunk/",
]

lock = threading.Lock()
visited_pages = set()
assets = set()
processed_assets = set()
log = {"pages": {}, "assets": {}, "failed": []}


def should_skip(path):
    return any(p in path for p in SKIP_PATTERNS)


def normalize_url(url, base=None):
    if base:
        url = urljoin(base, url)
    parts = urlsplit(url)
    if "itemalapitvany.hu" not in parts.netloc:
        return None
    if "webmail." in parts.netloc or "webdisk." in parts.netloc:
        return None
    path = parts.path or "/"
    # extensionless paths are WP permalink-style routes; normalize to a directory
    last_seg = path.rsplit("/", 1)[-1]
    if path != "/" and not path.endswith("/") and "." not in last_seg:
        path = path + "/"
    return urlunsplit(("https", CANON_HOST, path, "", ""))


def local_path_for(url):
    parts = urlsplit(url)
    path = parts.path
    if path in ("", "/"):
        return "index.html"
    if path.endswith("/"):
        return path.strip("/") + "/index.html"
    return path.lstrip("/")


def fetch(url, retries=2, timeout=20):
    wb_url = f"https://web.archive.org/web/{TARGET_TS}id_/{url}"
    for attempt in range(retries):
        try:
            req = urllib.request.Request(wb_url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read(), resp.headers.get("Content-Type", "")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None, None
            time.sleep(1.5 * (attempt + 1))
        except Exception:
            time.sleep(1.5 * (attempt + 1))
    return None, None


class LinkExtractor(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and attrs.get("href"):
            self.links.append(("a", "href", attrs["href"]))
        elif tag == "img":
            if attrs.get("src"):
                self.links.append(("img", "src", attrs["src"]))
            if attrs.get("srcset"):
                self.links.append(("img", "srcset", attrs["srcset"]))
        elif tag == "link" and attrs.get("href"):
            rel = attrs.get("rel", "")
            if "stylesheet" in rel or "icon" in rel or attrs.get("as") == "style":
                self.links.append(("link", "href", attrs["href"]))
        elif tag == "script" and attrs.get("src"):
            self.links.append(("script", "src", attrs["src"]))
        elif tag == "source":
            if attrs.get("src"):
                self.links.append(("source", "src", attrs["src"]))
            if attrs.get("srcset"):
                self.links.append(("source", "srcset", attrs["srcset"]))


def extract_css_urls(css_text):
    return re.findall(r'url\((?!["\']?data:)["\']?([^)"\']+)["\']?\)', css_text)


def is_page_url(url):
    path = urlsplit(url).path
    if should_skip(path):
        return False
    return path == "/" or path.endswith("/")


def relpath(from_file, to_file):
    from_dir = os.path.dirname(from_file)
    return os.path.relpath(to_file, start=from_dir or ".")


def save(local_path, data):
    full = os.path.join(ROOT_DIR, local_path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "wb") as f:
        f.write(data)


def process_page(url):
    data, content_type = fetch(url)
    if data is None:
        with lock:
            log["failed"].append(url)
        print(f"  FAIL page {url}")
        return []
    text = data.decode("utf-8", errors="replace")
    parser = LinkExtractor()
    parser.feed(text)
    my_local = local_path_for(url)
    replacements = []
    discovered_pages = []

    for tag, attr, value in parser.links:
        if value.startswith(("mailto:", "tel:", "javascript:", "#")):
            continue
        if attr == "srcset":
            parts = value.split(",")
            new_parts = []
            changed = False
            for p in parts:
                p = p.strip()
                bits = p.split(" ")
                norm = normalize_url(bits[0], url)
                if norm:
                    local = local_path_for(norm)
                    bits[0] = relpath(my_local, local)
                    changed = True
                    with lock:
                        assets.add(norm)
                new_parts.append(" ".join(bits))
            if changed:
                replacements.append((value, ", ".join(new_parts)))
            continue

        norm = normalize_url(value, url)
        if not norm or should_skip(urlsplit(norm).path):
            continue
        if tag == "a" and is_page_url(norm):
            discovered_pages.append(norm)
            local = local_path_for(norm)
            replacements.append((value, relpath(my_local, local)))
        else:
            with lock:
                assets.add(norm)
            local = local_path_for(norm)
            replacements.append((value, relpath(my_local, local)))

    for old, new in sorted(set(replacements), key=lambda x: -len(x[0])):
        if old == new:
            continue
        text = text.replace(f'"{old}"', f'"{new}"')
        text = text.replace(f"'{old}'", f"'{new}'")

    save(my_local, text.encode("utf-8"))
    with lock:
        log["pages"][url] = my_local
    print(f"  OK page {url} -> {my_local}")
    return discovered_pages


def process_css(url):
    data, content_type = fetch(url)
    if data is None:
        with lock:
            log["failed"].append(url)
        return
    text = data.decode("utf-8", errors="replace")
    my_local = local_path_for(url)
    for raw in extract_css_urls(text):
        raw_clean = raw.strip()
        if raw_clean.startswith("data:"):
            continue
        norm = normalize_url(raw_clean, url)
        if not norm:
            continue
        with lock:
            assets.add(norm)
        local = local_path_for(norm)
        text = text.replace(raw, relpath(my_local, local))
    save(my_local, text.encode("utf-8"))
    with lock:
        log["assets"][url] = my_local


def process_binary_asset(url):
    data, content_type = fetch(url)
    if data is None:
        with lock:
            log["failed"].append(url)
        return
    local = local_path_for(url)
    save(local, data)
    with lock:
        log["assets"][url] = local


def main():
    start = f"https://{CANON_HOST}/"
    frontier = [start] + EXTRA_PAGES

    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        round_num = 0
        while frontier:
            round_num += 1
            todo = []
            for u in frontier:
                with lock:
                    if u in visited_pages:
                        continue
                    visited_pages.add(u)
                todo.append(u)
            if not todo:
                break
            print(f"[page round {round_num}] fetching {len(todo)} pages")
            futures = {ex.submit(process_page, u): u for u in todo}
            next_frontier = []
            for fut in as_completed(futures):
                new_pages = fut.result()
                next_frontier.extend(new_pages)
            frontier = next_frontier

        round_num = 0
        while True:
            round_num += 1
            with lock:
                pending = [a for a in assets if a not in processed_assets]
                for a in pending:
                    processed_assets.add(a)
            if not pending:
                break
            print(f"[asset round {round_num}] fetching {len(pending)} assets")
            futures = []
            for a in pending:
                path = urlsplit(a).path.lower()
                if path.endswith(".css"):
                    futures.append(ex.submit(process_css, a))
                else:
                    futures.append(ex.submit(process_binary_asset, a))
            for fut in as_completed(futures):
                fut.result()

    with open(LOG_PATH, "w") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)

    print(f"\nDone. Pages: {len(log['pages'])}  Assets: {len(log['assets'])}  Failed: {len(log['failed'])}")
    for u in log["failed"]:
        print(" FAILED:", u)


if __name__ == "__main__":
    main()
