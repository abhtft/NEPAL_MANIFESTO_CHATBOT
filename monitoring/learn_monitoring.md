Short answer: No env is needed if you run Phoenix locally with defaults.
6006 is the UI port, not the tracing endpoint. Phoenix’s OTLP collector listens on 4317 (gRPC) and 4318 (HTTP).
With your current setup, init_arize_tracing() uses Phoenix defaults, so if Phoenix is running locally, traces will flow without extra env vars.
You only need env vars when:
Phoenix runs on a different host/container (e.g., set OTEL_EXPORTER_OTLP_ENDPOINT=http://phoenix:4317 in Docker).
You change the collector protocol/ports.
Make sure Phoenix is actually running (UI at http://localhost:6006 and collector on 4317/4318). The UI port (6006) doesn’t go into the OTLP env var.