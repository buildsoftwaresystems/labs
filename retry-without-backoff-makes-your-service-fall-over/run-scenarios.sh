#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT_DIR="${OUT_DIR:-$BASE_DIR/metrics}"
mkdir -p "$OUT_DIR"

BACKOFF_SCENARIOS=(0 10 50 100 250 500 1000 2000)
CONCURRENCY_SCENARIOS=(1 2 4 8)

export READY_AFTER_SECONDS="${READY_AFTER_SECONDS:-3600}"
export SERVER_DELAY_MS="${SERVER_DELAY_MS:-0}"
export FAIL_RATE="${FAIL_RATE:-1.0}"
export REQUESTS_PER_RUN="${REQUESTS_PER_RUN:-5000}"
export CONCURRENCY="${CONCURRENCY:-1}"

cd ${BASE_DIR}

PID1=""
cleanup() {
  if [ -n "${PID1:-}" ] && kill -0 "$PID1" 2>/dev/null; then
    kill "$PID1" 2>/dev/null || true
  fi
  docker compose down -v --remove-orphans >/dev/null 2>&1 || true
}
trap 'echo; echo "Interrupted, cleaning up..."; cleanup; exit 130' INT
trap cleanup EXIT

docker compose down -v --remove-orphans

for backoff in "${BACKOFF_SCENARIOS[@]}"; do
  export BACKOFF_MS="$backoff"
  for concurrency in "${CONCURRENCY_SCENARIOS[@]}"; do
    export CONCURRENCY="$concurrency"
    echo "=== scenario: ${backoff} ms backoff, ${concurrency} concurrency ==="

    docker compose up --build --force-recreate &
    PID1=$!

    stats_file="$OUT_DIR/${backoff}ms-${concurrency}c-docker-stats.tsv"
    echo "Timestamp_Ms  NAME                 CPU %" > "$stats_file"

    start_ms=$(date +%s%3N)
     timeout --foreground 120s docker stats --format "table {{.Name}}\t{{.CPUPerc}}" \
      | while read -r line; do t=${EPOCHREALTIME/[^0-9]/}; echo "${t%???} $line"; done \
      | grep --line-buffered -v $'\x1b' \
      | grep -v "CPU" \
      | awk '{print $1" "$2" "$3}' >> $stats_file || true
    kill $PID1 2>/dev/null || true
    end_ms=$(date +%s%3N)
    elapsed_ms=$((end_ms - start_ms))

    echo "# stats collection elapsed: ${elapsed_ms} ms"
    kill $PID1 2>/dev/null || true

    #docker compose run --rm client python /app/app.py | tee "$OUT_DIR/${backoff}ms-${concurrency}c-client.json"
    #docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" > "$OUT_DIR/${backoff}ms-${concurrency}c-docker-stats.tsv"
    #docker compose logs --tail=200 server > "$OUT_DIR/${backoff}ms-${concurrency}c-server.log"

    docker compose down -v --remove-orphans
    echo
    echo
    sleep 1
  done
done

printf "Metrics collected in %s\n" "$OUT_DIR"
