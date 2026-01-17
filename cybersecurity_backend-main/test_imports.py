"""Test script to verify workflow files are using correct field names"""
import sys
sys.path.insert(0, '.')

# Import the functions
from workflow.passive_recon import certificate_transparency_check, shodan_lookup
from workflow.web_scanning import run_nikto, run_gobuster
from workflow.openvas_integration import run_openvas_scan

# Check the source code
import inspect

print("=== Checking passive_recon.py ===")
ct_source = inspect.getsource(certificate_transparency_check)
if '"certificates"' in ct_source:
    print("✓ certificate_transparency_check uses 'certificates' (CORRECT)")
else:
    print("✗ certificate_transparency_check uses 'certificate_transparency' (OLD)")

shodan_source = inspect.getsource(shodan_lookup)
if '"threat_intel"' in shodan_source:
    print("✓ shodan_lookup uses 'threat_intel' (CORRECT)")
else:
    print("✗ shodan_lookup uses 'threat_intelligence' (OLD)")

print("\n=== Checking web_scanning.py ===")
nikto_source = inspect.getsource(run_nikto)
if '"nikto"' in nikto_source and '"nikto_findings"' not in nikto_source.replace('nikto_findings = []', ''):
    print("✓ run_nikto uses 'nikto' (CORRECT)")
else:
    print("✗ run_nikto uses 'nikto_findings' (OLD)")

gobuster_source = inspect.getsource(run_gobuster)
if '"gobuster"' in gobuster_source and '"gobuster_paths"' not in gobuster_source.replace('gobuster_paths = ', ''):
    print("✓ run_gobuster uses 'gobuster' (CORRECT)")
else:
    print("✗ run_gobuster uses 'gobuster_paths' (OLD)")

print("\n=== Checking openvas_integration.py ===")
openvas_source = inspect.getsource(run_openvas_scan)
if '"openvas"' in openvas_source:
    print("✓ run_openvas_scan uses 'openvas' (CORRECT)")
else:
    print("✗ run_openvas_scan uses 'openvas_findings' (OLD)")

print("\n=== CONCLUSION ===")
print("If all checks show CORRECT, the backend needs to be restarted!")
print("If any show OLD, there's a code issue that needs fixing.")
