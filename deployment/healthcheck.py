#!/usr/bin/env python3
"""
NEF Cadência - Health Check Script
Performs comprehensive health checks on the application
"""

import sys
import os
import subprocess
import socket
import time
from urllib.request import urlopen
from urllib.error import URLError

# Colors for terminal output
class Colors:
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

def print_header(text):
    print(f"\n{Colors.BLUE}{'='*60}{Colors.NC}")
    print(f"{Colors.BLUE}{text}{Colors.NC}")
    print(f"{Colors.BLUE}{'='*60}{Colors.NC}\n")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.NC}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.NC}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.NC}")

def check_service(service_name):
    """Check if a systemd service is running"""
    try:
        result = subprocess.run(
            ['systemctl', 'is-active', service_name],
            capture_output=True,
            text=True
        )
        return result.stdout.strip() == 'active'
    except Exception as e:
        print_error(f"Error checking {service_name}: {e}")
        return False

def check_port(host, port, service_name):
    """Check if a port is open"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        print_error(f"Error checking {service_name} port: {e}")
        return False

def check_http_endpoint(url, timeout=5):
    """Check if HTTP endpoint responds"""
    try:
        response = urlopen(url, timeout=timeout)
        return response.getcode() == 200
    except URLError as e:
        return False
    except Exception as e:
        print_error(f"Error checking HTTP endpoint: {e}")
        return False

def check_disk_space(path, threshold=90):
    """Check disk space usage"""
    try:
        stat = os.statvfs(path)
        total = stat.f_blocks * stat.f_frsize
        free = stat.f_bavail * stat.f_frsize
        used_percent = ((total - free) / total) * 100
        return used_percent < threshold, used_percent
    except Exception as e:
        print_error(f"Error checking disk space: {e}")
        return False, 0

def check_database_connection():
    """Check PostgreSQL database connection"""
    try:
        result = subprocess.run(
            ['sudo', '-u', 'postgres', 'psql', '-c', 'SELECT 1;'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception as e:
        print_error(f"Error checking database: {e}")
        return False

def main():
    print_header("NEF Cadência - Health Check")
    
    all_checks_passed = True
    
    # Check systemd services
    print_header("Service Status")
    
    services = {
        'nef-cadencia': 'Gunicorn (Application)',
        'nginx': 'Nginx (Web Server)',
        'postgresql': 'PostgreSQL (Database)',
        'redis-server': 'Redis (Cache)',
    }
    
    for service, description in services.items():
        if check_service(service):
            print_success(f"{description} is running")
        else:
            print_error(f"{description} is NOT running")
            all_checks_passed = False
    
    # Check ports
    print_header("Port Connectivity")
    
    ports = {
        ('127.0.0.1', 5432): 'PostgreSQL',
        ('127.0.0.1', 6379): 'Redis',
        ('127.0.0.1', 80): 'Nginx HTTP',
    }
    
    for (host, port), service in ports.items():
        if check_port(host, port, service):
            print_success(f"{service} port {port} is open")
        else:
            print_error(f"{service} port {port} is NOT accessible")
            all_checks_passed = False
    
    # Check HTTP endpoints
    print_header("HTTP Endpoints")
    
    endpoints = {
        'http://localhost/health/': 'Health Check',
        'http://localhost/admin/': 'Admin Panel',
    }
    
    for url, description in endpoints.items():
        if check_http_endpoint(url):
            print_success(f"{description} is responding")
        else:
            print_warning(f"{description} is not responding (may not exist)")
    
    # Check disk space
    print_header("Disk Space")
    
    paths = {
        '/': 'Root',
        '/opt/nef-cadencia': 'Application',
        '/var/log': 'Logs',
    }
    
    for path, description in paths.items():
        if os.path.exists(path):
            ok, usage = check_disk_space(path)
            if ok:
                print_success(f"{description}: {usage:.1f}% used")
            else:
                print_error(f"{description}: {usage:.1f}% used (threshold exceeded)")
                all_checks_passed = False
        else:
            print_warning(f"{description} path does not exist")
    
    # Check database connection
    print_header("Database Connection")
    
    if check_database_connection():
        print_success("PostgreSQL connection successful")
    else:
        print_error("PostgreSQL connection failed")
        all_checks_passed = False
    
    # Check application logs for errors
    print_header("Recent Errors")
    
    try:
        result = subprocess.run(
            ['journalctl', '-u', 'nef-cadencia', '-p', 'err', '-n', '5', '--no-pager'],
            capture_output=True,
            text=True
        )
        
        if result.stdout.strip():
            print_warning("Recent errors found in application logs:")
            print(result.stdout)
        else:
            print_success("No recent errors in application logs")
    except Exception as e:
        print_warning(f"Could not check logs: {e}")
    
    # Summary
    print_header("Summary")
    
    if all_checks_passed:
        print_success("All critical checks passed!")
        return 0
    else:
        print_error("Some checks failed. Please review the output above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
