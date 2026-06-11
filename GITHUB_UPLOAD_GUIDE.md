# GitHub Upload Guide

## 1. Create a GitHub Repository

Recommended repository name:

```text
design-knowledge-engine
```

Recommended description:

```text
Turn visual inspiration into structured knowledge through AI-powered image analysis and Markdown-based knowledge management.
```

Create an empty repository on GitHub. Do not initialize it with a README, license, or `.gitignore` because those files already exist locally.

## 2. Initialize Git

```bash
cd /path/to/Design-Knowledge-Engine
git init
```

## 3. First Commit

```bash
git add .
git commit -m "Initial open source preview"
```

## 4. Add Remote Repository

Replace `<your-account>` with your GitHub username or organization:

```bash
git remote add origin https://github.com/<your-account>/design-knowledge-engine.git
```

## 5. Push

```bash
git branch -M main
git push -u origin main
```

## 6. Create Release

1. Open the GitHub repository page.
2. Go to `Releases`.
3. Click `Draft a new release`.
4. Tag version:

```text
v0.1.0
```

5. Release title:

```text
Design Knowledge Engine v0.1.0
```

6. Paste the contents of `RELEASE_NOTES_v0.1.0.md`.
7. Publish the release.
