#!/usr/bin/env bash
#
# spider_starsfaq.sh — Mirror Stars!-R-Us articles from starsfaq.com
#
# Usage:
#   ./tools/spider_starsfaq.sh
#
# Downloads HTML articles from the Stars!-R-Us economics section, starting at
# art_economics.htm and following all links within /articles/. Output lands in:
#
#   local-data/starsfaq/www.starsfaq.com/articles/sru/
#
# After spidering, run tools/html_to_md_starsfaq.py to convert to markdown.
#
# To fetch a single article that wasn't caught by the spider, use wget directly:
#   wget --directory-prefix=local-data/starsfaq/www.starsfaq.com/articles/sru \
#        http://www.starsfaq.com/articles/sru/artNNN.htm
#
# Options used:
#   --recursive / --level=2   Follow links up to 2 hops deep
#   --no-parent               Don't crawl above the starting URL's directory
#   --include-directories     Restrict to /articles/ paths only
#   --adjust-extension        Add .htm suffix where missing
#   --page-requisites         Also fetch images/CSS needed to render pages
#   --convert-links           Rewrite links for local browsing
#   --wait / --random-wait    Be polite — 1 s base delay with jitter

set -e

OUTDIR="$(dirname "$0")/../local-data/starsfaq"
mkdir -p "$OUTDIR"

wget \
  --recursive \
  --level=2 \
  --no-parent \
  --domains starsfaq.com \
  --include-directories=/articles/ \
  --adjust-extension \
  --page-requisites \
  --convert-links \
  --wait=1 \
  --random-wait \
  --no-verbose \
  --directory-prefix="$OUTDIR" \
  "http://www.starsfaq.com/articles/sru/art_economics.htm"

echo "Done. Files saved to $OUTDIR"
