# Setting up your own proxy nodes

This project supports comparing a direct request against a request routed
through a proxy you configure in `proxies.yaml`. To get real region-to-region
data (rather than a single vendor's shared pool), the recommended setup is
running a tiny proxy yourself on a couple of cheap/free VMs in different
regions.

## 1. Pick 2-3 regions

Free/cheap tiers that work fine for this:
- Oracle Cloud Free Tier (always-free ARM VM)
- AWS Lightsail ($3.50-5/mo, many regions)
- DigitalOcean ($4-6/mo droplet)

Pick regions that are actually different from each other, e.g. one EU, one
US-East, one Asia.

## 2. Install a minimal forward proxy (tinyproxy)

On each VM (Ubuntu/Debian example):

```bash
sudo apt update && sudo apt install -y tinyproxy
sudo nano /etc/tinyproxy/tinyproxy.conf
```

Key settings to check/edit:
- `Port 8888`
- `Allow` block: add your own home/office IP so the proxy isn't open to the
  world (`Allow 203.0.113.5`)
- Optionally set `BasicAuth user password` for a login

Restart it:

```bash
sudo systemctl restart tinyproxy
sudo systemctl enable tinyproxy
```

Open the port in the cloud provider's firewall/security group (not just the
OS firewall).

## 3. Add it to proxies.yaml

```yaml
proxies:
  - label: eu-west
    host: <vm public ip>
    port: 8888
    scheme: http
    region: eu-west
```

## 4. Sanity-check it directly before wiring it into the app

```bash
curl -x http://<vm public ip>:8888 https://httpbin.org/ip
```

If that returns the VM's IP, the app will see the same thing.

## Notes

- `proxies.yaml` is gitignored on purpose - never commit real proxy
  hosts/credentials.
- Lock down `Allow`/security-group rules to your own IP. An open proxy on
  the public internet will get abused within hours.
