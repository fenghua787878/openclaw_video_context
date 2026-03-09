#!/usr/bin/env bash
# 检查 HTTP_PROXY/HTTPS_PROXY 是否可用（如 curl 测试）。
# 不可用时输出错误码并退出；脚本需稳健（set -e 可选，便于调用方处理）。

set -euo pipefail

TEST_URL="${TEST_URL:-https://www.example.com}"
TIMEOUT="${TIMEOUT:-10}"
EXIT_OK=0
EXIT_PROXY_FAIL=1

check_proxy() {
  if curl -sf --connect-timeout "$TIMEOUT" --max-time "$TIMEOUT" "$TEST_URL" >/dev/null 2>&1; then
    echo "OK: proxy or direct reachable ($TEST_URL)"
    return $EXIT_OK
  fi
  echo "ERROR: unreachable $TEST_URL (check HTTP_PROXY/HTTPS_PROXY or network)" >&2
  return $EXIT_PROXY_FAIL
}

# 若明确要求只检查代理变量存在性而不测连通性，可用 SKIP_CURL=1
if [[ "${SKIP_CURL:-0}" == "1" ]]; then
  if [[ -n "${HTTP_PROXY:-}" ]] || [[ -n "${HTTPS_PROXY:-}" ]]; then
    echo "OK: proxy env set (HTTP_PROXY/HTTPS_PROXY)"
    exit $EXIT_OK
  else
    echo "WARN: no proxy env set" >&2
    exit $EXIT_OK
  fi
fi

check_proxy
exit $?
