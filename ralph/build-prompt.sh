#!/bin/bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
project_dir="$(cd "$script_dir/.." && pwd)"
output_file="${1:-$script_dir/generated-prompt.md}"

cd "$project_dir"

commits=$(git log -n 5 --format="%H%n%ad%n%B---" --date=short 2>/dev/null || echo "No commits found")
issues=$(cat issues/*.md 2>/dev/null || echo "No issues found")
prompt=$(cat "$script_dir/prompt.md")

{
  printf 'Previous commits:\n%s\n\n' "$commits"
  printf 'Issues:\n%s\n\n' "$issues"
  printf '%s\n' "$prompt"
} > "$output_file"

echo "Prompt written to $output_file"
