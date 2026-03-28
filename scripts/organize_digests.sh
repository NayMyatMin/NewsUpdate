#!/usr/bin/env bash
# Moves completed weeks' digests into weekly subfolders.
# A week runs Monday–Sunday. Only past (completed) weeks are moved;
# the current week's files stay flat in digests/.
#
# Folder format: digests/YYYY-MM-DD_to_YYYY-MM-DD/
# e.g. digests/2026-03-23_to_2026-03-29/

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DIGEST_DIR="$(cd "$SCRIPT_DIR/../digests" && pwd)"

# Get today's date and the Monday of the current week (in UTC)
today=$(date -u +%Y-%m-%d)
# day_of_week: 1=Monday ... 7=Sunday
day_of_week=$(date -u -d "$today" +%u)
current_week_monday=$(date -u -d "$today -$((day_of_week - 1)) days" +%Y-%m-%d)

# Track which week folders received new files
declare -A new_week_dirs

# Find all markdown digest files in the flat digests/ directory
for file in "$DIGEST_DIR"/????-??-??.md; do
    [ -f "$file" ] || continue

    filename=$(basename "$file" .md)

    # Compute the Monday of this file's week
    file_dow=$(date -u -d "$filename" +%u 2>/dev/null) || continue
    file_monday=$(date -u -d "$filename -$((file_dow - 1)) days" +%Y-%m-%d)

    # Skip if this file belongs to the current (incomplete) week
    if [ "$file_monday" = "$current_week_monday" ]; then
        continue
    fi

    # Compute Sunday of that week
    file_sunday=$(date -u -d "$file_monday +6 days" +%Y-%m-%d)

    # Create weekly subfolder and move the file
    week_dir="$DIGEST_DIR/${file_monday}_to_${file_sunday}"
    mkdir -p "$week_dir"
    mv "$file" "$week_dir/"
    echo "Moved $filename.md -> ${file_monday}_to_${file_sunday}/"

    new_week_dirs["$week_dir"]=1
done

# Generate weekly summary for each newly archived week
for week_dir in "${!new_week_dirs[@]}"; do
    if [ ! -f "$week_dir/weekly-summary.md" ]; then
        echo "Generating weekly summary for $(basename "$week_dir")..."
        python3 "$SCRIPT_DIR/generate_weekly_summary.py" "$week_dir"
    fi
done
