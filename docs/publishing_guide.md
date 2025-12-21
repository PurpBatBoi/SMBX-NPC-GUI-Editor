# Publishing Guide

Since the executable (`dist/SMBX-NPC-Editor.exe`) is ignored by git, you must manually attach it to a GitHub Release. This is the standard best practice for distributing binaries.

## 1. Push Your Code

First, ensure your code changes are pushed to GitHub. The `.gitignore` will ensure the `dist/` folder and `*.exe` files are NOT uploaded to the repository source code.

```bash
git add .
git commit -m "Prepare for release"
git push
```

## 2. Draft a New Release

1.  Go to your repository on GitHub.
2.  Click on **Releases** (usually on the right sidebar).
3.  Click **Draft a new release**.
4.  **Choose a tag**: Create a new version tag (e.g., `v1.0.0`).
5.  **Release title**: Enter a title (e.g., "Initial Release").
6.  **Description**: Describe the changes/features.

## 3. Upload the Executable

1.  Locate the section **Attach binaries by dropping them here or selecting them**.
2.  Drag and drop the `dist/SMBX-NPC-Editor.exe` file from your computer into this box.
3.  Wait for the upload to complete.

## 4. Publish

Click **Publish release**.

Users can now download the `.exe` directly from the "Assets" section of release `v1.0.0` without needing Python installed.
