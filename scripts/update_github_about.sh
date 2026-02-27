#!/usr/bin/env bash
set -euo pipefail

: "${GITHUB_TOKEN:?GITHUB_TOKEN is required}"

OWNER="${1:-huangzhimin4read}"
REPO="${2:-openclaw-multiuser-session-guard-skill}"

DESC="${DESC:-OpenClaw skill for stable multi-user session routing. Enforces valid session.dmScope and startup guard to prevent context cross-talk and restart loops.}"
HOMEPAGE="${HOMEPAGE:-https://github.com/${OWNER}/${REPO}}"
TOPICS_JSON="${TOPICS_JSON:-[\"openclaw\",\"skill\",\"multi-user\",\"session-routing\",\"dmscope\",\"feishu\",\"systemd\"]}"

api() {
  curl -sSf \
    -H "Authorization: Bearer ${GITHUB_TOKEN}" \
    -H "Accept: application/vnd.github+json" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    "$@"
}

api -X PATCH "https://api.github.com/repos/${OWNER}/${REPO}" \
  -d "{\"description\":\"${DESC}\",\"homepage\":\"${HOMEPAGE}\"}" >/tmp/github_about_repo.json

api -X PUT "https://api.github.com/repos/${OWNER}/${REPO}/topics" \
  -d "{\"names\":${TOPICS_JSON}}" >/tmp/github_about_topics.json

echo "Updated About for ${OWNER}/${REPO}"
echo "Description: ${DESC}"
echo "Homepage: ${HOMEPAGE}"
echo "Topics: ${TOPICS_JSON}"
