# api/backup.py - Backup and Restore System
from flask import current_app
from datetime import datetime, timezone
import os
import tempfile
import shutil
import json
import sqlite3
import glob
import logging
from zipfile import ZipFile

from models import db, Setting, Admin

# Configure logging
logger = logging.getLogger(__name__)

# Backup zips hold the full database (Stripe/SMTP secrets, customer data), so they must never
# live under static/ — anything there is downloadable by anyone. They sit beside the DB instead
# and are only served through the admin-guarded /download-backup/<filename> route.
BACKUP_DIR = os.path.join('instance', 'backups')
LEGACY_BACKUP_DIR = os.path.join('static', 'backups')


def migrate_legacy_backups():
    """Move any zips left in the old public static/backups/ folder into BACKUP_DIR."""
    if not os.path.isdir(LEGACY_BACKUP_DIR):
        return
    os.makedirs(BACKUP_DIR, exist_ok=True)
    for name in os.listdir(LEGACY_BACKUP_DIR):
        if name.endswith('.zip'):
            shutil.move(os.path.join(LEGACY_BACKUP_DIR, name), os.path.join(BACKUP_DIR, name))


def resolve_db_path():
    """Absolute path of the live SQLite file, taken from the app's own DB config.

    The old `config.get('DATABASE_PATH', 'instance/minipass.db')` default is
    relative to the process CWD and DATABASE_PATH is never set anywhere, so a
    backup or restore run from any other directory silently read/wrote the
    wrong file.
    """
    configured = current_app.config.get('DATABASE_PATH')
    if configured:
        return os.path.abspath(configured)

    uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if uri.startswith('sqlite:///'):
        path = uri[len('sqlite:///'):]
        if not os.path.isabs(path):
            path = os.path.join(current_app.root_path, path)
        return os.path.abspath(path)

    return os.path.abspath(os.path.join(current_app.root_path, 'instance', 'minipass.db'))


def snapshot_database(destination_path):
    """Write a consistent copy of the live database to destination_path.

    The database runs in WAL mode, where a commit lands in the `-wal` sidecar
    and only later gets folded into the main `.db`. Copying the `.db` alone —
    which is what this module used to do — therefore captures a snapshot that
    is missing every recent commit, so freshly created activities, signups and
    passports were absent from the backup they were supposed to be in.

    sqlite3's own backup API reads through the WAL and produces a single
    self-contained file, and it is safe to run while the app is serving.
    """
    source = sqlite3.connect(resolve_db_path())
    try:
        dest = sqlite3.connect(destination_path)
        try:
            source.backup(dest)
        finally:
            dest.close()
    finally:
        source.close()

# ============================================================================
# BACKUP OPERATIONS
# ============================================================================

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def export_settings():
    """Export all settings to a dictionary"""
    settings = {}
    for setting in Setting.query.all():
        settings[setting.key] = setting.value
    
    # Add admin accounts (without passwords)
    admins = []
    for admin in Admin.query.all():
        admins.append({'email': admin.email})
    settings['_ADMINS'] = admins
    
    return settings

def restore_database(temp_dir):
    """Restore database from backup"""
    db_backup_path = os.path.join(temp_dir, 'database', 'minipass.db')
    if not os.path.exists(db_backup_path):
        return
    
    db_path = resolve_db_path()

    # Create backup of current database
    if os.path.exists(db_path):
        backup_current_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(db_path, backup_current_path)

    # Drop every pooled connection before the file is swapped. SQLAlchemy keeps
    # SQLite handles open, and a handle held across the copy still owns the old
    # WAL and its page cache — writes through it land on top of the file we just
    # restored and undo it.
    db.session.remove()
    db.engine.dispose()

    shutil.copy2(db_backup_path, db_path)

    # The -wal/-shm sidecars still describe the PREVIOUS database. Left in place,
    # SQLite replays that stale WAL over the restored file on the next open and
    # silently reverts the restore — which is why restoring appeared to do
    # nothing at all. The snapshot in the backup is self-contained, so dropping
    # them is safe.
    for sidecar in (f"{db_path}-wal", f"{db_path}-shm"):
        if os.path.exists(sidecar):
            os.remove(sidecar)

    # The restored snapshot's cart_order/signup/shop_order tables have whatever
    # sqlite_sequence high-water mark they had when the backup was taken — lower than what
    # may have been issued since, on either this environment or wherever the backup came
    # from. Push it back up to the persisted watermark (a sibling file this function never
    # touches) so the next checkout/signup can't reissue an already-used reference code.
    from utils import enforce_watermarks
    enforce_watermarks()

def restore_uploads(temp_dir):
    """Restore uploaded files from backup - handles busy directories"""
    # Try new backup structure first (static/uploads in zip)
    upload_backup_dir = os.path.join(temp_dir, 'static', 'uploads')
    if not os.path.exists(upload_backup_dir):
        # Try old backup structure (uploads directly in temp_dir)
        upload_backup_dir = os.path.join(temp_dir, 'uploads')
    if not os.path.exists(upload_backup_dir):
        return

    upload_dir = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')

    # Instead of moving the directory (which fails when busy),
    # clear contents and copy new files
    if os.path.exists(upload_dir):
        # Remove contents but keep the directory itself
        for item in os.listdir(upload_dir):
            item_path = os.path.join(upload_dir, item)
            try:
                if os.path.isfile(item_path):
                    os.remove(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
            except OSError as e:
                logger.warning(f"[RESTORE] Could not remove {item_path}: {e}")
    else:
        os.makedirs(upload_dir)

    # Copy new files into the existing directory
    for item in os.listdir(upload_backup_dir):
        src = os.path.join(upload_backup_dir, item)
        dst = os.path.join(upload_dir, item)
        try:
            if os.path.isfile(src):
                shutil.copy2(src, dst)
            elif os.path.isdir(src):
                shutil.copytree(src, dst)
        except Exception as e:
            logger.warning(f"[RESTORE] Could not copy {src} to {dst}: {e}")

def restore_templates(temp_dir):
    """Restore email templates from backup - handles busy directories"""
    # Try new backup structure first (templates/email_templates in zip)
    template_backup_dir = os.path.join(temp_dir, 'templates', 'email_templates')
    if not os.path.exists(template_backup_dir):
        # Try old backup structure (email_templates directly in temp_dir)
        template_backup_dir = os.path.join(temp_dir, 'email_templates')
    if not os.path.exists(template_backup_dir):
        return

    template_dir = 'templates/email_templates'

    # Instead of moving the directory (which fails when busy),
    # clear contents and copy new files
    if os.path.exists(template_dir):
        # Remove contents but keep the directory itself
        for item in os.listdir(template_dir):
            item_path = os.path.join(template_dir, item)
            try:
                if os.path.isfile(item_path):
                    os.remove(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
            except OSError as e:
                logger.warning(f"[RESTORE] Could not remove {item_path}: {e}")
    else:
        os.makedirs(template_dir)

    # Copy new files into the existing directory
    for item in os.listdir(template_backup_dir):
        src = os.path.join(template_backup_dir, item)
        dst = os.path.join(template_dir, item)
        try:
            if os.path.isfile(src):
                shutil.copy2(src, dst)
            elif os.path.isdir(src):
                shutil.copytree(src, dst)
        except Exception as e:
            logger.warning(f"[RESTORE] Could not copy {src} to {dst}: {e}")

def cleanup_old_restore_points(keep_count=3):
    """
    Delete old restore point ZIP files, keeping only the most recent ones.

    Args:
        keep_count (int): Number of most recent restore points to keep
    """
    logger.info(f"[CLEANUP] Starting cleanup_old_restore_points(keep_count={keep_count})")

    backup_dir = BACKUP_DIR
    if not os.path.exists(backup_dir):
        logger.warning(f"[CLEANUP] Backup directory does not exist: {backup_dir}")
        return

    # Get all restore point ZIP files with timestamp pattern
    pattern = os.path.join(backup_dir, 'restore_point_*.zip')
    restore_files = glob.glob(pattern)

    logger.info(f"[CLEANUP] Found {len(restore_files)} restore point files matching pattern: {pattern}")
    logger.debug(f"[CLEANUP] Restore files: {restore_files}")

    # Sort by modification time (newest first)
    restore_files.sort(key=os.path.getmtime, reverse=True)

    files_to_delete = restore_files[keep_count:]
    logger.info(f"[CLEANUP] Will keep {min(len(restore_files), keep_count)} files, deleting {len(files_to_delete)} old files")

    # Delete old files beyond keep_count
    for old_file in files_to_delete:
        try:
            os.remove(old_file)
            logger.info(f"[CLEANUP] ✓ Deleted old restore point: {old_file}")
        except Exception as e:
            logger.error(f"[CLEANUP] ✗ Error deleting {old_file}: {e}")

def cleanup_old_safety_backups(keep_count=3):
    """
    Delete old safety backups created before restore operations.
    Cleans up:
    - instance/*.backup_* (database backups)
    - static/uploads_backup_*/ (upload folder backups)
    - templates/email_templates_backup_*/ (template folder backups)

    Args:
        keep_count (int): Number of most recent backups to keep for each type
    """
    logger.info(f"[CLEANUP] Starting cleanup_old_safety_backups(keep_count={keep_count})")

    # Cleanup database backups
    db_backup_pattern = 'instance/*.backup_*'
    db_backups = glob.glob(db_backup_pattern)
    logger.info(f"[CLEANUP] Database backups: Found {len(db_backups)} files matching '{db_backup_pattern}'")
    logger.debug(f"[CLEANUP] Database backup files: {db_backups}")

    db_backups.sort(key=os.path.getmtime, reverse=True)
    db_to_delete = db_backups[keep_count:]
    logger.info(f"[CLEANUP] Database backups: Keeping {min(len(db_backups), keep_count)}, deleting {len(db_to_delete)}")

    for old_backup in db_to_delete:
        try:
            os.remove(old_backup)
            logger.info(f"[CLEANUP] ✓ Deleted old database backup: {old_backup}")
        except Exception as e:
            logger.error(f"[CLEANUP] ✗ Error deleting {old_backup}: {e}")

    # Cleanup uploads backups
    uploads_backup_pattern = 'static/uploads_backup_*'
    uploads_backups = glob.glob(uploads_backup_pattern)
    logger.info(f"[CLEANUP] Upload backups: Found {len(uploads_backups)} folders matching '{uploads_backup_pattern}'")
    logger.debug(f"[CLEANUP] Upload backup folders: {uploads_backups}")

    uploads_backups.sort(key=os.path.getmtime, reverse=True)
    uploads_to_delete = uploads_backups[keep_count:]
    logger.info(f"[CLEANUP] Upload backups: Keeping {min(len(uploads_backups), keep_count)}, deleting {len(uploads_to_delete)}")

    for old_backup in uploads_to_delete:
        try:
            shutil.rmtree(old_backup)
            logger.info(f"[CLEANUP] ✓ Deleted old uploads backup: {old_backup}")
        except Exception as e:
            logger.error(f"[CLEANUP] ✗ Error deleting {old_backup}: {e}")

    # Cleanup template backups
    templates_backup_pattern = 'templates/email_templates_backup_*'
    template_backups = glob.glob(templates_backup_pattern)
    logger.info(f"[CLEANUP] Template backups: Found {len(template_backups)} folders matching '{templates_backup_pattern}'")
    logger.debug(f"[CLEANUP] Template backup folders: {template_backups}")

    template_backups.sort(key=os.path.getmtime, reverse=True)
    templates_to_delete = template_backups[keep_count:]
    logger.info(f"[CLEANUP] Template backups: Keeping {min(len(template_backups), keep_count)}, deleting {len(templates_to_delete)}")

    for old_backup in templates_to_delete:
        try:
            shutil.rmtree(old_backup)
            logger.info(f"[CLEANUP] ✓ Deleted old template backup: {old_backup}")
        except Exception as e:
            logger.error(f"[CLEANUP] ✗ Error deleting {old_backup}: {e}")

    logger.info(f"[CLEANUP] Finished cleanup_old_safety_backups()")

def create_restore_point():
    """Create an automatic restore point before major operations"""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    restore_point_name = f"restore_point_{timestamp}.zip"
    
    # Use the same backup creation logic but with a different name
    try:
        backup_dir = BACKUP_DIR
        os.makedirs(backup_dir, exist_ok=True)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            backup_path = os.path.join(temp_dir, restore_point_name)
            
            with ZipFile(backup_path, 'w') as zipf:
                # Include database — same WAL-aware snapshot as create_backup(), so the
                # safety net taken before a restore isn't itself missing recent commits.
                db_path = resolve_db_path()
                if os.path.exists(db_path):
                    snapshot_path = os.path.join(temp_dir, 'minipass_snapshot.db')
                    snapshot_database(snapshot_path)
                    zipf.write(snapshot_path, 'database/minipass.db')
                
                # Include settings
                settings_data = export_settings()
                settings_file = os.path.join(temp_dir, 'settings.json')
                with open(settings_file, 'w') as f:
                    json.dump(settings_data, f, indent=2)
                zipf.write(settings_file, 'settings.json')
                
                # Add metadata
                metadata = {
                    'backup_type': 'restore_point',
                    'created_at': datetime.now(timezone.utc).isoformat(),
                    'created_by': 'system',
                    'version': '1.0'
                }
                metadata_file = os.path.join(temp_dir, 'backup_metadata.json')
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
                zipf.write(metadata_file, 'backup_metadata.json')
            
            # Move to backup directory
            final_path = os.path.join(backup_dir, restore_point_name)
            shutil.move(backup_path, final_path)

        # Cleanup old restore points after successful creation
        cleanup_old_restore_points(keep_count=3)

        return restore_point_name
    except Exception as e:
        print(f"Failed to create restore point: {e}")
        return None
