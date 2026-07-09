# Monitoring Ansible

Minimal Ansible project for deploying a Grafana, Loki, Tempo, and Prometheus monitoring stack through Ansible Tower/AWX. Inventory files are intentionally omitted.

## Playbooks

- `playbooks/deploy_lgtm.yaml` installs Grafana, Loki, Tempo, and Prometheus from raw binaries or local `.deb` packages, writes starter configs, creates data/config directories, and manages systemd services.
- `playbooks/deploy_agents.yaml` installs Grafana Alloy from a raw binary or local `.deb` package, writes a starter agent config, creates data/config directories, and manages its systemd service.
- `playbooks/deploy_nginx.yaml` installs Nginx and exposes Loki, Prometheus, and Tempo ingestion through one gateway on port `443`.

## Configuration

- Environment constants live in `vars/common_dev.yaml`, `vars/common_stg.yaml`, and `vars/common_prod.yaml`.
- Set `env` to `dev`, `stg`, or `prod` in the Tower job template. If omitted, `dev` is used.
- Set `target_hosts` only if the playbook should use a host pattern other than `all`.
- Set individual entries under `monitoring_components_enabled` to `false` to skip installing that component. For example, `grafana: false` skips Grafana while still allowing Loki, Tempo, Prometheus, Alloy, and Nginx to be managed.
- Set artifact filenames under `monitoring_component_files`. Files ending in `.deb` are installed from `files/deb/`; every other file is copied from `files/bin/` as a raw binary.
- Grafana should normally be installed from `grafana.deb`; a single `grafana-server` binary is not enough unless `grafana_home_dir` points to a full Grafana distribution with `conf/defaults.ini` and UI assets.
- Grafana datasources are provisioned automatically for Prometheus, Loki, and Tempo under `/etc/lgtm/grafana/provisioning/datasources/monitoring.yaml`.
- Set `monitoring_gateway_host` to the DNS name agents should use for the Nginx gateway. The generated Alloy config sends Loki and Prometheus traffic to `https://<gateway>:443`, and sends Tempo OTLP gRPC to `<gateway>:443`.
- Provide `nginx_ssl_certificate` and `nginx_ssl_certificate_key` on the gateway host before running `deploy_nginx.yaml`, or set `nginx_generate_self_signed_cert: true` for non-production environments.
- Replace every placeholder under `files/bin/` with the real Linux binary before running.

## Gateway routes

```text
/                                                        -> Grafana on nginx_grafana_upstream
/loki/                                                   -> Loki on nginx_loki_upstream
/prometheus/                                             -> Prometheus on nginx_prometheus_upstream, with /prometheus stripped
/opentelemetry.proto.collector.trace.v1.TraceService/Export -> Tempo OTLP gRPC on nginx_tempo_grpc_upstream
```

## Layout

```text
files/bin/                 Binary placeholders copied by the playbooks
files/deb/                 Local Debian packages copied and installed by apt
playbooks/deploy_lgtm.yaml Server deployment
playbooks/deploy_agents.yaml Agent deployment
playbooks/deploy_nginx.yaml  Nginx gateway deployment
vars/common_*.yaml         Per-environment constants and component toggles
```
