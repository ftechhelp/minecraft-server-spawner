"""
Backup scheduler for handling automatic daily backups for spawns
"""
import threading
import time
from datetime import datetime, time as dt_time
from zoneinfo import ZoneInfo
from typing import Callable


class BackupScheduler:
    """Background scheduler for automated spawn backups"""
    
    def __init__(self):
        self.running = False
        self.thread = None
        self.spawner = None
        self.check_interval = 60  # Check every minute if a backup is due
        self.tz = ZoneInfo("America/Vancouver")
    
    def start(self, spawner):
        """Start the scheduler with reference to spawner"""
        if self.running:
            return
        
        self.spawner = spawner
        self.running = True
        self.thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.thread.start()
        print("[BackupScheduler] Scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("[BackupScheduler] Scheduler stopped")
    
    def _scheduler_loop(self):
        """Main scheduler loop - runs every check_interval seconds"""
        last_check_time = None
        
        while self.running:
            try:
                now = datetime.now(tz=self.tz)
                current_time = now.time()
                
                # Check every minute, at least once per hour
                # Store the hour+minute to only run the check once per minute
                current_hour_minute = (now.hour, now.minute)
                
                if last_check_time != current_hour_minute:
                    self._check_and_run_backups(now)
                    last_check_time = current_hour_minute
                
                time.sleep(self.check_interval)
            
            except Exception as e:
                print(f"[BackupScheduler] Error in scheduler loop: {str(e)}")
                import traceback
                traceback.print_exc()
                time.sleep(self.check_interval)
    
    def _check_and_run_backups(self, now: datetime):
        """Check all spawns for scheduled backups and run if due"""
        try:
            if not self.spawner or not self.spawner.spawns:
                return
            
            print(f"[BackupScheduler] Checking backups at {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            
            for spawn_name, spawn in self.spawner.spawns.items():
                try:
                    # Check if daily backups are enabled
                    if not spawn.backup_settings.get('daily_backup_enabled', False):
                        print(f"[BackupScheduler] {spawn_name}: Daily backups disabled")
                        continue
                    
                    # Get scheduled time
                    scheduled_hour = spawn.backup_settings.get('daily_backup_hour', 2)
                    scheduled_minute = spawn.backup_settings.get('daily_backup_minute', 0)
                    scheduled_time = dt_time(scheduled_hour, scheduled_minute)
                    
                    # Check if current time is within backup window (±5 minutes)
                    current_time = now.time()
                    window_start = dt_time(scheduled_hour, max(0, scheduled_minute - 5))
                    window_end = dt_time(scheduled_hour, min(59, scheduled_minute + 5))
                    
                    print(f"[BackupScheduler] {spawn_name}: Current time {current_time}, Window {window_start}-{window_end}, Scheduled {scheduled_time}")
                    
                    if window_start <= current_time <= window_end:
                        # Check if last backup was today
                        last_backup_ts = spawn.backup_settings.get('last_backup_timestamp')
                        if last_backup_ts:
                            try:
                                # Parse timestamp in format 'YYYY-MM-DD HH:MM:SS'
                                last_backup_dt = datetime.strptime(last_backup_ts, '%Y-%m-%d %H:%M:%S').date()
                                if last_backup_dt == now.date():
                                    # Already backed up today
                                    print(f"[BackupScheduler] {spawn_name}: Already backed up today at {last_backup_ts}")
                                    continue
                            except ValueError as ve:
                                # If parsing fails, proceed with backup
                                print(f"[BackupScheduler] {spawn_name}: Could not parse timestamp '{last_backup_ts}': {ve}")
                        
                        # Run backup
                        print(f"[BackupScheduler] Running scheduled backup for {spawn_name}")
                        success, message, backup_file = spawn.create_backup()
                        if success:
                            print(f"[BackupScheduler] ✓ Backup created for {spawn_name}: {backup_file}")
                        else:
                            print(f"[BackupScheduler] ✗ Failed to backup {spawn_name}: {message}")
                    else:
                        print(f"[BackupScheduler] {spawn_name}: Not in backup window")
                
                except Exception as e:
                    print(f"[BackupScheduler] Error backing up {spawn_name}: {str(e)}")
                    import traceback
                    traceback.print_exc()
        
        except Exception as e:
            print(f"[BackupScheduler] Error in _check_and_run_backups: {str(e)}")
            import traceback
            traceback.print_exc()


# Global scheduler instance
backup_scheduler = BackupScheduler()
