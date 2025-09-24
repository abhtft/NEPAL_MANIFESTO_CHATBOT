## Phoenix tracing configuration examples

### Local defaults (no env needed)
- Start Phoenix locally (UI on `http://localhost:6006`).
- Our tracing init uses Phoenix defaults: OTLP gRPC on `localhost:4317`. No env vars required.

### Local override: HTTP OTLP (4318)
Use HTTP if 4317 is blocked or you prefer HTTP.

Windows Command Prompt:
```bat
set OTEL_EXPORTER_OTLP_TRACES_PROTOCOL=http/protobuf
set OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://localhost:4318/v1/traces
streamlit run app.py
```

PowerShell:
```powershell
$env:OTEL_EXPORTER_OTLP_TRACES_PROTOCOL = "http/protobuf"
$env:OTEL_EXPORTER_OTLP_TRACES_ENDPOINT = "http://localhost:4318/v1/traces"
streamlit run app.py
```

Linux/macOS (bash):
```bash
export OTEL_EXPORTER_OTLP_TRACES_PROTOCOL=http/protobuf
export OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://localhost:4318/v1/traces
streamlit run app.py
```

### Local override: gRPC OTLP (4317)
Explicitly set gRPC endpoint if needed.

```bash
export OTEL_EXPORTER_OTLP_TRACES_PROTOCOL=grpc
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
streamlit run app.py
```

### Docker Compose example
```yaml
services:
  app:
    build: .
    environment:
      - OTEL_EXPORTER_OTLP_TRACES_PROTOCOL=http/protobuf
      - OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://phoenix:4318/v1/traces
    ports:
      - "8501:8501"
    depends_on:
      - phoenix

  phoenix:
    image: arizeai/phoenix:latest
    ports:
      - "6006:6006"   # UI
      - "4317:4317"   # gRPC OTLP
      - "4318:4318"   # HTTP OTLP
```

### Azure App Service example
Set these in App Service → Configuration → Application settings.

- `OTEL_EXPORTER_OTLP_TRACES_PROTOCOL` = `http/protobuf`
- `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT` = `https://<your-phoenix-domain>/v1/traces`
- Optional (if auth enabled): `OTEL_EXPORTER_OTLP_HEADERS` = `authorization=Bearer <TOKEN>`

If you expose gRPC 4317 instead:
- `OTEL_EXPORTER_OTLP_TRACES_PROTOCOL` = `grpc`
- `OTEL_EXPORTER_OTLP_ENDPOINT` = `http://<host>:4317`

### Verify it works
- Run the app; you should see console lines like:
  - `OpenTelemetry Tracing Details … Collector Endpoint: localhost:4317`
  - `✅ Phoenix tracing enabled.`
- Open the Phoenix UI (local: `http://localhost:6006`, Azure: your domain) and confirm spans for retrieval and LLM calls.

### Notes and pitfalls
- The UI port (6006) is for the browser only. Do not set 6006 in OTLP env vars.
- If you instrument multiple times, Phoenix may log "Attempting to instrument while already instrumented"; this is safe but avoid duplicate init.
- In production, consider a `BatchSpanProcessor` and restricting payload size; by default, Phoenix uses a simple processor.

