# Monitoring Ansible

Minimal Ansible project for deploying a Grafana, Loki, Tempo, and Prometheus
monitoring stack to Debian-family and RHEL-family 8+ systems through Ansible
Tower/AWX. Inventory files are intentionally omitted.

## Playbooks

- `playbooks/deploy_lgtm.yaml` installs Grafana, Loki, Tempo, and Prometheus from raw binaries, local `.deb` packages, or local `.rpm` packages, writes starter configs, creates data/config directories, and manages systemd services.
- `playbooks/deploy_agents.yaml` installs Grafana Alloy from a raw binary, local `.deb` package, or local `.rpm` package, writes a starter agent config, creates data/config directories, and manages its systemd service.
- `playbooks/deploy_nginx.yaml` installs Nginx and exposes Loki, Prometheus, and Tempo ingestion through one gateway on port `443`.

## Configuration

- Environment constants live in `vars/common_dev.yaml`, `vars/common_stg.yaml`, and `vars/common_prod.yaml`.
- Set `env` to `dev`, `stg`, or `prod` in the Tower job template. If omitted, `dev` is used.
- Set `target_hosts` only if the playbook should use a host pattern other than `all`.
- Set individual entries under `monitoring_components_enabled` to `false` to skip installing that component. For example, `grafana: false` skips Grafana while still allowing Loki, Tempo, Prometheus, Alloy, and Nginx to be managed.
- Set OS-specific artifact filenames under `monitoring_component_files`. Files ending in `.deb` are installed from `files/deb/`, files ending in `.rpm` are installed from `files/rpm/`, and every other file is copied from `files/bin/` as a raw binary.
- Grafana should normally be installed from `grafana.deb` or `grafana.rpm`; a single `grafana-server` binary is not enough unless `grafana_home_dir` points to a full Grafana distribution with `conf/defaults.ini` and UI assets.
- Grafana datasources are provisioned automatically for Prometheus, Loki, and Tempo under `/etc/lgtm/grafana/provisioning/datasources/monitoring.yaml`.
- Grafana provisions the `Monitoring Stack Overview` dashboard automatically. Prometheus scrapes Grafana, Loki, Tempo, and itself to populate stack health and ingestion panels.
- Rendered service configs and gateway configs are sourced from Jinja templates under `configs/`.
- An importable Linux fleet dashboard is available at `files/grafana/dashboards/linux-fleet-overview.json`.
- Alloy config is generated from modular templates under `configs/alloy/templates/`. Tower inventory host or group vars choose the integrations for each server.
- Alloy live debugging is enabled by default in dev/stg through `alloy_live_debugging_enabled`. Open `http://<agent-host>:12345` to inspect component state and live data flowing through pipelines.
- Set `monitoring_gateway_host` to the DNS name agents should use for the Nginx gateway. The generated Alloy config sends Loki and Prometheus traffic to `https://<gateway>:443`, and sends Tempo OTLP gRPC to `<gateway>:443`.
- Provide `nginx_ssl_certificate` and `nginx_ssl_certificate_key` on the gateway host before running `deploy_nginx.yaml`, or set `nginx_generate_self_signed_cert: true` for non-production environments.
- Replace every placeholder under `files/bin/` with the real Linux binary before running.

## Debian and RHEL artifacts

The same Tower inventory can contain both Debian-family and RHEL-family hosts.
The playbooks select the artifact using `ansible_os_family`:

```yaml
monitoring_component_files:
  grafana:
    Debian: grafana.deb
    RedHat: grafana.rpm
  loki:
    Debian: loki
    RedHat: loki
  tempo:
    Debian: tempo.deb
    RedHat: tempo.rpm
  prometheus:
    Debian: prometheus
    RedHat: prometheus
  alloy:
    Debian: alloy.deb
    RedHat: alloy.rpm
```

Scalar filenames remain supported when the same raw binary is used on both
platforms. A `.deb` selected on RedHat or an `.rpm` selected on Debian fails
before installation with a host-specific error.

RPM packages are installed with DNF on RHEL-family version 8 or newer. Local
RPM signature checking is disabled by default; set
`monitoring_rpm_disable_gpg_check: false` in Tower inventory or extra vars when
package-signing keys are installed.

On RHEL with SELinux enabled, `deploy_nginx.yaml` enables
`httpd_can_network_connect` so Nginx can proxy to Grafana, Loki, Prometheus, and
Tempo. Set `nginx_selinux_allow_network_connect: false` if SELinux policy is
managed separately.

The playbook does not modify firewalld. Port `443/tcp` must be allowed through
your existing RHEL firewall policy.

On Debian, Alloy's service user joins `adm` and `systemd-journal`. On RHEL it
joins `systemd-journal`. If an integration's log files require another existing
group, set it explicitly in Tower inventory:

```yaml
alloy_log_reader_groups:
  - systemd-journal
  - nginx
```

## Alloy inventory variables

Set these in Ansible Tower inventory host vars or group vars:

```yaml
alloy_environment: production
alloy_project: payments
alloy_team: network-apps

alloy_enabled_integrations:
  - host
  - nginx
  - uvicorn
  - redis

alloy_nginx:
  access_log: /var/log/nginx/access.log
  error_log: /var/log/nginx/error.log

alloy_uvicorn:
  metrics_url: http://127.0.0.1:8000/metrics
  log_path: /var/log/payments-api/*.log

alloy_redis:
  address: redis://127.0.0.1:6379
```

Defaults live in `vars/alloy_defaults.yaml`. If `alloy_enabled_integrations` is omitted, only `host` is enabled. Common labels are added through shared relabel components for metrics and logs: `instance`, `environment`, `project`, and `team`.

The agent playbook validates the enabled integrations before rendering Alloy. Unknown integration names fail, and enabled integrations with required missing settings fail with a host-specific error message.

To add a new integration later:

1. Add `configs/alloy/templates/integrations/<name>.alloy.j2`.
2. Add `<name>` to `alloy_supported_integrations`.
3. Add required settings to `alloy_integration_required_options` only if that integration needs validation.

Example Tower host vars are in `examples/inventory/host_vars/`. Generated example Alloy configs are in `examples/generated-alloy/`.

## Gateway routes

```text
/                                                        -> Grafana on nginx_grafana_upstream
/loki/                                                   -> Loki on nginx_loki_upstream
/prometheus/                                             -> Prometheus on nginx_prometheus_upstream, with /prometheus stripped
/opentelemetry.proto.collector.trace.v1.TraceService/Export -> Tempo OTLP gRPC on nginx_tempo_grpc_upstream
```

## Layout

```text
configs/                         Jinja templates rendered by the deploy playbooks
configs/alloy/templates/         Modular Alloy templates
examples/inventory/host_vars/    Example Tower inventory host variables
examples/generated-alloy/        Rendered Alloy examples
files/bin/                       Binary placeholders copied by the playbooks
files/deb/                       Local Debian packages copied and installed by apt
files/rpm/                       Local RPM packages copied and installed by dnf
files/grafana/dashboards/        Importable Grafana dashboards
playbooks/deploy_lgtm.yaml       Server deployment
playbooks/deploy_agents.yaml     Agent deployment
playbooks/deploy_nginx.yaml      Nginx gateway deployment
vars/alloy_defaults.yaml         Alloy integration defaults and validation metadata
vars/common_*.yaml               Per-environment constants and component toggles
```
