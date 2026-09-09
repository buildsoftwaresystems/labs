import json
import os
import threading
import time
import urllib.error
import urllib.request

SERVER_URL = os.getenv("SERVER_URL", "http://server:8080/data")
BACKOFF_MS = int(os.getenv("BACKOFF_MS", "0"))
REQUESTS_PER_RUN = int(os.getenv("REQUESTS_PER_RUN", "1000"))
CONCURRENCY = int(os.getenv("CONCURRENCY", "20"))
WORKER_TIMEOUT_SECONDS = int(os.getenv("WORKER_TIMEOUT_SECONDS", "2"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "10"))


def do_call():
    req = urllib.request.Request(SERVER_URL, headers={"User-Agent": "retry-lab"})
    try:
        with urllib.request.urlopen(req, timeout=WORKER_TIMEOUT_SECONDS) as response:
            return response.status, response.read().decode()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode()
    except Exception as exc:
        return "ERR", str(exc)


def worker_worker():
    attempts = 0
    failures = 0
    successful = 0
    start = time.time()

    for _ in range(REQUESTS_PER_RUN):
        for retry in range(MAX_RETRIES):
            attempts += 1
            status, body = do_call()
            if status == 200:
                successful += 1
                break
            failures += 1
            if retry < MAX_RETRIES - 1:
                time.sleep(BACKOFF_MS / 1000.0)

    elapsed = time.time() - start
    return {
        "attempts": attempts,
        "failures": failures,
        "successful": successful,
        "elapsed_sec": elapsed,
    }


def main():
    results = []
    workers = []
    start = time.time()

    for _ in range(CONCURRENCY):
        thread = threading.Thread(target=lambda: results.append(worker_worker()))
        thread.start()
        workers.append(thread)

    for thread in workers:
        thread.join()

    total_attempts = sum(r["attempts"] for r in results)
    total_failures = sum(r["failures"] for r in results)
    total_successful = sum(r["successful"] for r in results)
    total_elapsed = time.time() - start

    summary = {
        "backoff_ms": BACKOFF_MS,
        "concurrency": CONCURRENCY,
        "requests_per_run": REQUESTS_PER_RUN,
        "total_attempts": total_attempts,
        "total_failures": total_failures,
        "total_successful": total_successful,
        "elapsed_sec": total_elapsed,
    }

    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
