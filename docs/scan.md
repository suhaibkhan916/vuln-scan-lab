# Scan configuration

I drove gvmd over GMP from the command line instead of clicking through the web UI, mostly so the steps are repeatable. `lab/gmp.sh` wraps `gvm-cli` in the `gvm-tools` container and reads the admin password from `GMP_PASSWORD`, so no credentials live in the repo.

## Settings

| Setting | Value |
|---|---|
| Target | `172.18.0.16` (Metasploitable 2) |
| Port list | All TCP and Nmap top 100 UDP |
| Alive test | Consider Alive (skips host discovery, the host is known to be up) |
| Scan config | Full and fast (nmap ports): a clone of Full and fast with Nmap as the port scanner, see below |
| Scanner | OpenVAS Default |
| Credentials | None. This is an unauthenticated, external-view scan |

## Commands

Create the target:

```bash
sh gmp.sh "<create_target><name>Metasploitable2</name><hosts>172.18.0.16</hosts><port_list id='730ef368-57e2-11e1-a90f-406186ea4fc5'/><alive_tests>Consider Alive</alive_tests></create_target>"
```

Clone Full and fast and swap the port scanner for Nmap. The stock config uses the built-in OpenVAS TCP scanner, which found no ports at all in my Docker setup:

```bash
sh gmp.sh "<create_config><copy>daba56c8-73ec-11df-a475-002264764cea</copy><name>Full and fast (nmap ports)</name></create_config>"
sh gmp.sh "<modify_config config_id='CONFIG_ID'><nvt_selection><family>Port scanners</family><nvt oid='1.3.6.1.4.1.25623.1.0.14259'/><nvt oid='1.3.6.1.4.1.25623.1.0.100315'/></nvt_selection></modify_config>"
```

Create the task (scanner ID is OpenVAS Default):

```bash
sh gmp.sh "<create_task><name>Metasploitable2 - Full and fast</name><target id='TARGET_ID'/><config id='CONFIG_ID'/><scanner id='08b69003-5fc2-4037-a479-93b440211c73'/></create_task>"
```

Start it and poll until the status is `Done`:

```bash
sh gmp.sh "<start_task task_id='TASK_ID'/>"
sh gmp.sh "<get_tasks task_id='TASK_ID'/>"
```

Export the report. The format IDs are the built-in PDF, CSV Results and XML formats:

```bash
sh gmp.sh "<get_reports report_id='REPORT_ID' format_id='c402cc3e-b531-11e1-9163-406186ea4fc5' details='1' filter='apply_overrides=0 min_qod=70 rows=-1'/>"
```

The PDF and CSV come back base64 encoded inside the XML response, so they need to be decoded before saving.

## Why unauthenticated

An unauthenticated scan shows what an attacker on the same network sees without any foothold. It misses local package vulnerabilities that an authenticated (SSH) scan would catch, so the real exposure of this box is worse than the report shows. On Metasploitable that hardly matters, since the network-facing problems are bad enough on their own.
