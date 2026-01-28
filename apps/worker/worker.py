import os, time, requests
API = os.getenv("API_BASE_URL", "http://localhost:8001")
POLL = int(os.getenv("WORKER_POLL_SECONDS","10"))

print(f"[worker] API={API} POLL={POLL}")

# Placeholder: in production, worker authenticates as org service account and pulls enabled cameras per org/env.
# For now, worker is a scaffold—your existing anomaly detector logic is plugged here next.

while True:
    try:
        # health check just to keep container alive
        r = requests.get(f"{API}/health", timeout=5)
        print("[worker] health:", r.status_code)
    except Exception as e:
        print("[worker] err:", e)
    time.sleep(POLL)
