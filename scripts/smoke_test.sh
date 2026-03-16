#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

run_case() {
  local mode="$1"
  local question="$2"
  local context="$3"
  echo "===== $mode ====="
  "$PYTHON_BIN" "$ROOT/scripts/render_reading.py" \
    --mode "$mode" \
    --question "$question" \
    --context "$context" \
    --date "2026-03-16" \
    --style standard
  echo
}

run_case "career" "我要不要辞职做自己的项目" "现在工作稳定但很消耗，手里有一个想做半年的产品方向，还没验证过付费。"
run_case "relationship" "我该不该主动联系他" "之前聊得不错，但最近冷下来了。我怕不联系就断掉，联系又怕显得太主动。"
run_case "fortune" "为什么我最近做什么都不顺" "事情很多，睡眠一般，开了很多线但都推进不快。"
run_case "personality" "我是不是那种容易自我消耗的人" "常常一开始很猛，后面就乱，想很多，也容易同时开很多线。"

echo "Smoke test passed."
