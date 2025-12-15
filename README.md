# DNSScience Tools

**The Complete Network Engineering & DNS Toolkit**

[![Version](https://img.shields.io/badge/version-4.0.0-blue.svg)](https://github.com/straticus1/dnsscience-tools)
[![Python](https://img.shields.io/badge/python-3.10+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)

DNSScience Tools is a unified repository containing the complete suite of network engineering, DNS analysis, and infrastructure management tools from [DNSScience.io](https://dnsscience.io) and [IPScience.io](https://ipscience.io).

## Included Tools

| Tool | Description | Documentation |
|------|-------------|---------------|
| **dnsscience-util** | Advanced DNS analysis, security testing, and debugging | [README](cli/README.md) |
| **DNSNet** | Enterprise DNS/DHCP/IPAM management toolkit | [README](submodules/dnsnet/README.md) |
| **GlobalDetect** | ISP network engineering utilities | [README](submodules/globaldetect/README.md) |
| **RANCID-NG** | Network config backup & change tracking | [README](submodules/rancid-ng/README.md) |

## Quick Start

```bash
# Clone with submodules
git clone --recurse-submodules https://github.com/straticus1/dnsscience-tools.git
cd dnsscience-tools

# Install all tools
./install-all.sh --all --venv

# Activate virtual environment
source .venv/bin/activate

# Verify installation
dnsscience-util --help
dnsnet --help
globaldetect --help
rancid-ng --help
```

## Installation Options

```bash
# Install all tools in virtual environment (recommended)
./install-all.sh --all --venv

# Install all tools system-wide
sudo ./install-all.sh --all --system

# Install specific tools only
./install-all.sh --dnsnet --venv
./install-all.sh --globaldetect --venv
./install-all.sh --rancid --venv

# Create symlinks in /usr/local/bin
./install-all.sh --all --symlink

# Update submodules only
./install-all.sh --submodules
```

## Tool Overview

### dnsscience-util

The world's most advanced DNS analysis, security testing, and debugging tool. Combines features of `dig`, `ldns`, and advanced security analysis.

```bash
# Basic DNS query
dnsscience-util example.com

# DNSSEC validation
dnsscience-util example.com +dnssec

# Global resolver testing (258+ resolvers)
dnsscience-util --global-test example.com

# Security analysis
dnsscience-util --security-analyze example.com

# DNS over HTTPS
dnsscience-util --doh https://cloudflare-dns.com/dns-query example.com

# Domain enrichment via API
dnsscience-util --enrich example.com
```

### DNSNet

Enterprise DNS, DHCP, Cloud, and IPAM management toolkit with compliance support.

```bash
# Configure providers
dnsnet config init

# List DNS zones from Infoblox
dnsnet infoblox dns zones list

# Export zone to BIND format
dnsnet infoblox dns zones export example.com --format bind

# Import Terraform DNS config
dnsnet iac import ./terraform/dns --to-db

# Visual traceroute
dnsnet trace run google.com

# Network ping with stats
dnsnet ping stats 8.8.8.8 -c 100
```

**Supported Platforms:**
- Infoblox, BlueCat, EfficientIP, Men&Mice Micetro
- AWS Route53, Cloudflare, Azure DNS, Google Cloud DNS, OCI, Akamai, NS1
- BIND, PowerDNS, NSD, Unbound
- A10 Thunder, F5 BIG-IP GTM

### GlobalDetect (GlobalConnect)

Comprehensive ISP network engineering utilities.

```bash
# IP information with GeoIP
globaldetect ip info 8.8.8.8 --geoip

# BGP/AS analysis
globaldetect bgp asinfo 15169
globaldetect bgp prefixes 15169

# DNS propagation check
globaldetect dns propagation example.com --type A

# Network diagnostics
globaldetect diag traceroute google.com --geoip
globaldetect diag ping 8.8.8.8

# RBL/Blacklist check (50+ providers)
globaldetect rbl check 1.2.3.4

# SSL/TLS analysis
globaldetect recon ssl google.com

# Neighbor discovery (CDP/LLDP)
sudo globaldetect neighbors discover

# Network inventory
globaldetect system list
globaldetect catalog discover 192.168.1.0/24 --save

# Have I Been Pwned check
globaldetect hibp email user@example.com

# Facility/datacenter lookup
globaldetect facility search "Equinix"
```

### RANCID-NG

Network configuration backup and change tracking (Python rewrite of RANCID).

```bash
# Initialize repository
rancid-ng init --group production

# Run configuration collection
rancid-ng run --group production

# Show configuration changes
rancid-ng diff --device router1

# Interactive login scripts
clogin router.example.com     # Cisco
jlogin switch.example.com     # Juniper
panlogin fw.example.com       # Palo Alto
```

**Supported Devices:**
- Cisco IOS/IOS-XE/NX-OS/IOS-XR, Juniper JunOS, Arista EOS
- Palo Alto PAN-OS, Fortinet FortiGate, F5 BIG-IP
- Cisco IronPort, Proofpoint, BlueCat DDI, Infoblox NIOS

## Additional Tools

| Tool | Description |
|------|-------------|
| `dns4.py` | Fast DNS lookups with multiple resolver support |
| `dns_compare.py` | Compare DNS configurations between servers |
| `dns_cache_validator.py` | Validate DNS cache consistency |
| `visual_traceroute.py` | ASCII visual network path tracing |
| `dnsscience_tickets.py` | DNSScience.io ticket management |

## Repository Structure

```
dnsscience-tools/
├── README.md                 # This file
├── install-all.sh           # Unified installer
├── requirements.txt         # Python dependencies
├── dnsscience-util.py       # Main DNS utility
├── dns4.py                  # Fast DNS lookups
├── dns_compare.py           # DNS comparison tool
├── dns_cache_validator.py   # Cache validator
├── visual_traceroute.py     # Visual traceroute
├── cli/                     # CLI tools
│   └── dnsscience.py        # DNSScience CLI
├── docs/                    # Documentation
├── deploy/                  # Deployment scripts
├── submodules/              # Git submodules
│   ├── dnsnet/              # DNSNet toolkit
│   ├── globaldetect/        # GlobalDetect utilities
│   └── rancid-ng/           # RANCID-NG
└── ansible/                 # Ansible playbooks
```

## Configuration

### API Keys

Several tools require API keys for full functionality:

```bash
# DNSScience.io API
dnsscience-util --api-add-key dns_live_YOUR_API_KEY

# GlobalDetect external services
export IPINFO_TOKEN="your_token"
export ABUSEIPDB_API_KEY="your_key"
export CLOUDFLARE_API_TOKEN="your_token"
export DNSSCIENCE_API_KEY="your_key"
```

### DNSNet Configuration

```bash
dnsnet config init
# Follow prompts to configure providers
```

### RANCID-NG Configuration

Create `~/.cloginrc`:
```
add user router* admin
add password router* {vtypassword} {enablepassword}
add method router* ssh
```

Create `router.db`:
```
router1.example.com:cisco:up
router2.example.com:juniper:up
```

## Requirements

- Python 3.10+
- Git (for submodules)
- Root/sudo for some network operations (ping, traceroute, packet capture)

## Documentation

- [dnsscience-util Guide](docs/DNSSCIENCE-UTIL-GUIDE.md)
- [DNSScience API](docs/DNSSCIENCE-API.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Security Features](docs/SECURITY-FEATURES.md)
- [API Reference](docs/API-REFERENCE.md)
- [Changelog](docs/CHANGELOG.md)

## Support

- **DNSScience.io**: [https://dnsscience.io](https://dnsscience.io)
- **IPScience.io**: [https://ipscience.io](https://ipscience.io)
- **GitHub Issues**: [https://github.com/straticus1/dnsscience-tools/issues](https://github.com/straticus1/dnsscience-tools/issues)

## License

MIT License - see [LICENSE](LICENSE) for details.

## Credits

DNSScience Tools is developed by [After Dark Systems, LLC](https://afterdarksystems.com).

---

**Made with expertise in DNS, security, and network engineering.**
