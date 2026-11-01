# Lab setup

I ran everything on a Windows 11 laptop (32 GB RAM) with Docker Desktop on the WSL 2 backend. There are no full VMs here. The scanner and the target both run as containers on one private Docker network.

## Components

| Part | What I used |
|---|---|
| Scanner | Greenbone Community Edition (OpenVAS), official containers from `registry.community.greenbone.net` |
| Target | Metasploitable 2 (`tleemcjr/metasploitable2` image) |
| Network | Default compose bridge network, `172.18.0.0/16`. The target was at `172.18.0.16` for the final scan |

The compose file in `lab/compose.yaml` is Greenbone's stock file. I added `lab/compose.override.yaml` to put Metasploitable on the same network. The target publishes no ports to the host, so the only thing that can reach it is the scanner. The Greenbone web UI is bound to `127.0.0.1:9392`.

## Steps

1. Start Docker Desktop.
2. From the `lab` folder, pull the images and start everything:

   ```bash
   docker compose pull
   docker compose up -d
   ```

3. Change the default gvmd admin password (the containers ship with `admin`/`admin`) and export it for the helper scripts:

   ```bash
   docker compose exec -u gvmd gvmd gvmd --user=admin --new-password='pick-something-long'
   export GMP_PASSWORD='pick-something-long'
   ```

4. Wait for the feed. On first start gvmd loads the NVTs, then the SCAP/CPE data, then creates the scan configs. On my machine this took a while. You know it's done when the "Full and fast" config shows up:

   ```bash
   sh gmp.sh "<get_configs filter='rows=-1'/>"
   ```

5. Create the target, create the task, and start it (see `scan.md` for the exact commands I used).
6. Export the report once the task status is `Done`.

## Problems I ran into

- Disk space. The images plus the feed data come to roughly 20 GB. Partway through the first feed load, free space on C: dropped to about 11 GB, every container vanished, and `docker compose up` just hung. Freeing space, restarting Docker Desktop and running `wsl --shutdown` fixed it. The feed data survived because it lives in named volumes.
- The `gvm-tools` container exits right after it starts, so `docker compose exec` against it fails. `gmp.sh` uses `docker compose run --rm` instead.
- My first real scan finished in four minutes with three informational results, which made no sense for Metasploitable. The traceroute result gave it away: the scanner was on `172.18.0.2` and the target I'd configured was `172.19.0.10`. After the Docker restarts, compose had recreated the network on a different subnet and the target got a new IP, so I'd scanned an empty address. I deleted that task, made a new target with the current IP and reran it. Next time I'd pin a static IP in the compose file, or at least check `docker inspect` right before every scan.
- Even with the right IP, the rerun came back almost empty: five low results, no open ports listed. Running `nmap -sS` from inside the `ospd-openvas` container found the ports straight away, so the network was fine. The problem was the built-in "OpenVAS TCP scanner" that Full and fast uses for port discovery, which found nothing in this Docker setup. I cloned Full and fast, switched the Port scanners family to "Nmap (NASL wrapper)" plus "Ping Host", and the scan started finding services.
- A scan I started straight after a restart died in under a second. gvmd was still resyncing its VT table with the scanner, so the task had no tests to run. Waiting for the VT update to finish in the gvmd log fixed it.
- Metasploitable's image has no init process, so the override calls `/bin/services.sh` and then tails `/dev/null` to keep the container alive.

## Ports open on the target

Checked with `netstat -tln` inside the container. On first start:

`21 22 23 25 80 111 139 445 512 513 514 1099 1524 2121 3306 3632 5432 5900 6000 6667 6697 8009 8180 8787`, plus two high RPC ports.

After the Docker restarts, VNC (5900), X11 (6000), AJP (8009) and Tomcat (8180) didn't come back up, and I didn't notice until after the final scan. So those four aren't in the report. It's listed under the scan's limits in the triage.
