# Monitoring Ansible

Minimal Ansible project for deploying a Grafana, Loki, Tempo, and Prometheus monitoring stack through Ansible Tower/AWX. Inventory files are intentionally omitted.

## Playbooks

- `playbooks/deploy_lgtm.yaml` installs Grafana, Loki, Tempo, and Prometheus binaries, writes starter configs, creates data/config directories, and manages systemd services.
- `playbooks/deploy_agents.yaml` installs Grafana Alloy, writes a starter agent config, creates data/config directories, and manages its systemd service.

## Configuration

- Environment constants live in `vars/common_dev.yaml`, `vars/common_stg.yaml`, and `vars/common_prod.yaml`.
- Set `env` to `dev`, `stg`, or `prod` in the Tower job template. If omitted, `dev` is used.
- Set `target_hosts` only if the playbook should use a host pattern other than `all`.
- Set individual entries under `monitoring_components_enabled` to `false` to skip installing that component. For example, `grafana: false` skips Grafana while still allowing Loki, Tempo, Prometheus, and Alloy to be managed.
- Replace every placeholder under `files/bin/` with the real Linux binary before running.

## Layout

```text
files/bin/                 Binary placeholders copied by the playbooks
playbooks/deploy_lgtm.yaml Server deployment
playbooks/deploy_agents.yaml Agent deployment
vars/common_*.yaml         Per-environment constants and component toggles
```
