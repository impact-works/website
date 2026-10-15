# Impact Works website

A deliberately minimal Hugo website for [impactworks.dev](https://impactworks.dev/). The homepage presents the Impact Works name, vision, and mission. `/about/` introduces founder Matt Wynne and Impact Works’ values.

Page copy lives in `content/_index.md` and `content/about.md`. Background sources and editorial cautions are recorded in `docs/content-sources.md` (not published by Hugo).

## Local development

The project uses the same Hugo and GitHub Pages pattern as the NCLT websites. Enter the devenv shell, then preview or build:

```sh
devenv shell
dev
build
check
```

`check` builds the site and verifies the homepage copy, About page headings and exact values, navigation between both pages, page metadata, and local stylesheets. Each page must have one H1 and one main landmark, with no scripts or remote assets.

To check a GitHub Pages project-path build as well:

```sh
hugo --minify --baseURL https://example.org/website/ --destination /tmp/impactworks-project-check
python3 scripts/check_site.py /tmp/impactworks-project-check
```

## Deployment

Pushes to `main` run `.github/workflows/gh-pages.yaml`, build with Hugo Extended 0.152.2, check the output, and deploy it with GitHub Pages Actions.

The custom domain is `impactworks.dev`.
