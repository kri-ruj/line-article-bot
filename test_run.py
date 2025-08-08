#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test if apps can run"""

import sys
import os

def test_import(module_name):
    """Test if a module can be imported"""
    try:
        __import__(module_name.replace('.py', ''))
        return True, "OK"
    except Exception as e:
        return False, str(e)

def main():
    print("="*50)
    print("Testing LINE Article Bot Apps")
    print("="*50)
    
    apps = [
        ('app_ultimate.py', 'Ultimate App (No Dependencies)'),
        ('app_line_fixed.py', 'LINE Bot'),
        ('app_production.py', 'Production App'),
        ('simple_10x_demo.py', 'AI Demo')
    ]
    
    print("\nChecking Python version...")
    print(f"Python: {sys.version}")
    
    print("\nTesting imports...")
    for app_file, description in apps:
        if os.path.exists(app_file):
            success, msg = test_import(app_file)
            status = "PASS" if success else f"FAIL: {msg[:50]}"
            print(f"  {app_file:25} {description:30} [{status}]")
        else:
            print(f"  {app_file:25} {description:30} [FILE NOT FOUND]")
    
    print("\n" + "="*50)
    print("\nTo run an app:")
    print("  Option 1: Use run.bat")
    print("  Option 2: python app_ultimate.py")
    print("  Option 3: python app_line_fixed.py (needs .env)")
    print("  Option 4: python app_production.py (needs .env)")

if __name__ == "__main__":
    main()