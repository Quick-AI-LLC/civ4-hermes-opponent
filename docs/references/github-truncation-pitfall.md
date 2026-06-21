# Remote Skill JSON Fetch — Truncation Pitfall

**When**: 2026-05-10, while fetching `civ4-player-skill.json` from GitHub.

## Problem
`curl` and Python `urllib` both returned a truncated version of the file (~3,325 bytes). The `system_prompt` string was cut off mid-sentence and had mixed `\n` escaping, causing `JSONDecodeError: Invalid control character`.

## Root Cause
GitHub's raw content endpoint can return partial content under certain conditions (rate limiting, CDN edge issues, or file size). The tool's output looked complete in preview but was actually cut.

## Fix Applied
User provided the full file content directly. Validated with `json.loads()` before use.

## Pattern for Next Time
When fetching skill JSON from a remote source:
1. Validate with `json.loads()` immediately after fetch
2. Check that string values aren't truncated (look for unclosed strings)
3. Compare byte count against expected size if known
4. If GitHub fails, try `gh api` or clone the repo as fallback