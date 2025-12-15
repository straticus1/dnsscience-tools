#!/usr/bin/env python3
"""
DNSScience API Utility - Complete CLI access to DNSScience.io & IPScience.io APIs

Version: 1.0.0

Usage:
    dnsscience-api-util.py <command> [options]
    dnsscience-api-util.py --help

Global Options:
    -j, --json      Output in JSON format
    -p, --pretty    Pretty-print JSON output (implies --json)
    --api-key KEY   Use specific API key (overrides config)
    --quiet         Suppress non-essential output
"""

import sys
import os
import json
import argparse
import requests
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

__version__ = "1.0.0"

# Configuration file location
CONFIG_DIR = Path.home() / ".dnsscience"
CONFIG_FILE = CONFIG_DIR / "config.json"


class Colors:
    """ANSI color codes for terminal output."""
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    END = '\033[0m'

    @classmethod
    def disable(cls):
        """Disable colors."""
        cls.CYAN = cls.GREEN = cls.YELLOW = cls.RED = cls.BOLD = cls.DIM = cls.END = ''


def colored(text: str, color: str) -> str:
    """Apply color to text."""
    return f"{color}{text}{Colors.END}"


class APIError(Exception):
    """API error with status code and message."""
    def __init__(self, message: str, status_code: int = None, response: Dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response or {}


class Config:
    """Configuration management."""

    def __init__(self):
        self.api_key: Optional[str] = None
        self.api_url: str = "https://www.dnsscience.io"
        self.ipscience_url: str = "https://ip.dnsscience.io"
        self.email: Optional[str] = None
        self._load()

    def _load(self):
        """Load configuration from file."""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE) as f:
                    data = json.load(f)
                    self.api_key = data.get('api_key')
                    self.api_url = data.get('api_url', self.api_url)
                    self.ipscience_url = data.get('ipscience_url', self.ipscience_url)
                    self.email = data.get('email')
            except (json.JSONDecodeError, IOError):
                pass

    def save(self):
        """Save configuration to file."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump({
                'api_key': self.api_key,
                'api_url': self.api_url,
                'ipscience_url': self.ipscience_url,
                'email': self.email
            }, f, indent=2)
        os.chmod(CONFIG_FILE, 0o600)

    def is_authenticated(self) -> bool:
        return bool(self.api_key)


class DNSScienceAPI:
    """Client for DNSScience.io and IPScience.io APIs."""

    def __init__(self, api_key: Optional[str] = None, api_url: Optional[str] = None):
        self.config = Config()
        self.api_key = api_key or self.config.api_key
        self.api_url = (api_url or self.config.api_url).rstrip('/')
        self.ipscience_url = self.config.ipscience_url.rstrip('/')
        self.session = requests.Session()
        if self.api_key:
            self.session.headers['X-API-Key'] = self.api_key
        self.session.headers['User-Agent'] = f'dnsscience-api-util/{__version__}'
        self.session.headers['Accept'] = 'application/json'

    def _request(self, method: str, endpoint: str, base_url: str = None, **kwargs) -> Dict[str, Any]:
        """Make an API request."""
        base = base_url or self.api_url
        url = f"{base}{endpoint}"
        try:
            response = self.session.request(method, url, timeout=30, **kwargs)
            data = response.json() if response.text else {}

            if response.status_code >= 400:
                error_msg = data.get('error', data.get('message', f'HTTP {response.status_code}'))
                raise APIError(error_msg, response.status_code, data)

            return data
        except requests.exceptions.ConnectionError:
            raise APIError("Failed to connect to API server. Check your internet connection.")
        except requests.exceptions.Timeout:
            raise APIError("Request timed out. Try again later.")
        except requests.exceptions.RequestException as e:
            raise APIError(f"Request failed: {str(e)}")
        except json.JSONDecodeError:
            return {'raw_response': response.text}

    def _get(self, endpoint: str, params: Dict = None, base_url: str = None) -> Dict[str, Any]:
        return self._request('GET', endpoint, base_url=base_url, params=params)

    def _post(self, endpoint: str, data: Dict = None, json_data: Dict = None, base_url: str = None) -> Dict[str, Any]:
        return self._request('POST', endpoint, base_url=base_url, data=data, json=json_data)

    def _delete(self, endpoint: str, base_url: str = None) -> Dict[str, Any]:
        return self._request('DELETE', endpoint, base_url=base_url)

    # ==========================================
    # Authentication
    # ==========================================

    def login(self, email: str, password: str) -> Dict[str, Any]:
        """Login and get API key."""
        return self._post('/api/auth/login', json_data={'email': email, 'password': password})

    def get_me(self) -> Dict[str, Any]:
        """Get current user info."""
        return self._get('/api/auth/me')

    # ==========================================
    # Domain / DNS Operations (dnsscience.io)
    # ==========================================

    def scan_domain(self, domain: str, full: bool = False) -> Dict[str, Any]:
        """Run comprehensive domain scan."""
        params = {'full': 'true' if full else 'false'}
        return self._post('/api/scan', json_data={'domain': domain, **params})

    def get_domain(self, domain: str) -> Dict[str, Any]:
        """Get domain information."""
        return self._get(f'/api/domain/{domain}')

    def get_domain_history(self, domain: str, limit: int = 100) -> Dict[str, Any]:
        """Get domain scan history."""
        return self._get(f'/api/domain/{domain}/history', params={'limit': limit})

    def get_domain_timeline(self, domain: str) -> Dict[str, Any]:
        """Get domain timeline."""
        return self._get(f'/api/domain/{domain}/timeline')

    def get_domain_profile(self, domain: str) -> Dict[str, Any]:
        """Get complete domain profile."""
        return self._get(f'/api/domain/{domain}/complete-profile')

    def search_domains(self, query: str, limit: int = 50) -> Dict[str, Any]:
        """Search domains."""
        return self._get('/api/search', params={'q': query, 'limit': limit})

    def list_domains(self, page: int = 1, per_page: int = 50) -> Dict[str, Any]:
        """List tracked domains."""
        return self._get('/api/domains', params={'page': page, 'per_page': per_page})

    def compare_domain(self, domain: str) -> Dict[str, Any]:
        """Compare domain DNS across resolvers."""
        return self._get(f'/api/compare/{domain}')

    # ==========================================
    # DNS Tools
    # ==========================================

    def dns_propagation(self, domain: str, record_type: str = 'A') -> Dict[str, Any]:
        """Check DNS propagation."""
        return self._get('/api/tools/propagation', params={'domain': domain, 'type': record_type})

    def dnssec_validate(self, domain: str) -> Dict[str, Any]:
        """Validate DNSSEC chain."""
        return self._get('/api/tools/dnssec-validate', params={'domain': domain})

    def dns_compare(self, domain: str, servers: List[str] = None) -> Dict[str, Any]:
        """Compare DNS across servers."""
        data = {'domain': domain}
        if servers:
            data['servers'] = servers
        return self._post('/api/tools/dns-compare', json_data=data)

    def convert_zone(self, zone_data: str, input_format: str, output_format: str) -> Dict[str, Any]:
        """Convert zone file format."""
        return self._post('/api/tools/convert-zone', json_data={
            'zone': zone_data,
            'input_format': input_format,
            'output_format': output_format
        })

    # ==========================================
    # Certificates
    # ==========================================

    def get_cert_chain(self, domain: str) -> Dict[str, Any]:
        """Get SSL certificate chain."""
        return self._get('/api/tools/cert-chain', params={'domain': domain})

    def list_certificates(self, page: int = 1, per_page: int = 50) -> Dict[str, Any]:
        """List tracked certificates."""
        return self._get('/api/certificates', params={'page': page, 'per_page': per_page})

    def get_domain_certificates(self, domain: str) -> Dict[str, Any]:
        """Get certificates for domain."""
        return self._get(f'/api/domain/{domain}/certificates')

    def get_expiring_certs(self, days: int = 30) -> Dict[str, Any]:
        """Get expiring certificates."""
        return self._get('/api/certificates/expiring', params={'days': days})

    def get_expired_certs(self) -> Dict[str, Any]:
        """Get expired certificates."""
        return self._get('/api/certificates/expired')

    # ==========================================
    # DNS Records
    # ==========================================

    def list_dns_records(self, domain: str = None, record_type: str = None, page: int = 1) -> Dict[str, Any]:
        """List DNS records."""
        params = {'page': page}
        if domain:
            params['domain'] = domain
        if record_type:
            params['type'] = record_type
        return self._get('/api/dns-records', params=params)

    # ==========================================
    # Subdomains
    # ==========================================

    def list_subdomains(self, domain: str = None, page: int = 1, per_page: int = 50) -> Dict[str, Any]:
        """List discovered subdomains."""
        params = {'page': page, 'per_page': per_page}
        if domain:
            params['domain'] = domain
        return self._get('/api/subdomains', params=params)

    # ==========================================
    # Enrichment / RDAP / Web3
    # ==========================================

    def enrich_domain(self, domain: str) -> Dict[str, Any]:
        """Get comprehensive domain enrichment."""
        return self._get('/api/enrichment', params={'domain': domain})

    def rdap_lookup(self, domain: str) -> Dict[str, Any]:
        """RDAP/WHOIS lookup."""
        return self._get('/api/rdap', params={'domain': domain})

    def web3_domains(self, address: str = None) -> Dict[str, Any]:
        """Get Web3 domain information."""
        params = {}
        if address:
            params['address'] = address
        return self._get('/api/web3-domains', params=params)

    # ==========================================
    # Threats / Security
    # ==========================================

    def list_threats(self, domain: str = None, page: int = 1) -> Dict[str, Any]:
        """List threat detections."""
        params = {'page': page}
        if domain:
            params['domain'] = domain
        return self._get('/api/threats', params=params)

    def threat_intel(self, target: str) -> Dict[str, Any]:
        """Get threat intelligence."""
        return self._get(f'/api/threat-intel/{target}')

    def blacklist_check(self, target: str) -> Dict[str, Any]:
        """Check blacklist status."""
        return self._get('/api/browse/blacklists', params={'target': target})

    # ==========================================
    # Reverse DNS
    # ==========================================

    def reverse_dns(self, ip: str) -> Dict[str, Any]:
        """Reverse DNS lookup."""
        return self._get('/api/reverse-dns', params={'ip': ip})

    def reverse_dns_issues(self, page: int = 1) -> Dict[str, Any]:
        """Get reverse DNS issues."""
        return self._get('/api/reverse-dns/issues', params={'page': page})

    # ==========================================
    # IP Operations (ipscience.io)
    # ==========================================

    def ip_lookup(self, ip: str) -> Dict[str, Any]:
        """Get IP information."""
        return self._get(f'/api/ip/{ip}', base_url=self.ipscience_url)

    def ip_geoip(self, ip: str = None) -> Dict[str, Any]:
        """Get GeoIP data."""
        if ip:
            return self._get(f'/api/geoip/{ip}', base_url=self.ipscience_url)
        return self._get('/api/geoip/me', base_url=self.ipscience_url)

    def ip_reputation(self, ip: str) -> Dict[str, Any]:
        """Get IP reputation."""
        return self._get(f'/api/ip/{ip}/reputation', base_url=self.ipscience_url)

    def ip_bgp(self, ip: str) -> Dict[str, Any]:
        """Get BGP info for IP."""
        return self._get(f'/api/ip/{ip}/bgp', base_url=self.ipscience_url)

    def ip_profile(self, ip: str) -> Dict[str, Any]:
        """Get complete IP profile."""
        return self._get(f'/api/ip/{ip}/complete-profile', base_url=self.ipscience_url)

    def ip_scan(self, ip: str, ports: str = None) -> Dict[str, Any]:
        """Scan IP address."""
        params = {}
        if ports:
            params['ports'] = ports
        return self._get(f'/api/ip/{ip}/scan', base_url=self.ipscience_url, params=params)

    # ==========================================
    # ASN Operations (ipscience.io)
    # ==========================================

    def asn_lookup(self, asn: str) -> Dict[str, Any]:
        """Get ASN information."""
        asn = str(asn).upper().replace('AS', '')
        return self._get(f'/api/asn/{asn}', base_url=self.ipscience_url)

    def asn_prefixes(self, asn: str, ip_type: str = None) -> Dict[str, Any]:
        """Get ASN prefixes."""
        asn = str(asn).upper().replace('AS', '')
        params = {}
        if ip_type:
            params['type'] = ip_type
        return self._get(f'/api/asn/{asn}/prefixes', base_url=self.ipscience_url, params=params)

    def asn_peers(self, asn: str) -> Dict[str, Any]:
        """Get ASN peers."""
        asn = str(asn).upper().replace('AS', '')
        return self._get(f'/api/asn/{asn}/peers', base_url=self.ipscience_url)

    # ==========================================
    # Network Tools
    # ==========================================

    def traceroute(self, target: str, max_hops: int = 30) -> Dict[str, Any]:
        """Visual traceroute."""
        return self._post('/api/traceroute', base_url=self.ipscience_url, json_data={
            'target': target,
            'max_hops': max_hops
        })

    def whois(self, target: str) -> Dict[str, Any]:
        """WHOIS lookup."""
        return self._get(f'/api/whois/{target}', base_url=self.ipscience_url)

    def facilities(self, ip: str = None) -> Dict[str, Any]:
        """Get data center facilities."""
        if ip:
            return self._get(f'/api/facilities/ip/{ip}', base_url=self.ipscience_url)
        return self._get('/api/facilities', base_url=self.ipscience_url)

    # ==========================================
    # Account / Subscription
    # ==========================================

    def get_account_usage(self) -> Dict[str, Any]:
        """Get API usage statistics."""
        return self._get('/api/account/usage')

    def get_subscription(self) -> Dict[str, Any]:
        """Get subscription details."""
        return self._get('/api/subscription/current')

    def get_invoices(self) -> Dict[str, Any]:
        """Get invoices."""
        return self._get('/api/subscription/invoices')

    def list_api_keys(self) -> Dict[str, Any]:
        """List API keys."""
        return self._get('/api/account/api-keys')

    def create_api_key(self, name: str) -> Dict[str, Any]:
        """Create new API key."""
        return self._post('/api/account/api-keys', json_data={'name': name})

    def delete_api_key(self, key_id: str) -> Dict[str, Any]:
        """Delete API key."""
        return self._delete(f'/api/account/api-keys/{key_id}')

    # ==========================================
    # Bulk Operations
    # ==========================================

    def bulk_ip_lookup(self, ips: List[str]) -> Dict[str, Any]:
        """Bulk IP lookup."""
        return self._post('/api/bulk/ip', base_url=self.ipscience_url, json_data={'ips': ips})

    def bulk_domain_scan(self, domains: List[str]) -> Dict[str, Any]:
        """Bulk domain scan."""
        return self._post('/api/bulk/scan', json_data={'domains': domains})

    # ==========================================
    # Stats / Health
    # ==========================================

    def get_stats(self) -> Dict[str, Any]:
        """Get platform statistics."""
        return self._get('/api/stats')

    def health_check(self) -> Dict[str, Any]:
        """Health check."""
        return self._get('/api/health')


class OutputFormatter:
    """Format output for display."""

    def __init__(self, json_output: bool = False, pretty: bool = False, quiet: bool = False):
        self.json_output = json_output or pretty
        self.pretty = pretty
        self.quiet = quiet

    def output(self, data: Any, title: str = None):
        """Output data in configured format."""
        if self.json_output:
            if self.pretty:
                print(json.dumps(data, indent=2, default=str))
            else:
                print(json.dumps(data, default=str))
        else:
            if title and not self.quiet:
                print(colored(f"\n{title}", Colors.CYAN + Colors.BOLD))
                print(colored("-" * len(title), Colors.CYAN))
            self._print_dict(data)

    def _print_dict(self, data: Any, indent: int = 0):
        """Pretty print dictionary data."""
        prefix = "  " * indent
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    print(f"{prefix}{colored(key + ':', Colors.YELLOW)}")
                    self._print_dict(value, indent + 1)
                else:
                    print(f"{prefix}{colored(key + ':', Colors.YELLOW)} {value}")
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, dict):
                    print(f"{prefix}[{i}]")
                    self._print_dict(item, indent + 1)
                else:
                    print(f"{prefix}- {item}")
        else:
            print(f"{prefix}{data}")

    def error(self, message: str):
        """Print error message."""
        if self.json_output:
            print(json.dumps({'error': message}))
        else:
            print(colored(f"Error: {message}", Colors.RED), file=sys.stderr)

    def success(self, message: str):
        """Print success message."""
        if not self.quiet and not self.json_output:
            print(colored(f"Success: {message}", Colors.GREEN))


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        prog='dnsscience-api-util',
        description='DNSScience API Utility - Complete CLI for DNSScience.io & IPScience.io',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('-V', '--version', action='version', version=f'%(prog)s {__version__}')
    parser.add_argument('-j', '--json', action='store_true', help='Output in JSON format')
    parser.add_argument('-p', '--pretty', action='store_true', help='Pretty-print JSON output')
    parser.add_argument('--api-key', help='API key (overrides config)')
    parser.add_argument('-q', '--quiet', action='store_true', help='Suppress non-essential output')
    parser.add_argument('--no-color', action='store_true', help='Disable colored output')

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # ==========================================
    # Config commands
    # ==========================================
    config_parser = subparsers.add_parser('config', help='Configuration management')
    config_sub = config_parser.add_subparsers(dest='config_cmd')
    config_sub.add_parser('show', help='Show configuration')
    config_set = config_sub.add_parser('set', help='Set configuration')
    config_set.add_argument('key', choices=['api-key', 'api-url', 'ipscience-url'])
    config_set.add_argument('value')

    # Login
    login_parser = subparsers.add_parser('login', help='Authenticate with account')
    login_parser.add_argument('-e', '--email', help='Account email')
    login_parser.add_argument('-p', '--password', help='Account password')

    subparsers.add_parser('logout', help='Clear saved credentials')
    subparsers.add_parser('whoami', help='Show current user')

    # ==========================================
    # Domain commands
    # ==========================================
    scan_parser = subparsers.add_parser('scan', help='Scan a domain')
    scan_parser.add_argument('domain', help='Domain to scan')
    scan_parser.add_argument('--full', action='store_true', help='Full scan')

    domain_parser = subparsers.add_parser('domain', help='Get domain info')
    domain_parser.add_argument('domain', help='Domain name')
    domain_parser.add_argument('--history', action='store_true', help='Show scan history')
    domain_parser.add_argument('--timeline', action='store_true', help='Show timeline')
    domain_parser.add_argument('--profile', action='store_true', help='Complete profile')
    domain_parser.add_argument('--certificates', action='store_true', help='Show certificates')

    search_parser = subparsers.add_parser('search', help='Search domains')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument('-l', '--limit', type=int, default=50, help='Result limit')

    subparsers.add_parser('domains', help='List tracked domains')

    compare_parser = subparsers.add_parser('compare', help='Compare DNS across resolvers')
    compare_parser.add_argument('domain', help='Domain to compare')

    # ==========================================
    # DNS Tools
    # ==========================================
    prop_parser = subparsers.add_parser('propagation', help='Check DNS propagation')
    prop_parser.add_argument('domain', help='Domain to check')
    prop_parser.add_argument('-t', '--type', default='A', help='Record type')

    dnssec_parser = subparsers.add_parser('dnssec', help='Validate DNSSEC')
    dnssec_parser.add_argument('domain', help='Domain to validate')

    cert_parser = subparsers.add_parser('cert-chain', help='Get SSL certificate chain')
    cert_parser.add_argument('domain', help='Domain')

    subparsers.add_parser('certificates', help='List certificates')

    expiring_parser = subparsers.add_parser('expiring-certs', help='List expiring certificates')
    expiring_parser.add_argument('-d', '--days', type=int, default=30, help='Days threshold')

    # ==========================================
    # Enrichment
    # ==========================================
    enrich_parser = subparsers.add_parser('enrich', help='Domain enrichment')
    enrich_parser.add_argument('domain', help='Domain')

    rdap_parser = subparsers.add_parser('rdap', help='RDAP/WHOIS lookup')
    rdap_parser.add_argument('domain', help='Domain')

    web3_parser = subparsers.add_parser('web3', help='Web3 domain lookup')
    web3_parser.add_argument('--address', help='Wallet address')

    # ==========================================
    # Threats
    # ==========================================
    threats_parser = subparsers.add_parser('threats', help='List threat detections')
    threats_parser.add_argument('-d', '--domain', help='Filter by domain')

    threatintel_parser = subparsers.add_parser('threat-intel', help='Threat intelligence')
    threatintel_parser.add_argument('target', help='IP or domain')

    # ==========================================
    # IP commands
    # ==========================================
    ip_parser = subparsers.add_parser('ip', help='IP lookup')
    ip_parser.add_argument('ip', help='IP address')
    ip_parser.add_argument('--reputation', action='store_true', help='Show reputation')
    ip_parser.add_argument('--bgp', action='store_true', help='Show BGP info')
    ip_parser.add_argument('--profile', action='store_true', help='Complete profile')
    ip_parser.add_argument('--scan', action='store_true', help='Scan IP')
    ip_parser.add_argument('--ports', help='Ports to scan (comma-separated)')

    geoip_parser = subparsers.add_parser('geoip', help='GeoIP lookup')
    geoip_parser.add_argument('ip', nargs='?', help='IP address (omit for your IP)')

    reverse_parser = subparsers.add_parser('reverse-dns', help='Reverse DNS')
    reverse_parser.add_argument('ip', help='IP address')

    # ==========================================
    # ASN commands
    # ==========================================
    asn_parser = subparsers.add_parser('asn', help='ASN lookup')
    asn_parser.add_argument('asn', help='AS number')
    asn_parser.add_argument('--prefixes', action='store_true', help='Show prefixes')
    asn_parser.add_argument('--peers', action='store_true', help='Show peers')
    asn_parser.add_argument('--type', choices=['v4', 'v6'], help='IP version filter')

    # ==========================================
    # Network tools
    # ==========================================
    trace_parser = subparsers.add_parser('traceroute', help='Visual traceroute')
    trace_parser.add_argument('target', help='Target host')
    trace_parser.add_argument('--max-hops', type=int, default=30, help='Max hops')

    whois_parser = subparsers.add_parser('whois', help='WHOIS lookup')
    whois_parser.add_argument('target', help='Domain or IP')

    facilities_parser = subparsers.add_parser('facilities', help='Data center lookup')
    facilities_parser.add_argument('--ip', help='Find facilities for IP')

    # ==========================================
    # Account
    # ==========================================
    subparsers.add_parser('usage', help='Show API usage')
    subparsers.add_parser('subscription', help='Show subscription')
    subparsers.add_parser('invoices', help='List invoices')

    keys_parser = subparsers.add_parser('api-keys', help='Manage API keys')
    keys_sub = keys_parser.add_subparsers(dest='keys_cmd')
    keys_sub.add_parser('list', help='List API keys')
    keys_create = keys_sub.add_parser('create', help='Create API key')
    keys_create.add_argument('name', help='Key name')
    keys_delete = keys_sub.add_parser('delete', help='Delete API key')
    keys_delete.add_argument('key_id', help='Key ID')

    # ==========================================
    # Bulk operations
    # ==========================================
    bulk_ip_parser = subparsers.add_parser('bulk-ip', help='Bulk IP lookup')
    bulk_ip_parser.add_argument('ips', nargs='+', help='IP addresses')

    bulk_domain_parser = subparsers.add_parser('bulk-scan', help='Bulk domain scan')
    bulk_domain_parser.add_argument('domains', nargs='+', help='Domains')

    # ==========================================
    # Misc
    # ==========================================
    subparsers.add_parser('stats', help='Platform statistics')
    subparsers.add_parser('health', help='Health check')

    return parser


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if args.no_color:
        Colors.disable()

    formatter = OutputFormatter(
        json_output=args.json,
        pretty=args.pretty,
        quiet=args.quiet
    )

    api = DNSScienceAPI(api_key=args.api_key)
    config = Config()

    try:
        if not args.command:
            parser.print_help()
            sys.exit(0)

        # Config commands
        if args.command == 'config':
            if args.config_cmd == 'show':
                formatter.output({
                    'config_file': str(CONFIG_FILE),
                    'api_url': config.api_url,
                    'ipscience_url': config.ipscience_url,
                    'email': config.email,
                    'api_key': '***' + config.api_key[-8:] if config.api_key else None,
                    'authenticated': config.is_authenticated()
                }, 'Configuration')
            elif args.config_cmd == 'set':
                if args.key == 'api-key':
                    config.api_key = args.value
                elif args.key == 'api-url':
                    config.api_url = args.value
                elif args.key == 'ipscience-url':
                    config.ipscience_url = args.value
                config.save()
                formatter.success(f"Set {args.key}")

        elif args.command == 'login':
            email = args.email or input('Email: ')
            password = args.password
            if not password:
                import getpass
                password = getpass.getpass('Password: ')
            result = api.login(email, password)
            if 'api_key' in result:
                config.api_key = result['api_key']
                config.email = email
                config.save()
                formatter.success("Login successful! API key saved.")
            else:
                formatter.output(result, 'Login Result')

        elif args.command == 'logout':
            config.api_key = None
            config.email = None
            config.save()
            formatter.success("Logged out successfully.")

        elif args.command == 'whoami':
            result = api.get_me()
            formatter.output(result, 'Current User')

        # Domain commands
        elif args.command == 'scan':
            result = api.scan_domain(args.domain, full=args.full)
            formatter.output(result, f'Scan: {args.domain}')

        elif args.command == 'domain':
            if args.history:
                result = api.get_domain_history(args.domain)
            elif args.timeline:
                result = api.get_domain_timeline(args.domain)
            elif args.profile:
                result = api.get_domain_profile(args.domain)
            elif args.certificates:
                result = api.get_domain_certificates(args.domain)
            else:
                result = api.get_domain(args.domain)
            formatter.output(result, f'Domain: {args.domain}')

        elif args.command == 'search':
            result = api.search_domains(args.query, limit=args.limit)
            formatter.output(result, f'Search: {args.query}')

        elif args.command == 'domains':
            result = api.list_domains()
            formatter.output(result, 'Tracked Domains')

        elif args.command == 'compare':
            result = api.compare_domain(args.domain)
            formatter.output(result, f'DNS Comparison: {args.domain}')

        # DNS Tools
        elif args.command == 'propagation':
            result = api.dns_propagation(args.domain, args.type)
            formatter.output(result, f'Propagation: {args.domain}')

        elif args.command == 'dnssec':
            result = api.dnssec_validate(args.domain)
            formatter.output(result, f'DNSSEC: {args.domain}')

        elif args.command == 'cert-chain':
            result = api.get_cert_chain(args.domain)
            formatter.output(result, f'Certificate Chain: {args.domain}')

        elif args.command == 'certificates':
            result = api.list_certificates()
            formatter.output(result, 'Certificates')

        elif args.command == 'expiring-certs':
            result = api.get_expiring_certs(days=args.days)
            formatter.output(result, f'Expiring Certificates ({args.days} days)')

        # Enrichment
        elif args.command == 'enrich':
            result = api.enrich_domain(args.domain)
            formatter.output(result, f'Enrichment: {args.domain}')

        elif args.command == 'rdap':
            result = api.rdap_lookup(args.domain)
            formatter.output(result, f'RDAP: {args.domain}')

        elif args.command == 'web3':
            result = api.web3_domains(address=args.address)
            formatter.output(result, 'Web3 Domains')

        # Threats
        elif args.command == 'threats':
            result = api.list_threats(domain=args.domain)
            formatter.output(result, 'Threats')

        elif args.command == 'threat-intel':
            result = api.threat_intel(args.target)
            formatter.output(result, f'Threat Intel: {args.target}')

        # IP commands
        elif args.command == 'ip':
            if args.reputation:
                result = api.ip_reputation(args.ip)
            elif args.bgp:
                result = api.ip_bgp(args.ip)
            elif args.profile:
                result = api.ip_profile(args.ip)
            elif args.scan:
                result = api.ip_scan(args.ip, ports=args.ports)
            else:
                result = api.ip_lookup(args.ip)
            formatter.output(result, f'IP: {args.ip}')

        elif args.command == 'geoip':
            result = api.ip_geoip(args.ip)
            formatter.output(result, 'GeoIP')

        elif args.command == 'reverse-dns':
            result = api.reverse_dns(args.ip)
            formatter.output(result, f'Reverse DNS: {args.ip}')

        # ASN commands
        elif args.command == 'asn':
            if args.prefixes:
                result = api.asn_prefixes(args.asn, ip_type=args.type)
            elif args.peers:
                result = api.asn_peers(args.asn)
            else:
                result = api.asn_lookup(args.asn)
            formatter.output(result, f'ASN: {args.asn}')

        # Network tools
        elif args.command == 'traceroute':
            result = api.traceroute(args.target, max_hops=args.max_hops)
            formatter.output(result, f'Traceroute: {args.target}')

        elif args.command == 'whois':
            result = api.whois(args.target)
            formatter.output(result, f'WHOIS: {args.target}')

        elif args.command == 'facilities':
            result = api.facilities(ip=args.ip)
            formatter.output(result, 'Facilities')

        # Account
        elif args.command == 'usage':
            result = api.get_account_usage()
            formatter.output(result, 'API Usage')

        elif args.command == 'subscription':
            result = api.get_subscription()
            formatter.output(result, 'Subscription')

        elif args.command == 'invoices':
            result = api.get_invoices()
            formatter.output(result, 'Invoices')

        elif args.command == 'api-keys':
            if args.keys_cmd == 'list' or not args.keys_cmd:
                result = api.list_api_keys()
                formatter.output(result, 'API Keys')
            elif args.keys_cmd == 'create':
                result = api.create_api_key(args.name)
                formatter.output(result, 'New API Key')
            elif args.keys_cmd == 'delete':
                result = api.delete_api_key(args.key_id)
                formatter.success(f"Deleted API key {args.key_id}")

        # Bulk operations
        elif args.command == 'bulk-ip':
            result = api.bulk_ip_lookup(args.ips)
            formatter.output(result, 'Bulk IP Lookup')

        elif args.command == 'bulk-scan':
            result = api.bulk_domain_scan(args.domains)
            formatter.output(result, 'Bulk Domain Scan')

        # Misc
        elif args.command == 'stats':
            result = api.get_stats()
            formatter.output(result, 'Platform Statistics')

        elif args.command == 'health':
            result = api.health_check()
            formatter.output(result, 'Health Check')

        else:
            parser.print_help()

    except APIError as e:
        formatter.error(str(e))
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nAborted.")
        sys.exit(130)
    except Exception as e:
        formatter.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
