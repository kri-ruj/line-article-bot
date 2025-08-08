#!/usr/bin/env python3
"""
Force deployment of the fixed application
"""

import subprocess
import time
import sys

def run_command(cmd, timeout=300):
    """Run command with timeout"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"

def main():
    print("=== Force Deployment Script ===\n")
    
    # Step 1: Verify fixes are in place
    print("1. Verifying fixes in app_firestore_final.py...")
    with open('app_firestore_final.py', 'r') as f:
        content = f.read()
    
    fixes_found = []
    if 'Found existing session in localStorage' in content:
        fixes_found.append("✓ localStorage persistence")
    if 'Continuing with stored session despite LIFF error' in content:
        fixes_found.append("✓ Session recovery")
    if 'encodeURIComponent(userId)' in content:
        fixes_found.append("✓ URL encoding for APIs")
    
    if len(fixes_found) < 3:
        print("❌ Not all fixes found in the file!")
        sys.exit(1)
    
    for fix in fixes_found:
        print(f"  {fix}")
    
    # Step 2: Cancel any running deployments
    print("\n2. Checking for running deployments...")
    success, stdout, stderr = run_command("gcloud builds list --ongoing --limit=1 --format='value(ID)'", 10)
    if success and stdout.strip():
        build_id = stdout.strip()
        print(f"  Found ongoing build: {build_id}")
        print("  Cancelling...")
        run_command(f"gcloud builds cancel {build_id}", 10)
        time.sleep(5)
    else:
        print("  No ongoing builds found")
    
    # Step 3: Deploy with explicit configuration
    print("\n3. Starting deployment...")
    deploy_cmd = """
    gcloud run deploy article-hub \
        --source . \
        --region asia-northeast1 \
        --platform managed \
        --allow-unauthenticated \
        --memory 512Mi \
        --timeout 60 \
        --max-instances 10 \
        --min-instances 0 \
        --port 8080 \
        --set-env-vars="GOOGLE_APPLICATION_CREDENTIALS=/app/service-account.json" \
        --no-use-http2 \
        --async \
        --format=json
    """
    
    print("  Submitting deployment...")
    success, stdout, stderr = run_command(deploy_cmd.strip(), 30)
    
    if success:
        print("  ✓ Deployment submitted successfully")
    else:
        print(f"  ✗ Deployment submission failed: {stderr}")
        
    # Step 4: Monitor deployment
    print("\n4. Monitoring deployment...")
    print("  This may take 3-5 minutes...")
    
    for i in range(30):  # Check for 5 minutes
        time.sleep(10)
        success, stdout, stderr = run_command(
            "gcloud run services describe article-hub --region asia-northeast1 --format='value(status.conditions[0].status)'", 
            10
        )
        if success and stdout.strip() == "True":
            print("\n  ✓ Deployment completed successfully!")
            break
        print(".", end="", flush=True)
    
    # Step 5: Verify deployment
    print("\n\n5. Verifying deployment...")
    success, stdout, stderr = run_command(
        "gcloud run services describe article-hub --region asia-northeast1 --format='value(status.url)'",
        10
    )
    
    if success and stdout.strip():
        service_url = stdout.strip()
        print(f"  Service URL: {service_url}")
        
        # Test if fixes are live
        print("\n6. Testing if fixes are deployed...")
        test_cmd = f"curl -s '{service_url}' | grep -q \"localStorage.setItem('lineUserId'\""
        success, _, _ = run_command(test_cmd, 30)
        
        if success:
            print("  ✓ Fixes are LIVE!")
            print(f"\n✅ Deployment successful!")
            print(f"   Main App: {service_url}")
            print(f"   LIFF URL: https://liff.line.me/2007870100-ao8GpgRQ")
        else:
            print("  ⚠️ Fixes may not be deployed yet. Check manually.")
    else:
        print("  Could not get service URL")
    
    print("\n=== Deployment Script Complete ===")

if __name__ == "__main__":
    main()