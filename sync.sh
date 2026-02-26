#!/usr/bin/env bash
set -euo pipefail

SOURCE_REPO="$HOME/Documents/2-coding-space/git/github.com/xquant-tutorial"
TARGET_REPO="$HOME/Documents/2-coding-space/git/github.com/xquant-learning"

# Validate source repo exists
if [[ ! -d "$SOURCE_REPO/.git" ]]; then
    echo "Error: source repo not found at $SOURCE_REPO"
    exit 1
fi

cd "$TARGET_REPO"

# Sync specs and notebooks for each chapter
for chapter_dir in "$SOURCE_REPO"/q*-*/; do
    chapter=$(basename "$chapter_dir")

    for subdir in specs notebooks; do
        src="$chapter_dir$subdir"
        dst="$TARGET_REPO/$chapter/$subdir"

        # Skip if source directory doesn't exist or is empty
        if [[ ! -d "$src" ]] || [[ -z "$(ls -A "$src" 2>/dev/null)" ]]; then
            continue
        fi

        mkdir -p "$dst"

        # Use rsync to mirror content (delete files removed from source)
        rsync -a --delete "$src/" "$dst/"
    done
done

# Check for changes
if git diff --quiet HEAD -- 2>/dev/null && [[ -z "$(git ls-files --others --exclude-standard)" ]]; then
    echo "No changes to sync."
    exit 0
fi

# Stage, commit, push
git add -A
git commit -m "sync specs and notebooks from xquant-tutorial"
git push

echo "Synced and pushed successfully."
