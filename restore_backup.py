#!/usr/bin/env python3
"""
Restore database from Cloud Storage backup
"""

import subprocess
import sys

BUCKET = 'secondbrain-app-20250612-article-data'

def list_backups():
    """List available backups"""
    print("🔍 Looking for backups in Cloud Storage...")
    result = subprocess.run(
        ['gcloud', 'storage', 'ls', f'gs://{BUCKET}/backup_*.db'],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0 and result.stdout:
        backups = result.stdout.strip().split('\n')
        print(f"\n📦 Found {len(backups)} backup(s):")
        for i, backup in enumerate(backups, 1):
            # Get size and date
            info_result = subprocess.run(
                ['gcloud', 'storage', 'ls', '--long', backup],
                capture_output=True,
                text=True
            )
            if info_result.stdout:
                parts = info_result.stdout.strip().split()
                size = int(parts[0]) / 1024  # Convert to KB
                date = parts[1]
                print(f"  {i}. {backup.split('/')[-1]} - {size:.1f} KB - {date}")
        return backups
    else:
        print("❌ No backups found")
        return []

def restore_backup(backup_url):
    """Restore a specific backup"""
    print(f"\n🔄 Restoring {backup_url}...")
    
    # Download backup
    local_file = '/tmp/restore.db'
    result = subprocess.run(
        ['gcloud', 'storage', 'cp', backup_url, local_file],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"❌ Failed to download: {result.stderr}")
        return False
    
    # Verify database
    import sqlite3
    try:
        conn = sqlite3.connect(local_file)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM articles")
        count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM users")
        users = cursor.fetchone()[0]
        conn.close()
        
        print(f"✅ Backup contains {count} articles and {users} users")
        
        # Restore to main database
        print("📤 Uploading as main database...")
        result = subprocess.run(
            ['gcloud', 'storage', 'cp', local_file, f'gs://{BUCKET}/articles.db'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Database restored successfully!")
            print("\n⚠️  IMPORTANT: Restart the Cloud Run service to load the restored database:")
            print(f"   gcloud run services update article-hub --region asia-northeast1")
            return True
        else:
            print(f"❌ Failed to upload: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Backup verification failed: {e}")
        return False

def main():
    backups = list_backups()
    
    if not backups:
        return
    
    if len(sys.argv) > 1:
        # Restore specific backup by number
        try:
            idx = int(sys.argv[1]) - 1
            if 0 <= idx < len(backups):
                restore_backup(backups[idx])
            else:
                print(f"❌ Invalid backup number: {sys.argv[1]}")
        except ValueError:
            print(f"❌ Invalid input: {sys.argv[1]}")
    else:
        print("\nUsage: python3 restore_backup.py [backup_number]")
        print("Example: python3 restore_backup.py 1")

if __name__ == "__main__":
    main()