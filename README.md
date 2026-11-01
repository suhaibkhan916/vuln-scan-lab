# Vulnerability scan lab: OpenVAS vs Metasploitable 2

I set up Greenbone OpenVAS and a deliberately vulnerable Metasploitable 2 host in Docker, scanned it, and wrote up the results the way I would for a real team: a ranked triage on one page and a remediation tracker with owners, deadlines and a way to verify each fix.

## Results at a glance

| | |
|---|---|
| Target | Metasploitable 2 (Ubuntu 8.04), 23 open ports |
| Scanner | OpenVAS 23.51, Greenbone Community Feed, Full and fast |
| Findings | 10 critical, 11 high, 39 medium, 6 low |
| Worst | Root shells with no credentials on 1524 (ingreslock), 21 (vsftpd backdoor), 513 (rlogin) and 445 (Samba) |

The triage is in [TRIAGE.md](TRIAGE.md). The short version: seven separate services hand out a remote shell without credentials, so on a real network this box should be isolated and rebuilt, not patched.

## What's in the repo

```
TRIAGE.md                 one-page ranked triage + remediation tracker
remediation-tracker.csv   same tracker, for a spreadsheet or ticketing tool
reports/                  raw OpenVAS output (PDF, CSV, XML)
docs/setup.md             how I built the lab, and what went wrong
docs/scan.md              scan settings and the exact GMP commands
lab/                      compose files and helper scripts to reproduce it
```

## How I approached the triage

OpenVAS gives you a long list sorted by CVSS, which isn't the same as a priority list. A few things I did differently:

- I grouped findings by root cause. 66 findings collapse into 12 actual problems; five SSL/TLS findings on the same port are one fix, so they get one ticket.
- I ranked by what an attacker gets. An unauthenticated root shell ranks above a 10.0 version-banner match. The Samba bug scores 6.0 in OpenVAS, but the active check proved command execution and smbd runs as root on this box, so I moved it up to #4.
- Findings where the scanner actually ran `id` or logged in (QoD 95 to 99) count for more than version guesses (QoD 70 to 80).
- Each tracker row says how to confirm the fix on the next scan, as well as what to change.

## Things that went wrong (and what I learned)

This took several attempts. The full notes are in [docs/setup.md](docs/setup.md), but the useful lessons were:

- The Greenbone feed is big. Images plus feed come to roughly 20 GB, and the database keeps growing during the CVE import. Docker crashed twice when C: ran low, and the first time it took all the containers with it. Check disk space before you start.
- IPs can change after a restart. When Docker came back, compose put the network on a new subnet. My first "finished" scan had hit an empty address and returned three info results. The traceroute result (scanner on `172.18.x`, target on `172.19.x`) gave it away.
- An empty scan doesn't mean a clean host. The next scan reached the right IP and still found no open ports. `nmap` from inside the scanner container saw them fine, so I switched the scan config's port scanner from the built-in TCP scanner to the Nmap wrapper. The rerun found 23 open ports and 66 findings.

The habit I'm keeping from this: when a scan comes back suspiciously clean, prove the scanner can see the target before trusting the result.

## Reproducing it

You need Docker Desktop and about 30 GB of free disk.

```bash
cd lab
docker compose up -d
```

Wait for the feed to load (see [docs/setup.md](docs/setup.md)), then follow [docs/scan.md](docs/scan.md) to create the target and task, and export the report with:

```bash
python export_report.py REPORT_ID ../reports
```

The Metasploitable container publishes no ports to the host. Only the scanner can reach it, on the internal Docker network. Don't expose it anywhere else.

## Tools

Greenbone Community Edition (OpenVAS, gvmd, ospd-openvas), gvm-tools / GMP, Docker Compose, Nmap, Python for the report export.
