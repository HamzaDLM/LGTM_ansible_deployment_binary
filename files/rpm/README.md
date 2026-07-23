Place local RPM packages here.

Any component file ending in `.rpm` is installed from this directory with DNF
on RedHat-family hosts. Default package filenames are configured in
`monitoring_component_files` inside `vars/common_*.yaml`:

- `grafana.rpm`
- `alloy.rpm`
- `tempo.rpm`

Loki and Prometheus default to raw binaries because upstream RPM availability
varies. You can use RPM packages for them by changing their RedHat filenames.

Set `monitoring_rpm_disable_gpg_check: false` in Tower inventory or extra vars
if your RPM signing keys are installed and package signatures must be enforced.
