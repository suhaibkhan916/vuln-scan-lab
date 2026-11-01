# Triage: Metasploitable 2 (172.18.0.16)

Scan: OpenVAS 23.51 (Greenbone Community Feed), Full and fast with Nmap port discovery, unauthenticated. Run 1 Nov 2026, 17:00 to 17:36 UTC. Full output in [`reports/`](reports/).

OpenVAS reported 66 findings above log level: **10 critical, 11 high, 39 medium, 6 low**, across 23 open ports. Most of that is noise around the same handful of root causes, so I grouped the findings by root cause and ranked them by what an attacker on the network could actually do, not just by CVSS.

## How I ranked

1. Impact first. Unauthenticated remote root beats everything. Then remote code execution as a service user, then credential exposure, then weaknesses that need an attacker already in the middle.
2. Proof beats inference. Findings where the scanner actually ran a command or logged in (QoD 95 to 99) rank above version-banner matches (QoD 70 to 80).
3. CVSS breaks ties. I moved two findings away from their score: Samba is only 6.0 in OpenVAS but gives a root shell, so it goes up. OS end of life is 10.0 but isn't an exploit on its own, so I treat it as the platform fix behind everything else.

## Ranked findings

| # | Finding | Port | CVSS | Why it ranks here |
|---|---|---|---|---|
| 1 | Ingreslock backdoor | 1524 | 10.0 | Bind shell. Scanner sent `id;` and got `uid=0(root)` back. No exploit needed, just connect |
| 2 | vsftpd 2.3.4 backdoor (CVE-2011-2523) | 21, 6200 | 9.8 | Active check triggered the backdoor and opened a shell on 6200 |
| 3 | rlogin / rsh / rexec with no password | 512-514 | 10.0 | Root login with no password confirmed on rlogin, all three in cleartext |
| 4 | Samba usermap_script RCE (CVE-2007-2447) | 445 | 6.0 | Scanner made the host ping it back. Runs as root on this box, score undersells it |
| 5 | DistCC RCE (CVE-2004-2687) | 3632 | 9.3 | Ran `id` as `daemon`. Easy foothold, then local privesc on an old kernel |
| 6 | dRuby RCE | 8787 | 10.0 | Arbitrary syscalls despite `$SAFE` mode |
| 7 | UnrealIRCd 3.2.8.1 backdoor (CVE-2010-2075) | 6667, 6697 | 7.5 / 8.1 | Trojaned build, remote command execution |
| 8 | Default and weak credentials | 21, 2121, 5432 | 9.0 / 7.5 | `postgres:postgres` on PostgreSQL, `msfadmin:msfadmin` and others on FTP |
| 9 | Web apps: TWiki (CVE-2008-5304/5305), PHP-CGI (CVE-2012-1823), WebDAV PUT, phpinfo | 80 | 10.0 / 7.5 | Code execution through outdated apps, and the scanner uploaded a file via PUT to `/dav/` |
| 10 | Ubuntu 8.04 end of life | n/a | 10.0 | No patches since 2013. Root cause for most of the above |
| 11 | Cleartext and weak crypto: Telnet, FTP, SSLv2/3, weak SSH KEX, expired certs, OpenSSL CCS (CVE-2014-0224) | 22, 23, 25, 5432 | 4.3 to 7.4 | Needs an attacker in path. Fix after the shells are gone |
| 12 | Info leaks: anonymous FTP, SMTP VRFY/EXPN, TRACE, browsable `/doc` | 21, 25, 80 | 5.0 to 6.4 | Helps recon, low direct impact |

## What I'd do first

Items 1 to 7 each give a remote shell with no credentials. On a real network I'd treat this host as already compromised: isolate it, then rebuild it rather than patch it, because a backdoored FTP server and an open root shell mean nothing on the disk can be trusted. Rotate every credential that has ever touched it.

## Limits of this scan

- Unauthenticated, so local package vulnerabilities aren't covered. The real count is higher.
- Tomcat (8180), VNC (5900), X11 (6000) and AJP (8009) weren't running in the container during the final scan, so their known issues (Tomcat manager default creds, VNC password `password`) don't appear here.
- Version-only findings (QoD 70 to 80) weren't manually verified.

## Remediation tracker

Also in [`remediation-tracker.csv`](remediation-tracker.csv) so it can be imported into a spreadsheet or ticketing tool. Target dates follow a 7 / 30 / 90 day SLA for critical / high / medium from the scan date. Nothing is fixed yet since the box is a deliberately vulnerable lab target; "verify" means rescan and confirm the finding is gone.

| ID | Finding (#) | Severity | Action | Target | Status | Verify |
|---|---|---|---|---|---|---|
| R-01 | Ingreslock backdoor (1) | Critical | Remove the inetd entry on 1524, then rebuild host | 2026-11-08 | Open | Port 1524 closed on rescan |
| R-02 | vsftpd backdoor (2) | Critical | Replace vsftpd 2.3.4 with a clean current build, or disable FTP | 2026-11-08 | Open | Backdoor check negative, 6200 closed |
| R-03 | r-services (3) | Critical | Disable rexec, rlogin, rsh in inetd. Use SSH | 2026-11-08 | Open | 512-514 closed |
| R-04 | Samba RCE (4) | Critical | Upgrade Samba past 3.0.25, or remove `username map script` | 2026-11-08 | Open | Active check negative |
| R-05 | DistCC (5) | Critical | Disable distccd, or bind to localhost with `--allow` | 2026-11-08 | Open | 3632 closed |
| R-06 | dRuby (6) | Critical | Stop the DRb service, or bind to localhost | 2026-11-08 | Open | 8787 closed |
| R-07 | UnrealIRCd (7) | Critical | Remove the IRC daemon (not needed) | 2026-11-08 | Open | 6667/6697 closed |
| R-08 | Default credentials (8) | Critical | Change postgres, msfadmin, service, user passwords. Bind PostgreSQL to localhost | 2026-11-08 | Open | Default login checks negative |
| R-09 | Web apps (9) | High | Remove TWiki, phpinfo.php, WebDAV PUT. Upgrade PHP or drop CGI mode | 2026-12-01 | Open | Web findings gone on rescan |
| R-10 | OS end of life (10) | High | Rebuild on a supported Ubuntu LTS | 2026-12-01 | Open | OS EOL check negative |
| R-11 | Cleartext and weak crypto (11) | Medium | Disable Telnet and FTP, TLS 1.2+ only, new 2048-bit certs, modern SSH KEX | 2027-01-30 | Open | SSL/TLS and SSH checks clean |
| R-12 | Info leaks (12) | Medium | Disable anonymous FTP, VRFY/EXPN, TRACE, directory listing | 2027-01-30 | Open | Checks negative |
