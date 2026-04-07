#!/usr/bin/env python3
"""
Guardian Sentinel Project Integrity Verification
Checks: Files, Ports, API Configuration, Frontend Connectivity
"""

import os
import sys
import json
from pathlib import Path

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{text:^60}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

def check_file(filepath, description):
    """Check if a file exists"""
    if os.path.isfile(filepath):
        size = os.path.getsize(filepath)
        print(f"{GREEN}✓{RESET} {description}: {filepath} ({size} bytes)")
        return True
    else:
        print(f"{RED}✗{RESET} {description}: {filepath} NOT FOUND")
        return False

def check_port_config(filepath, port, description):
    """Check if a file contains the expected port configuration"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            if str(port) in content:
                print(f"{GREEN}✓{RESET} {description}: Port {port} configured in {filepath}")
                return True
            else:
                print(f"{RED}✗{RESET} {description}: Port {port} NOT found in {filepath}")
                return False
    except Exception as e:
        print(f"{RED}✗{RESET} Error reading {filepath}: {e}")
        return False

def check_cors_config(filepath):
    """Check if CORS middleware is configured"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            cors_checks = {
                'CORSMiddleware import': 'CORSMiddleware' in content,
                'add_middleware': 'add_middleware' in content,
                'allow_origins': 'allow_origins' in content
            }
            
            all_present = all(cors_checks.values())
            for check, result in cors_checks.items():
                status = f"{GREEN}✓{RESET}" if result else f"{RED}✗{RESET}"
                print(f"{status} {check}: {'Present' if result else 'Missing'}")
            
            return all_present
    except Exception as e:
        print(f"{RED}✗{RESET} Error reading {filepath}: {e}")
        return False

def check_html_api_url(filepath, expected_url):
    """Check if HTML frontend has the correct API URL"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            if expected_url in content:
                print(f"{GREEN}✓{RESET} HTML Frontend: API URL configured as {expected_url}")
                return True
            else:
                print(f"{RED}✗{RESET} HTML Frontend: Expected API URL {expected_url} not found")
                return False
    except Exception as e:
        print(f"{RED}✗{RESET} Error reading {filepath}: {e}")
        return False

def main():
    print_header("Guardian Sentinel - Project Integrity Check")
    
    project_root = "."
    results = {
        'files': [],
        'ports': [],
        'cors': [],
        'connectivity': []
    }
    
    # 1. Check Core Files
    print(f"{YELLOW}1. Checking Core Project Files...{RESET}")
    files_to_check = [
        ("api.py", "Backend API"),
        ("data_pipeline.py", "Data Pipeline"),
        ("bilstm_model.h5", "Bi-LSTM Model"),
        ("tokenizer.pickle", "Keras Tokenizer"),
        ("future_scope/index.html", "HTML Frontend"),
        ("future_scope/frontend.py", "Streamlit Frontend"),
    ]
    
    for filepath, description in files_to_check:
        results['files'].append(check_file(filepath, description))
    
    # 2. Check Port Configuration
    print(f"\n{YELLOW}2. Checking Port Configuration...{RESET}")
    results['ports'].append(check_port_config("api.py", 8000, "Backend Port"))
    results['ports'].append(check_port_config("future_scope/index.html", 8000, "Frontend API Connection"))
    
    # 3. Check CORS Configuration
    print(f"\n{YELLOW}3. Checking CORS Middleware (Critical for HTML Frontend)...{RESET}")
    cors_ok = check_cors_config("api.py")
    results['cors'].append(cors_ok)
    
    # 4. Check Frontend-Backend Connectivity
    print(f"\n{YELLOW}4. Checking Frontend-Backend Connectivity...{RESET}")
    results['connectivity'].append(check_html_api_url(
        "future_scope/index.html", 
        'http://localhost:8000'
    ))
    
    # Summary
    print_header("Verification Summary")
    
    all_files_ok = all(results['files'])
    all_ports_ok = all(results['ports'])
    cors_ok = all(results['cors'])
    all_connectivity_ok = all(results['connectivity'])
    
    print(f"Files: {GREEN}✓ PASS{RESET if all_files_ok else f' {RED}(Some missing){RESET}'}")
    print(f"Ports: {GREEN}✓ PASS{RESET if all_ports_ok else f' {RED}(Config mismatch){RESET}'}")
    print(f"CORS:  {GREEN}✓ PASS{RESET if cors_ok else f' {RED}(Not configured){RESET}'}")
    print(f"API:   {GREEN}✓ PASS{RESET if all_connectivity_ok else f' {RED}(URL mismatch){RESET}'}")
    
    print(f"\n{YELLOW}How to Run:{RESET}")
    print("1. Start Backend API:")
    print(f'   {BLUE}cd "C:\\Users\\chiranjeevi madem\\Downloads\\code\\code"{RESET}')
    print(f'   {BLUE}uvicorn api:app --host 0.0.0.0 --port 8000{RESET}')
    print(f"\n2. Open HTML Frontend:")
    print(f'   {BLUE}Open in browser: file:///C:/Users/chiranjeevi%20madem/Downloads/code/code/future_scope/index.html{RESET}')
    print(f"   {YELLOW}(Or: http://localhost:8501 if launched via API startup){RESET}")
    
    print(f"\n{GREEN}Project Integrity: {'✓ ALL CHECKS PASSED' if all([all_files_ok, all_ports_ok, cors_ok, all_connectivity_ok]) else '✗ SOME CHECKS FAILED'}{RESET}\n")

if __name__ == "__main__":
    main()
