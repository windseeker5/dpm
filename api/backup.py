# api/backup.py - Backup and Restore System
from flask import Blueprint, request, jsonify, send_file, current_app
from datetime import datetime, timezone
import os
import tempfile
import shutil
import json
import sqlite3
from zipfile import ZipFile
from pathlib import Path

from models import db, Setting, Admin, AdminActionLog
from decorators import admin_required, rate_limit
from utils import get_setting

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

# ============================================================================
# RESTORE OPERATIONS
# ============================================================================

@backup_api.route('/restore', methods=['POST'])
@admin_required
@rate_limit(max_requests=2, window=600)  # 2 restores per 10 minutes
def restore_backup():
    """Restore from a backup file"""
    try:
        filename = request.json.get('filename')
        restore_type = request.json.get('type', 'full')  # 'full', 'settings', 'data'
        confirm = request.json.get('confirm', False)
        
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
        
        log_backup_action(f"Restored from backup: {filename} (type: {restore_type})")
        
        return jsonify({
            'success': True,
            'message': f'Successfully restored {restore_type} backup',
            'metadata': metadata
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

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
    """Restore uploaded files from backup"""
    # Try new backup structure first (static/uploads in zip)
    upload_backup_dir = os.path.join(temp_dir, 'static', 'uploads')
    if not os.path.exists(upload_backup_dir):
        # Try old backup structure (uploads directly in temp_dir)
        upload_backup_dir = os.path.join(temp_dir, 'uploads')
    if not os.path.exists(upload_backup_dir):
        return
    
    upload_dir = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
    
    # Create backup of current uploads
    if os.path.exists(upload_dir):
        backup_upload_dir = f"{upload_dir}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if os.path.exists(upload_dir):
            shutil.move(upload_dir, backup_upload_dir)
    
    # Restore uploads
    shutil.copytree(upload_backup_dir, upload_dir)

def restore_templates(temp_dir):
    """Restore email templates from backup"""
    # Try new backup structure first (templates/email_templates in zip)
    template_backup_dir = os.path.join(temp_dir, 'templates', 'email_templates')
    if not os.path.exists(template_backup_dir):
        # Try old backup structure (email_templates directly in temp_dir)
        template_backup_dir = os.path.join(temp_dir, 'email_templates')
    if not os.path.exists(template_backup_dir):
        return
    
    template_dir = 'templates/email_templates'
    
    # Create backup of current templates
    if os.path.exists(template_dir):
        backup_template_dir = f"{template_dir}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.move(template_dir, backup_template_dir)
    
    # Restore templates
    shutil.copytree(template_backup_dir, template_dir)

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