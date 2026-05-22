# Smart Grid AI Website

This folder is the static download website for Smart Grid AI.

## Deploy

You can deploy the contents of `landing/` to any static host:

- GitHub Pages
- Netlify
- Vercel
- Cloudflare Pages
- S3 or similar object storage

## Deploy On Vercel

Recommended Vercel settings:

```text
Framework Preset: Other
Root Directory: landing
Build Command: leave empty
Output Directory: .
Install Command: leave empty
```

The included `vercel.json` enables clean URLs and cache headers for assets and downloads.

### Best practice for a production landing site

- Keep `landing/index.html` as the site entry point.
- Keep static assets in `landing/assets/`.
- Keep the downloadable installer in `landing/downloads/`.
- Replace `landing/downloads/SmartGridAI-Setup.exe` with the real installer.
- Use a static host that serves `landing/` directly, such as Vercel, Netlify, or GitHub Pages.

### Vercel CLI

From the project root:

```bash
cd landing
vercel
vercel --prod
```

## Installer Download

The current download buttons point to:

```text
downloads/SmartGridAI-Setup.exe
```

After building the Electron desktop installer, either:

1. Place the installer at `landing/downloads/SmartGridAI-Setup.exe`, or
2. Change the links in `index.html` to your GitHub Release or cloud storage URL.

## Local Preview

Open `landing/index.html` directly in a browser to preview the page.
