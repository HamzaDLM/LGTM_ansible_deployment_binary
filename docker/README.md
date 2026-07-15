# Local LGTM Lab

This directory contains a local Docker Compose lab for experimenting with Grafana, Loki, Tempo, Prometheus, Alloy, Nginx, Redis, and a minimal FastAPI service.

## Start

```bash
cd docker
docker compose up --build
```

Open:

- Grafana: <http://localhost:3000> (`admin` / `admin`)
- Demo app through Nginx: <http://localhost:8080>
- Alloy UI: <http://localhost:12345>

## Generate Signals

```bash
curl http://localhost:8080/
curl http://localhost:8080/slow
curl http://localhost:8080/error
curl http://localhost:8080/cache/example
```

The FastAPI app exposes Prometheus metrics at `/metrics`, writes JSON logs to stdout, and sends OpenTelemetry traces to Alloy. Alloy scrapes metrics and sends them to Prometheus through remote write, collects Docker logs and sends them to Loki, and forwards traces to Tempo.

## Flow

```text
FastAPI /metrics      -> Alloy -> Prometheus -> Grafana
Nginx exporter        -> Alloy -> Prometheus -> Grafana
Redis exporter        -> Alloy -> Prometheus -> Grafana
Docker container logs -> Alloy -> Loki   -> Grafana
FastAPI OTLP traces   -> Alloy -> Tempo  -> Grafana
```

For real projects, copy the FastAPI instrumentation pattern into each backend, keep logs on stdout, expose service metrics, and run Alloy as a sidecar or host/container-level collector rather than inside the application container.
