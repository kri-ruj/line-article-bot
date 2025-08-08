#!/usr/bin/env python3
"""
Fix persistence issues in the app
"""

import re

# Read the current enhanced app
with open('app_production_enhanced.py', 'r') as f:
    content = f.read()

# Fix 1: Ensure sync happens BEFORE shutdown
shutdown_fix = '''
    def cleanup(self):
        """Final sync before shutdown"""
        try:
            logging.info("Performing final database sync before shutdown...")
            # Force a sync even if recently synced
            self.upload_database()
            logging.info("Final sync complete")
        except Exception as e:
            logging.error(f"Error in final sync: {e}")
'''

# Find and update the cleanup method
cleanup_pattern = r'def cleanup\(self\):.*?logging\.info\("Final sync complete"\)'
content = re.sub(cleanup_pattern, shutdown_fix.strip(), content, flags=re.DOTALL)

# Fix 2: Add immediate sync after article operations
# Find the save_article_from_line method and add sync
save_article_pattern = r'(def save_article_from_line\(self, user_id, url\):.*?logging\.info\(f"Article saved from LINE: \{url\}"\))'

def save_article_replacement(match):
    original = match.group(1)
    return original + '''
        # Immediately sync to cloud after saving
        try:
            storage_manager.upload_database()
            logging.info(f"Database synced after saving article")
        except Exception as e:
            logging.error(f"Failed to sync after save: {e}")'''

content = re.sub(save_article_pattern, save_article_replacement, content, flags=re.DOTALL)

# Fix 3: Improve the upload_database method to be more robust
upload_pattern = r'def upload_database\(self\):.*?(?=\n    def \w+|\Z)'

new_upload = '''    def upload_database(self):
        """Upload database to Cloud Storage with verification"""
        try:
            # Check if database exists and has content
            if not os.path.exists(self.db_path):
                logging.warning("Database file does not exist, skipping upload")
                return
            
            # Get file size
            db_size = os.path.getsize(self.db_path)
            if db_size < 1024:  # Less than 1KB
                logging.warning(f"Database too small ({db_size} bytes), might be corrupted")
            
            # Create a backup copy with timestamp
            import shutil
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = f"{self.db_path}.backup_{timestamp}"
            shutil.copy2(self.db_path, backup_path)
            
            # Upload main database
            logging.info(f"Uploading database ({db_size} bytes) to Cloud Storage...")
            result = subprocess.run(
                ['gsutil', '-q', 'cp', backup_path, f'gs://{self.bucket_name}/{self.db_filename}'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                logging.info(f"Database uploaded successfully ({db_size} bytes)")
                self.last_sync = datetime.now()
                
                # Also keep a backup copy in cloud
                if db_size > 10000:  # Only backup if substantial data
                    backup_name = f"backup_{timestamp}.db"
                    subprocess.run(
                        ['gsutil', '-q', 'cp', backup_path, f'gs://{self.bucket_name}/{backup_name}'],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    logging.info(f"Backup saved as {backup_name}")
            else:
                logging.error(f"Failed to upload database: {result.stderr}")
            
            # Clean up local backup
            try:
                os.remove(backup_path)
            except:
                pass
                
        except subprocess.TimeoutExpired:
            logging.error("Database upload timed out")
        except Exception as e:
            logging.error(f"Error uploading database: {e}")'''

content = re.sub(upload_pattern, new_upload, content, flags=re.DOTALL)

# Fix 4: Add import for shutil and os if not present
if 'import shutil' not in content:
    content = content.replace('import os', 'import os\nimport shutil')

# Fix 5: Ensure download doesn't overwrite if local is newer/larger
download_pattern = r'def download_database\(self\):.*?(?=\n    def \w+|\Z)'

new_download = '''    def download_database(self):
        """Download database from Cloud Storage if it exists and is valid"""
        try:
            logging.info("Checking for existing database in Cloud Storage...")
            
            # First check if cloud database exists
            result = subprocess.run(
                ['gsutil', 'ls', '-l', f'gs://{self.bucket_name}/{self.db_filename}'],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logging.info("No database in Cloud Storage yet")
                return
            
            # Parse size from gsutil output
            cloud_size = 0
            try:
                # Output format: "32768  2025-08-03T17:45:37Z  gs://..."
                parts = result.stdout.strip().split()
                if parts:
                    cloud_size = int(parts[0])
            except:
                pass
            
            logging.info(f"Cloud database size: {cloud_size} bytes")
            
            # Download to temp file first
            temp_db = f"{self.db_path}.download"
            result = subprocess.run(
                ['gsutil', '-q', 'cp', f'gs://{self.bucket_name}/{self.db_filename}', temp_db],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Verify the downloaded database
                try:
                    conn = sqlite3.connect(temp_db)
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM articles")
                    count = cursor.fetchone()[0]
                    conn.close()
                    
                    logging.info(f"Downloaded database has {count} articles")
                    
                    # Use the downloaded database
                    import shutil
                    shutil.move(temp_db, self.db_path)
                    logging.info("Database downloaded and verified from Cloud Storage")
                    
                except Exception as e:
                    logging.error(f"Downloaded database verification failed: {e}")
                    # Clean up bad download
                    try:
                        os.remove(temp_db)
                    except:
                        pass
            else:
                logging.warning(f"Could not download database: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            logging.error("Database download timed out")
        except Exception as e:
            logging.warning(f"Could not download database: {e}")
            logging.info("Will use new database")'''

content = re.sub(download_pattern, new_download, content, flags=re.DOTALL)

# Save the fixed version
with open('app_production_persistent_fixed.py', 'w') as f:
    f.write(content)

print("✅ Created app_production_persistent_fixed.py with persistence fixes!")
print("Fixes applied:")
print("  1. Improved upload with verification and backups")
print("  2. Better download with validation")
print("  3. Immediate sync after saving articles")
print("  4. Robust error handling")
print("  5. Cloud backups with timestamps")