from pathlib import Path
from datetime import datetime
from html import escape
import os, re, shutil

import yaml
import mistune
from PIL import Image, ImageOps, ExifTags

ROOT = Path(__file__).parent
OUT = ROOT / "_site"
TOPICS = ROOT / "topics"
TEMPLATES = ROOT / "templates"
STATIC = ROOT / "static"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def load_template(name: str) -> str:
    return (TEMPLATES / name).read_text(encoding="utf-8")


def render(template: str, **values) -> str:
    # Templates use {{key}} rather than str.format so CSS/JS braces are safe.
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", str(value))
    return template


def parse_front_matter(path: Path):
    raw = path.read_text(encoding="utf-8")
    if raw.startswith("---"):
        parts = raw.split("---", 2)
        if len(parts) == 3:
            data = yaml.safe_load(parts[1]) or {}
            return data, parts[2].strip()
    return {}, raw.strip()


def parse_date(value):
    if isinstance(value, datetime):
        return value.date()
    if hasattr(value, "isoformat") and not isinstance(value, str):
        return value
    if isinstance(value, str):
        for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%Y/%m/%d"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                pass
    return None


def topic_sort_key(item):
    data, slug = item
    date = parse_date(data.get("date"))
    return (date is None, date or datetime.min.date(), slug.lower())


def safe_filename(path: Path) -> str:
    return path.name.replace(" ", "-")


def exif_info(path: Path):
    """Return useful EXIF information without failing on malformed metadata."""
    try:
        with Image.open(path) as im:
            exif = im.getexif()
            if not exif:
                return ""
            tags = {ExifTags.TAGS.get(k, k): v for k, v in exif.items()}
            taken = tags.get("DateTimeOriginal") or tags.get("DateTime")
            camera = " ".join(str(x) for x in (tags.get("Make"), tags.get("Model")) if x)
            parts = []
            if taken:
                parts.append(str(taken).replace(":", ".", 2))
            if camera:
                parts.append(camera)
            return " · ".join(parts)
    except Exception:
        return ""


def process_image(src: Path, target: Path):
    with Image.open(src) as original:
        im = ImageOps.exif_transpose(original).convert("RGB")
        max_side = 1800
        im.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
        im.save(target, "JPEG", quality=88, optimize=True, progressive=True)

        thumb = target.with_name(target.stem + "-thumb.jpg")
        thumb_im = im.copy()
        thumb_im.thumbnail((480, 360), Image.Resampling.LANCZOS)
        thumb_im.save(thumb, "JPEG", quality=82, optimize=True, progressive=True)
        return thumb


def normalize_hidden(data):
    hidden = data.get("hidden_images", []) or []
    if isinstance(hidden, str):
        hidden = [hidden]
    return {str(x) for x in hidden}


def normalize_cover(data):
    cover = data.get("cover")
    return str(cover) if cover else None


def build_base_url():
    explicit = os.environ.get("SITE_URL", "").strip().rstrip("/")
    if explicit:
        return explicit
    repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
    server = os.environ.get("GITHUB_SERVER_URL", "https://github.com").rstrip("/")
    if repo and server.endswith("github.com"):
        owner, name = repo.split("/", 1)
        return f"https://{owner}.github.io/{name}"
    return ""


shutil.rmtree(OUT, ignore_errors=True)
(OUT / "topics").mkdir(parents=True)
for p in STATIC.glob("*"):
    if p.is_file():
        shutil.copy2(p, OUT / p.name)

items = []
if not TOPICS.exists():
    TOPICS.mkdir()

for directory in [x for x in TOPICS.iterdir() if x.is_dir()]:
    md_path = directory / "index.md"
    if not md_path.exists():
        continue

    data, body = parse_front_matter(md_path)
    slug = directory.name
    target = OUT / "topics" / slug
    target.mkdir(parents=True, exist_ok=True)
    hidden = normalize_hidden(data)
    explicit_cover = normalize_cover(data)
    images = []

    for src in sorted(directory.iterdir(), key=lambda p: p.name.lower()):
        if src.suffix.lower() not in IMAGE_EXTENSIONS or src.name in hidden:
            continue
        output_name = safe_filename(src.with_suffix(".jpg"))
        dst = target / output_name
        process_image(src, dst)
        thumb_name = dst.stem + "-thumb.jpg"
        images.append({
            "name": src.name,
            "url": output_name,
            "thumb": thumb_name,
            "exif": exif_info(src),
        })

    # Optional cover: otherwise use the first visible image.
    cover_image = None
    if explicit_cover:
        for image in images:
            if image["name"] == explicit_cover:
                cover_image = image
                break
    if cover_image is None and images:
        cover_image = images[0]

    image_html = []
    for index, image in enumerate(images):
        caption = image["exif"] or image["name"]
        image_html.append(
            '<figure class="photo">'
            f'<a href="{escape(image["url"])}" data-index="{index}" data-lightbox>'
            f'<img loading="lazy" src="{escape(image["thumb"])}" alt="{escape(caption)}">'
            '</a>'
            f'<figcaption>{escape(caption)}</figcaption>'
            '</figure>'
        )

    body_html = mistune.html(body) if body else ""

    date = data.get("date", "")
    if hasattr(date, "strftime"):
        date = date.strftime("%d.%m.%Y")

    title = str(data.get("title", slug))
    subject = str(data.get("subject", ""))
    school_class = str(data.get("class", ""))
    description = str(data.get("description", ""))
    meta = " · ".join(x for x in (str(date), subject, school_class) if x)

    topic_html = render(
        load_template("topic.html"),
        title=escape(title),
        meta=escape(meta),
        description=escape(description),
        body=body_html,
        images_html="".join(image_html),
        image_count=len(images),
        slug=escape(slug),
    )
    (target / "index.html").write_text(topic_html, encoding="utf-8")

    data["_slug"] = slug
    data["_cover"] = (
        f"topics/{slug}/{cover_image['thumb']}" if cover_image else ""
    )
    data["_date_sort"] = parse_date(data.get("date"))
    data["_meta"] = meta
    data["_image_count"] = len(images)
    items.append((data, slug))

items.sort(key=topic_sort_key, reverse=True)

cards = []
for data, slug in items:
    cover = data.get("_cover", "")
    cover_html = (
        f'<img loading="lazy" src="{escape(cover)}" alt="">'
        if cover else '<div class="no-cover">Bez fotografií</div>'
    )
    cards.append(
        f'<a class="topic" href="topics/{escape(slug)}/">'
        f'{cover_html}'
        '<div class="topic-info">'
        f'<h2>{escape(str(data.get("title", slug)))}</h2>'
        f'<p class="meta">{escape(str(data.get("_meta", "")))}</p>'
        f'<p>{escape(str(data.get("description", "")))}</p>'
        f'<span class="count">{data.get("_image_count", 0)} fotografií</span>'
        '</div></a>'
    )

title = os.environ.get("GALLERY_TITLE", "Výuka 2026/2027")
index_html = render(
    load_template("index.html"),
    title=escape(title),
    topics_html="".join(cards),
)
(OUT / "index.html").write_text(index_html, encoding="utf-8")

# Sitemap for GitHub Pages / search engines.
base_url = build_base_url()
if base_url:
    urls = [f"{base_url}/"]
    urls.extend(f"{base_url}/topics/{slug}/" for _, slug in items)
    sitemap = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n" \
              "<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">" \
              + "".join(f"<url><loc>{escape(url)}</loc></url>" for url in urls) \
              + "</urlset>\n"
    (OUT / "sitemap.xml").write_text(sitemap, encoding="utf-8")

print(f"Generated {len(items)} topics in {OUT}")
