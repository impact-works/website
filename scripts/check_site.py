"""Smoke-test the built site: python3 scripts/check_site.py [output-dir]."""

from html.parser import HTMLParser
from pathlib import Path
import sys
from urllib.parse import unquote, urlsplit


BRAND = "impact works"
VISION = "The world's best technology in the hands of people doing good in the world."
MISSION = (
    "We’re rooted in our community. We work with small organizations doing good, "
    "building and sharing excellent technology that helps them do more."
)
VALUES = {
    "Justice": (
        "Impact Works is as much a political act as it is a business. "
        "We put powerful technology in the hands of people and communities the "
        "market leaves behind. We refuse work that makes inequality worse."
    ),
    "Quality": (
        "Good work comes from paying attention: understanding what you’re working "
        "with, who you’re doing it for, and why. We aim for work that’s a pleasure "
        "to use and affordable to run and maintain."
    ),
    "Community": (
        "We’re part of the community we serve, and our customers are our partners. "
        "We put the people doing the work first and share what we build so others "
        "can use it and keep it going."
    ),
}


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.tags = []
        self.body_text = []
        self.in_body = False
        self.heading_level = None
        self.headings = []
        self.feed(path.read_text())

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags.append((tag, attrs))
        if tag == "body":
            self.in_body = True
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.heading_level = tag
            self.headings.append([tag, []])

    def handle_endtag(self, tag):
        if tag == "body":
            self.in_body = False
        if tag == self.heading_level:
            self.heading_level = None

    def handle_data(self, data):
        if self.in_body:
            self.body_text.append(data)
        if self.heading_level:
            self.headings[-1][1].append(data)

    def elements(self, tag):
        return [attrs for name, attrs in self.tags if name == tag]


def normalize(parts):
    return " ".join(" ".join(parts).split())


def canonical(page):
    return next(
        attrs["href"] for attrs in page.elements("link")
        if attrs.get("rel") == "canonical"
    )


root = Path(sys.argv[1] if len(sys.argv) > 1 else "public").resolve()
index = root / "index.html"
about_index = root / "about/index.html"
assert index.is_file(), "Missing built homepage"
assert about_index.is_file(), "Missing About page"
assert set(root.rglob("*.html")) == {index, about_index}, "Unexpected HTML pages"

home = Page(index)
about = Page(about_index)
base_path = urlsplit(canonical(home)).path.rstrip("/")


def local_target(href):
    url = urlsplit(href)
    assert not url.scheme and not url.netloc, f"Expected local URL: {href}"
    output_path = unquote(url.path)
    if base_path:
        assert output_path.startswith(f"{base_path}/"), f"Missing base path: {href}"
        output_path = output_path[len(base_path):]
    target = root / output_path.lstrip("/")
    if target.is_dir():
        target /= "index.html"
    return target


assert home.headings == [["h1", [BRAND]]], f"Unexpected homepage headings: {home.headings}"
assert normalize(home.body_text) == f"{BRAND} About {VISION} {MISSION}", "Unexpected homepage copy"
assert any(local_target(a["href"]) == about_index for a in home.elements("a")), "Missing About link"
assert canonical(about) == canonical(home).rstrip("/") + "/about/", "Wrong About canonical"

about_headings = [(level, normalize(text)) for level, text in about.headings]
assert about_headings == [
    ("h1", "About Impact Works"),
    ("h2", "Matt Wynne"),
    ("h2", "Our values"),
    *[("h3", name) for name in VALUES],
], f"Unexpected About headings: {about_headings}"
assert [heading.get("id") for heading in about.elements("h2")] == ["matt", "values"], "Missing section anchors"
about_text = normalize(about.body_text)
bio = about_text.split("Matt Wynne", 1)[1].split("Our values", 1)[0]
assert len(bio.split()) >= 100, "Missing or incomplete biography"
assert "Nelson, British Columbia" in bio, "Missing bio location"
assert "co-founded Cucumber Ltd in 2013" in bio, "Missing historical Cucumber role"
assert "serving as CEO until 2018" in bio, "Missing historical CEO role"
assert "Founder" in bio, "Missing Founder title"
assert not home.elements("img"), "Homepage should not contain images"
portraits = about.elements("img")
assert len(portraits) == 1, "Expected one founder portrait"
portrait = portraits[0]
assert portrait.get("alt") == "Matt Wynne, founder of Impact Works", "Missing portrait description"
assert portrait.get("width") == portrait.get("height") == "640", "Expected explicit square portrait dimensions"
assert local_target(portrait["src"]).is_file(), "Missing local portrait"
assert portrait.get("sizes"), "Missing responsive image sizes"
assert {item.strip().rsplit(" ", 1)[1] for item in portrait.get("srcset", "").split(",")} == {"320w", "640w"}
for source in portrait["srcset"].split(","):
    assert local_target(source.strip().rsplit(" ", 1)[0]).is_file(), "Missing responsive portrait"
for name, statement in VALUES.items():
    assert statement in about_text, f"Missing or changed value: {name}"
assert any(a.get("href") == f"{base_path}/" for a in about.elements("a")), "Missing home link"
current = [a for a in about.elements("a") if a.get("aria-current") == "page"]
assert len(current) == 1 and local_target(current[0]["href"]) == about_index, "Wrong current-page link"

for page in [home, about]:
    assert len(page.elements("main")) == 1, "Expected one main landmark"
    assert len(page.elements("h1")) == 1, "Expected one H1"
    assert len(page.elements("nav")) == 1, "Expected main navigation"
    assert page.elements("nav")[0].get("aria-label") == "Main"
    assert not any(page.elements(tag) for tag in ["script", "form", "footer"])
    assert len(page.elements("link")) == 2, "Expected canonical and local stylesheet links"
    metadata = {m.get("name", m.get("property")): m.get("content") for m in page.elements("meta")}
    assert metadata.get("description"), "Missing page description"
    assert metadata.get("og:description") == metadata["description"]
    assert metadata.get("og:url") == canonical(page)
    assert metadata.get("og:title") == ("Impact Works" if page is home else "About Impact Works | Impact Works")
    for attrs in page.elements("link"):
        if attrs.get("rel") == "stylesheet":
            assert local_target(attrs["href"]).is_file(), f"Missing stylesheet: {attrs['href']}"
    for attrs in page.elements("a"):
        href = attrs.get("href", "")
        if not urlsplit(href).scheme:
            assert local_target(href).is_file(), f"Broken internal link: {href}"

print("Passed: homepage, About page, values, navigation, metadata, and local assets.")
