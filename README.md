# gatewardops.com

Source for [gatewardops.com](https://gatewardops.com): practical IT tools that run in the browser, plus guides, downloads and a daily IT news digest.

## What's here

| Path | Purpose |
| --- | --- |
| `index.html` | Home page. All HTML, CSS and JavaScript in one file. Colours are CSS variables at the top. |
| `guides/` | Step-by-step guides as standalone HTML pages. |
| `data/news.json` | Daily headlines, written automatically. Don't edit it by hand. |
| `scripts/fetch_news.py` | Collects headlines from public RSS/Atom feeds. Python standard library only. |
| `.github/workflows/news.yml` | Runs the script every day at 05:15 UTC and commits the result. |
| `CNAME` | Custom domain for GitHub Pages. |
| `.nojekyll` | Serves the files as they are, without a Jekyll build. |

## Tools

- **CIDR / subnet calculator**: network, broadcast, host range, masks and address type for IPv4.
- **Hash generator**: SHA-1/256/384/512 for text or files, via the Web Crypto API.
- **JWT decoder**: header, payload and time claims. Decodes only; it does not verify signatures.

Everything runs client-side. No cookies, no analytics, and no data is sent to a server.

## Daily news

The workflow can also be started by hand: **Actions → Daily news → Run workflow**. To change the sources, edit `FEEDS` in `scripts/fetch_news.py`.

```bash
python scripts/fetch_news.py   # run locally; writes data/news.json
```

## Hosting

GitHub Pages, deploying from `main` / root, with HTTPS enforced. The guide [Custom domain on GitHub Pages](https://gatewardops.com/guides/custom-domain-github-pages.html) explains the setup.
