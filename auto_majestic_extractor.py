#!/usr/bin/env python3
"""
Auto-Recovering Majestic Million Extractor
Runs indefinitely with automatic Docker restart when failures occur
"""

import subprocess
import time
import json
import sys
import os
from pathlib import Path
from datetime import datetime

class AutoExtractor:
    def __init__(self):
        self.progress_file = "extraction_progress_million.json"
        self.max_consecutive_failures = 50  # Restart Docker after 50 failures in a row
        self.check_interval = 300  # Check progress every 5 minutes
        
    def check_docker_running(self):
        """Check if Docker Selenium is running"""
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", "ancestor=selenium/standalone-edge:latest", "--format", "{{.ID}}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return bool(result.stdout.strip())
        except Exception as e:
            print(f"⚠️ Error checking Docker: {e}")
            return False
    
    def start_docker(self):
        """Start Docker Selenium Edge"""
        print("🔄 Starting Docker Selenium Edge...")
        
        # Stop any existing containers
        try:
            subprocess.run(
                ["docker", "stop", "$(docker ps -q)"],
                shell=True,
                capture_output=True,
                timeout=30
            )
            time.sleep(2)
        except:
            pass
        
        # Start new container
        try:
            result = subprocess.run(
                [
                    "docker", "run", "-d",
                    "-p", "4444:4444",
                    "-p", "7900:7900",
                    "--shm-size=4g",
                    "-e", "SE_SESSION_REQUEST_TIMEOUT=300",
                    "-e", "SE_NODE_MAX_SESSIONS=5",
                    "selenium/standalone-edge:latest"
                ],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                container_id = result.stdout.strip()[:12]
                print(f"✅ Docker Selenium started: {container_id}")
                time.sleep(15)  # Wait for container to be ready
                return True
            else:
                print(f"❌ Failed to start Docker: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Error starting Docker: {e}")
            return False
    
    def get_progress(self):
        """Read current progress"""
        if Path(self.progress_file).exists():
            try:
                with open(self.progress_file, 'r') as f:
                    return json.load(f)
            except:
                return None
        return None
    
    def run_extraction(self):
        """Run extraction script as subprocess"""
        print("🚀 Starting extraction...")
        
        try:
            process = subprocess.Popen(
                [sys.executable, "majestic_joel_extractor.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            last_progress_check = time.time()
            last_progress = self.get_progress()
            consecutive_errors = 0
            
            # Monitor the process
            while True:
                # Check if process is still running
                if process.poll() is not None:
                    print("⚠️ Extraction process ended")
                    break
                
                # Read output line by line
                try:
                    line = process.stdout.readline()
                    if line:
                        print(line.rstrip())
                        
                        # Count consecutive errors
                        if "Connection aborted" in line or "RemoteDisconnected" in line:
                            consecutive_errors += 1
                        elif "✅" in line or "Checkpoint saved" in line:
                            consecutive_errors = 0
                        
                        # If too many consecutive errors, restart Docker
                        if consecutive_errors >= self.max_consecutive_failures:
                            print(f"🚨 {consecutive_errors} consecutive failures detected!")
                            print("💀 Docker Selenium appears dead - restarting...")
                            process.terminate()
                            time.sleep(5)
                            process.kill()
                            return "RESTART_DOCKER"
                except:
                    pass
                
                # Periodic progress check
                current_time = time.time()
                if current_time - last_progress_check > self.check_interval:
                    current_progress = self.get_progress()
                    
                    if current_progress and last_progress:
                        # Check if stuck
                        if current_progress.get('last_processed_index') == last_progress.get('last_processed_index'):
                            print("⚠️ No progress in 5 minutes - may be stuck")
                            # Let it continue for now
                        else:
                            print(f"✅ Progress: {current_progress.get('last_processed_index', 0):,} URLs")
                    
                    last_progress = current_progress
                    last_progress_check = current_time
                
                time.sleep(0.1)
            
            return "COMPLETED"
            
        except KeyboardInterrupt:
            print("\n⚠️ Ctrl+C detected - stopping extraction gracefully...")
            try:
                process.terminate()
                time.sleep(5)
                if process.poll() is None:
                    process.kill()
            except:
                pass
            return "INTERRUPTED"
        
        except Exception as e:
            print(f"❌ Error running extraction: {e}")
            return "ERROR"
    
    def run_forever(self):
        """Main loop - runs until all URLs are processed"""
        print("=" * 70)
        print("🤖 AUTO-RECOVERING MAJESTIC MILLION EXTRACTOR")
        print("=" * 70)
        print("This will run indefinitely until all 1,000,000 URLs are extracted")
        print("Safe to leave running overnight - auto-restarts on failures")
        print("Press Ctrl+C to stop gracefully")
        print("=" * 70)
        
        restart_count = 0
        
        while True:
            # Check if extraction is complete
            progress = self.get_progress()
            if progress and progress.get('last_processed_index', 0) >= 999999:
                print("=" * 70)
                print("🎉 EXTRACTION COMPLETE!")
                print(f"✅ All 1,000,000 URLs processed!")
                print(f"✅ Successful: {progress.get('successful', 0):,}")
                print(f"❌ Failed: {progress.get('failed', 0):,}")
                print("=" * 70)
                break
            
            # Ensure Docker is running
            if not self.check_docker_running():
                print("⚠️ Docker Selenium not running")
                if not self.start_docker():
                    print("❌ Could not start Docker - waiting 60s before retry...")
                    time.sleep(60)
                    continue
            
            # Run extraction
            restart_count += 1
            print(f"\n{'=' * 70}")
            print(f"🔄 Extraction Run #{restart_count}")
            if progress:
                print(f"📍 Resuming from URL #{progress.get('last_processed_index', 0) + 1:,}")
                print(f"✅ Successful so far: {progress.get('successful', 0):,}")
                print(f"❌ Failed so far: {progress.get('failed', 0):,}")
            print(f"{'=' * 70}\n")
            
            result = self.run_extraction()
            
            if result == "INTERRUPTED":
                print("\n👋 Extraction stopped by user")
                break
            elif result == "COMPLETED":
                print("\n✅ Extraction script completed normally")
                # Check if truly done
                time.sleep(5)
                continue
            elif result == "RESTART_DOCKER":
                print("\n🔄 Restarting Docker and resuming...")
                if not self.start_docker():
                    print("❌ Could not restart Docker - waiting 60s...")
                    time.sleep(60)
                continue
            else:
                print("\n⚠️ Extraction ended - restarting in 30 seconds...")
                time.sleep(30)
                continue
        
        print("\n" + "=" * 70)
        print("🏁 Auto-extractor finished")
        print("=" * 70)

if __name__ == "__main__":
    extractor = AutoExtractor()
    extractor.run_forever()
