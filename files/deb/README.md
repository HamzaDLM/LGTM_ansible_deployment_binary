Place local Debian packages here.

Any component file ending in `.deb` is installed from this directory with APT
on Debian-family hosts. Default package filenames are configured in
`monitoring_component_files` inside `vars/common_*.yaml`:

- `alloy.deb`
- `grafana.deb`
- `tempo.deb`

You can also use versioned package names by changing `monitoring_component_files`.
