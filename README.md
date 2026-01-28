# Third Eye (Multi-tenant Anomaly Detection)

Monorepo:
- apps/api    FastAPI + Postgres + JWT + Blob + Twilio
- apps/worker Camera polling + LLM1/LLM2 + anomaly pipeline
- apps/web    Next.js admin console (envs/cameras/users/anomalies)

Local run: docker compose up
