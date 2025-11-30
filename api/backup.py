# api/backup.py - Backup and Restore System
from flask import Blueprint, request, jsonify, send_file, current_app
from datetime import datetime, timezone
import os
import tempfile
import shutil
import json
import sqlite3
import glob
import logging
from zipfile import ZipFile
from pathlib import Path

from models import db, Setting, Admin, AdminActionLog
from decorators import admin_required, rate_limit
from utils import get_setting

# Configure logging
logger = logging.getLogger(__name__)

backup_api = Blueprint('backup_api', __name__, url_prefix='/api/v1/backup')

# ============================================================================
# BACKUP OPERATIONS
# ============================================================================

@backup_api.route('/create', methods=['POST'])
@admin_required
@rate_limit(max_requests=5, window=300)  # 5 backups per 5 minutes
def create_backup():
    """Create a complete system backup"""
    try:
        backup_type = request.json.get('type', 'full')  # 'full', 'settings', 'data'
        include_uploads = request.json.get('include_uploads', True)
        
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_filename = f"minipass_backup_{backup_type}_{timestamp}.zip"
        
        # Create temporary directory for backup
        with tempfile.TemporaryDirectory() as temp_dir:
            backup_path = os.path.join(temp_dir, backup_filename)
            
            with ZipFile(backup_path, 'w') as zipf:
                # Always include database
                db_path = current_app.config.get('DATABASE_PATH', 'instance/minipass.db')
                if os.path.exists(db_path):
                    zipf.write(db_path, 'database/minipass.db')
                
                # Include settings export
                settings_data = export_settings()
                settings_file = os.path.join(temp_dir, 'settings.json')
                with open(settings_file, 'w') as f:
                    json.dump(settings_data, f, indent=2)
                zipf.write(settings_file, 'settings.json')
                
                # Include uploads if requested
                if include_uploads and backup_type in ['full', 'data']:
                    upload_dir = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
                    if os.path.exists(upload_dir):
                        for root, dirs, files in os.walk(upload_dir):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arc_path = os.path.relpath(file_path, os.path.dirname(upload_dir))
                                zipf.write(file_path, arc_path)
                
                # Include ALL email template files if full backup (HTML, compiled, images, JSON, etc.)
                if backup_type == 'full':
                    template_dir = 'templates/email_templates'
                    if os.path.exists(template_dir):
                        for root, dirs, files in os.walk(template_dir):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arc_path = os.path.relpath(file_path, 'templates')
                                zipf.write(file_path, f'templates/{arc_path}')
                
                # Add backup metadata
                metadata = {
                    'backup_type': backup_type,
                    'created_at': datetime.now(timezone.utc).isoformat(),
                    'created_by': request.headers.get('X-Admin-Email', 'unknown'),
                    'version': '1.0',
                    'include_uploads': include_uploads
                }
                metadata_file = os.path.join(temp_dir, 'backup_metadata.json')
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
                zipf.write(metadata_file, 'backup_metadata.json')
            
            # Move to backup directory
            backup_dir = os.path.join('static', 'backups')
            os.makedirs(backup_dir, exist_ok=True)
            final_path = os.path.join(backup_dir, backup_filename)
            shutil.move(backup_path, final_path)
        
        # Log action
        log_backup_action(f"Created {backup_type} backup: {backup_filename}")
        
        # Get file size
        file_size = os.path.getsize(final_path)
        
        return jsonify({
            'success': True,
            'data': {
                'filename': backup_filename,
                'type': backup_type,
                'size': file_size,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'path': f'/static/backups/{backup_filename}'
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@backup_api.route('/list', methods=['GET'])
@admin_required
def list_backups():
    """List all available backups"""
    try:
        backup_dir = os.path.join('static', 'backups')
        if not os.path.exists(backup_dir):
            return jsonify({'success': True, 'data': []})
        
        backups = []
        for filename in os.listdir(backup_dir):
            if filename.endswith('.zip'):
                file_path = os.path.join(backup_dir, filename)
                stat = os.stat(file_path)
                
                # Try to extract metadata from backup
                metadata = {}
                try:
                    with ZipFile(file_path, 'r') as zipf:
                        if 'backup_metadata.json' in zipf.namelist():
                            with zipf.open('backup_metadata.json') as f:
                                metadata = json.load(f)
                except:
                    pass  # If metadata can't be read, continue without it
                
                backups.append({
                    'filename': filename,
                    'size': stat.st_size,
                    'created_at': datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                    'type': metadata.get('backup_type', 'unknown'),
                    'version': metadata.get('version', 'unknown'),
                    'created_by': metadata.get('created_by', 'unknown')
                })
        
        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x['created_at'], reverse=True)
        
        return jsonify({'success': True, 'data': backups})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@backup_api.route('/download/<filename>', methods=['GET'])
@admin_required
@rate_limit(max_requests=10, window=300)
def download_backup(filename):
    """Download a backup file"""
    try:
        # Validate filename to prevent path traversal
        if not filename.endswith('.zip') or '/' in filename or '\\' in filename:
            return jsonify({'success': False, 'error': 'Invalid filename'}), 400
        
        backup_path = os.path.join('static', 'backups', filename)
        if not os.path.exists(backup_path):
            return jsonify({'success': False, 'error': 'Backup not found'}), 404
        
        log_backup_action(f"Downloaded backup: {filename}")
        
        return send_file(
            backup_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/zip'
        )
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@backup_api.route('/delete/<filename>', methods=['DELETE'])
@admin_required
@rate_limit(max_requests=10, window=300)
def delete_backup(filename):
    """Delete a backup file"""
    try:
        # Validate filename
        if not filename.endswith('.zip') or '/' in filename or '\\' in filename:
            return jsonify({'success': False, 'error': 'Invalid filename'}), 400

        backup_path = os.path.join('static', 'backups', filename)
        if not os.path.exists(backup_path):
            return jsonify({'success': False, 'error': 'Backup not found'}), 404

        os.remove(backup_path)
        log_backup_action(f"Deleted backup: {filename}")

        return jsonify({'success': True, 'message': f'Backup {filename} deleted'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@backup_api.route('/cleanup-now', methods=['POST'])
@admin_required
@rate_limit(max_requests=10, window=300)
def manual_cleanup():
    """Manually trigger cleanup of old backups (for testing/debugging)"""
    try:
        logger.info("[MANUAL CLEANUP] Manual cleanup endpoint called")

        # Run both cleanup functions
        cleanup_old_restore_points(keep_count=3)
        cleanup_old_safety_backups(keep_count=3)

        return jsonify({
            'success': True,
            'message': 'Cleanup completed. Check logs for details.'
        })

    except Exception as e:
        logger.error(f"[MANUAL CLEANUP] Error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# RESTORE OPERATIONS
# ============================================================================

@backup_api.route('/restore', methods=['POST'])
@admin_required
@rate_limit(max_requests=2, window=600)  # 2 restores per 10 minutes
def restore_backup():
    """Restore from a backup file"""
    logger.info("[RESTORE] ========== RESTORE BACKUP FUNCTION CALLED ==========")

    restore_successful = False
    try:
        filename = request.json.get('filename')
        restore_type = request.json.get('type', 'full')  # 'full', 'settings', 'data'
        confirm = request.json.get('confirm', False)

        logger.info(f"[RESTORE] Filename: {filename}, Type: {restore_type}, Confirm: {confirm}")

        if not confirm:
            return jsonify({
                'success': False,
                'error': 'Restore confirmation required'
            }), 400

        if not filename:
            return jsonify({'success': False, 'error': 'Filename required'}), 400

        backup_path = os.path.join('static', 'backups', filename)
        if not os.path.exists(backup_path):
            return jsonify({'success': False, 'error': 'Backup not found'}), 404

        # Create restore point before restoring
        create_restore_point()

        with tempfile.TemporaryDirectory() as temp_dir:
            # Extract backup
            with ZipFile(backup_path, 'r') as zipf:
                zipf.extractall(temp_dir)

            # Read metadata
            metadata_file = os.path.join(temp_dir, 'backup_metadata.json')
            metadata = {}
            if os.path.exists(metadata_file):
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)

            # Restore based on type
            if restore_type in ['full', 'settings']:
                restore_settings(temp_dir)

            if restore_type in ['full', 'data']:
                restore_database(temp_dir)
                restore_uploads(temp_dir)

            if restore_type == 'full':
                restore_templates(temp_dir)

        logger.info("[RESTORE] Restore operations completed successfully")
        restore_successful = True

        log_backup_action(f"Restored from backup: {filename} (type: {restore_type})")

        return jsonify({
            'success': True,
            'message': f'Successfully restored {restore_type} backup',
            'metadata': metadata
        })

    except Exception as e:
        logger.error(f"[RESTORE] Error during restore: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

    finally:
        # ALWAYS cleanup old backups, even if restore failed
        # This runs after successful restore or after exception
        if restore_successful:
            logger.info("[RESTORE] Running cleanup in finally block...")
            try:
                cleanup_old_safety_backups(keep_count=3)
                logger.info("[RESTORE] Cleanup completed successfully")
            except Exception as cleanup_error:
                logger.error(f"[RESTORE] Cleanup failed: {cleanup_error}", exc_info=True)

@backup_api.route('/validate/<filename>', methods=['GET'])
@admin_required
def validate_backup(filename):
    """Validate a backup file"""
    try:
        backup_path = os.path.join('static', 'backups', filename)
        if not os.path.exists(backup_path):
            return jsonify({'success': False, 'error': 'Backup not found'}), 404
        
        validation_result = {
            'filename': filename,
            'valid': True,
            'errors': [],
            'warnings': [],
            'contents': []
        }
        
        try:
            with ZipFile(backup_path, 'r') as zipf:
                # Check for required files
                files = zipf.namelist()
                validation_result['contents'] = files
                
                # Check for metadata
                if 'backup_metadata.json' in files:
                    with zipf.open('backup_metadata.json') as f:
                        metadata = json.load(f)
                        validation_result['metadata'] = metadata
                else:
                    validation_result['warnings'].append('No metadata found')
                
                # Check for database
                if not any(f.startswith('database/') for f in files):
                    validation_result['errors'].append('No database found in backup')
                
                # Check for settings
                if 'settings.json' not in files:
                    validation_result['warnings'].append('No settings export found')
                
                # Validate database if present
                db_files = [f for f in files if f.startswith('database/')]
                if db_files:
                    try:
                        with zipf.open(db_files[0]) as db_file:
                            # Try to open as SQLite database
                            temp_db_path = os.path.join(tempfile.gettempdir(), 'temp_validate.db')
                            with open(temp_db_path, 'wb') as temp_f:
                                temp_f.write(db_file.read())
                            
                            conn = sqlite3.connect(temp_db_path)
                            cursor = conn.cursor()
                            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                            tables = cursor.fetchall()
                            conn.close()
                            os.remove(temp_db_path)
                            
                            validation_result['database_tables'] = [t[0] for t in tables]
                    except Exception as e:
                        validation_result['errors'].append(f'Database validation failed: {str(e)}')
                
        except Exception as e:
            validation_result['valid'] = False
            validation_result['errors'].append(f'Failed to read backup file: {str(e)}')
        
        if validation_result['errors']:
            validation_result['valid'] = False
        
        return jsonify({'success': True, 'data': validation_result})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

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

def restore_settings(temp_dir):
    """Restore settings from backup"""
    settings_file = os.path.join(temp_dir, 'settings.json')
    if not os.path.exists(settings_file):
        return
    
    with open(settings_file, 'r') as f:
        settings_data = json.load(f)
    
    # Restore settings (excluding admin accounts)
    for key, value in settings_data.items():
        if not key.startswith('_'):
            setting = Setting.query.filter_by(key=key).first()
            if setting:
                setting.value = value
            else:
                db.session.add(Setting(key=key, value=value))
    
    db.session.commit()

def restore_database(temp_dir):
    """Restore database from backup"""
    db_backup_path = os.path.join(temp_dir, 'database', 'minipass.db')
    if not os.path.exists(db_backup_path):
        return
    
    # Get current database path
    db_path = current_app.config.get('DATABASE_PATH', 'instance/minipass.db')
    
    # Create backup of current database
    if os.path.exists(db_path):
        backup_current_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(db_path, backup_current_path)
    
    # Restore database
    shutil.copy2(db_backup_path, db_path)

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

    backup_dir = os.path.join('static', 'backups')
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
        backup_dir = os.path.join('static', 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            backup_path = os.path.join(temp_dir, restore_point_name)
            
            with ZipFile(backup_path, 'w') as zipf:
                # Include database
                db_path = current_app.config.get('DATABASE_PATH', 'instance/minipass.db')
                if os.path.exists(db_path):
                    zipf.write(db_path, 'database/minipass.db')
                
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

def log_backup_action(action):
    """Log backup/restore actions"""
    log = AdminActionLog(
        admin_email=request.headers.get('X-Admin-Email', 'unknown'),
        action=action,
        timestamp=datetime.now(timezone.utc)
    )
    db.session.add(log)
    db.session.commit()