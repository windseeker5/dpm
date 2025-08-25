#!/usr/bin/env python3
"""
Static Asset Validator for Minipass Application

This script identifies all missing/inaccessible static files that could be causing 404 errors
by parsing HTML templates and checking both filesystem and HTTP accessibility.

Usage:
    python test/static_asset_checker.py

Output:
    - missing_assets.txt: List of all missing files
    - asset_status_report.json: Complete status of all assets
"""

import os
import sys
import json
import re
import requests
from pathlib import Path
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from collections import defaultdict
import time
from datetime import datetime

class StaticAssetChecker:
    def __init__(self, app_root=None):
        self.app_root = Path(app_root) if app_root else Path(__file__).parent.parent
        self.templates_dir = self.app_root / "templates"
        self.static_dir = self.app_root / "static"
        self.test_dir = self.app_root / "test"
        
        # Environment URLs
        self.local_base = "http://127.0.0.1:8890"
        self.vps_base = "https://lhgi.minipass.me"
        
        # Asset tracking
        self.all_assets = set()
        self.template_assets = defaultdict(list)
        self.asset_results = {}
        self.critical_assets = {
            # Core Tabler framework files
            'tabler/css/tabler.min.css', 'tabler/js/tabler.min.js',
            'tabler/icons/tabler-icons.min.css',
            # Custom application assets
            'css/dropdown-fix.css', 'js/dropdown-fix.js',
            'minipass.css',
            # TinyMCE editor
            'tinymce/tinymce.min.js',
            # Essential icons and images
            'favicon.png', 'apple-touch-icon.png'
        }
        
        # Session for HTTP requests
        self.session = requests.Session()
        self.session.timeout = 10
        
        print(f"🔍 Static Asset Checker initialized")
        print(f"📁 App root: {self.app_root}")
        print(f"📄 Templates: {self.templates_dir}")
        print(f"📦 Static files: {self.static_dir}")
    
    def find_all_templates(self):
        """Find all HTML template files."""
        templates = []
        for root, dirs, files in os.walk(self.templates_dir):
            for file in files:
                if file.endswith(('.html', '.htm')):
                    templates.append(Path(root) / file)
        return templates
    
    def extract_assets_from_template(self, template_path):
        """Extract all static asset references from a template file."""
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"❌ Error reading {template_path}: {e}")
            return []
        
        assets = []
        
        # Parse with BeautifulSoup
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # CSS files
            for link in soup.find_all('link', href=True):
                if link.get('rel') and 'stylesheet' in link.get('rel'):
                    assets.append(('css', link['href']))
            
            # JavaScript files
            for script in soup.find_all('script', src=True):
                assets.append(('js', script['src']))
            
            # Images
            for img in soup.find_all('img', src=True):
                assets.append(('img', img['src']))
            
            # Background images in style attributes
            style_bg_pattern = r'background-image:\s*url\([\'"]?([^\'")]+)[\'"]?\)'
            for match in re.finditer(style_bg_pattern, content, re.IGNORECASE):
                assets.append(('bg-img', match.group(1)))
            
        except Exception as e:
            print(f"❌ Error parsing {template_path} with BeautifulSoup: {e}")
        
        # Additional regex patterns for assets that might be missed
        patterns = [
            # CSS @import and url() functions
            (r'@import\s+[\'"]([^\'"]+)[\'"]', 'css'),
            (r'url\([\'"]?([^\'")]+)[\'"]?\)', 'resource'),
            # Flask url_for static calls
            (r'url_for\([\'"]static[\'"],\s*filename=[\'"]([^\'"]+)[\'"]', 'static'),
            # Direct static references
            (r'/static/([^\s\'"<>]+)', 'static'),
            # Favicon and manifest
            (r'href=[\'"]([^\'">]*\.ico)[\'"]', 'icon'),
            (r'href=[\'"]([^\'">]*manifest\.json)[\'"]', 'manifest'),
        ]
        
        for pattern, asset_type in patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                asset_path = match.group(1)
                assets.append((asset_type, asset_path))
        
        return assets
    
    def normalize_asset_path(self, asset_path):
        """Normalize asset path to relative static path."""
        # Remove leading slashes and 'static/' prefix
        asset_path = asset_path.lstrip('/')
        if asset_path.startswith('static/'):
            asset_path = asset_path[7:]  # Remove 'static/' prefix
        
        # Skip external URLs
        if asset_path.startswith(('http://', 'https://', '//')):
            return None
        
        # Skip data URLs
        if asset_path.startswith('data:'):
            return None
        
        # Skip template variables that haven't been rendered
        if '{{' in asset_path or '{%' in asset_path:
            return None
        
        # Skip JavaScript template literals and variables
        if asset_path.startswith(('${', 'cid:', 'window.', 'params', 'file')):
            return None
        
        # Skip pure variable names or incomplete paths
        if asset_path in ['file', 'params', 'window.location'] or '${' in asset_path:
            return None
        
        # Skip email CID references
        if asset_path.startswith('cid:'):
            return None
        
        # Skip template placeholders that ended up as literal text
        if asset_path.endswith(('`;', ') `;', ')`')):
            return None
        
        return asset_path
    
    def check_file_exists(self, asset_path):
        """Check if asset file exists on filesystem."""
        full_path = self.static_dir / asset_path
        exists = full_path.exists()
        size = full_path.stat().st_size if exists else 0
        return exists, size
    
    def check_http_accessibility(self, asset_path, base_url):
        """Check if asset is accessible via HTTP."""
        url = urljoin(base_url + '/static/', asset_path)
        try:
            response = self.session.head(url, allow_redirects=True)
            accessible = response.status_code == 200
            size = int(response.headers.get('content-length', 0))
            return accessible, response.status_code, size, url
        except Exception as e:
            return False, 0, 0, url
    
    def analyze_assets(self):
        """Analyze all assets found in templates."""
        print(f"\n📊 Analyzing assets...")
        
        templates = self.find_all_templates()
        print(f"Found {len(templates)} template files")
        
        # Extract assets from each template
        for template in templates:
            relative_template = template.relative_to(self.app_root)
            print(f"📄 Processing: {relative_template}")
            
            assets = self.extract_assets_from_template(template)
            template_key = str(relative_template)
            
            for asset_type, asset_path in assets:
                normalized_path = self.normalize_asset_path(asset_path)
                if normalized_path:
                    self.all_assets.add(normalized_path)
                    self.template_assets[template_key].append({
                        'type': asset_type,
                        'original_path': asset_path,
                        'normalized_path': normalized_path
                    })
        
        print(f"Found {len(self.all_assets)} unique assets")
        
        # Check each asset
        for i, asset_path in enumerate(sorted(self.all_assets), 1):
            print(f"🔍 [{i}/{len(self.all_assets)}] Checking: {asset_path}")
            
            # Check filesystem
            file_exists, file_size = self.check_file_exists(asset_path)
            
            # Check HTTP accessibility
            local_accessible, local_status, local_size, local_url = self.check_http_accessibility(
                asset_path, self.local_base
            )
            
            vps_accessible, vps_status, vps_size, vps_url = self.check_http_accessibility(
                asset_path, self.vps_base
            )
            
            # Determine criticality
            is_critical = any(critical in asset_path for critical in self.critical_assets)
            
            # Store results
            self.asset_results[asset_path] = {
                'file_exists': file_exists,
                'file_size': file_size,
                'local': {
                    'accessible': local_accessible,
                    'status_code': local_status,
                    'size': local_size,
                    'url': local_url
                },
                'vps': {
                    'accessible': vps_accessible,
                    'status_code': vps_status,
                    'size': vps_size,
                    'url': vps_url
                },
                'is_critical': is_critical,
                'used_in_templates': []
            }
            
            # Add template references
            for template_key, template_assets in self.template_assets.items():
                for asset_info in template_assets:
                    if asset_info['normalized_path'] == asset_path:
                        self.asset_results[asset_path]['used_in_templates'].append({
                            'template': template_key,
                            'type': asset_info['type'],
                            'original_path': asset_info['original_path']
                        })
    
    def generate_missing_assets_report(self):
        """Generate missing assets text report."""
        missing_file = self.test_dir / "missing_assets.txt"
        
        with open(missing_file, 'w') as f:
            f.write("MINIPASS - MISSING STATIC ASSETS REPORT\n")
            f.write("=" * 50 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total assets checked: {len(self.asset_results)}\n\n")
            
            # Critical missing assets
            critical_missing = []
            non_critical_missing = []
            local_inaccessible = []
            vps_inaccessible = []
            
            for asset_path, info in self.asset_results.items():
                if not info['file_exists']:
                    if info['is_critical']:
                        critical_missing.append(asset_path)
                    else:
                        non_critical_missing.append(asset_path)
                
                if not info['local']['accessible']:
                    local_inaccessible.append(asset_path)
                
                if not info['vps']['accessible']:
                    vps_inaccessible.append(asset_path)
            
            # Write critical missing
            if critical_missing:
                f.write("🚨 CRITICAL MISSING FILES (HIGH PRIORITY)\n")
                f.write("-" * 45 + "\n")
                for asset in sorted(critical_missing):
                    f.write(f"❌ {asset}\n")
                    for template_ref in self.asset_results[asset]['used_in_templates']:
                        f.write(f"   └─ Used in: {template_ref['template']} ({template_ref['type']})\n")
                f.write(f"\nTotal critical missing: {len(critical_missing)}\n\n")
            
            # Write non-critical missing
            if non_critical_missing:
                f.write("⚠️  NON-CRITICAL MISSING FILES\n")
                f.write("-" * 30 + "\n")
                for asset in sorted(non_critical_missing):
                    f.write(f"⚠️  {asset}\n")
                f.write(f"\nTotal non-critical missing: {len(non_critical_missing)}\n\n")
            
            # Write local inaccessible
            if local_inaccessible:
                f.write("🌐 LOCAL SERVER INACCESSIBLE (127.0.0.1:8890)\n")
                f.write("-" * 45 + "\n")
                for asset in sorted(local_inaccessible):
                    info = self.asset_results[asset]
                    status = info['local']['status_code']
                    f.write(f"❌ {asset} (HTTP {status})\n")
                f.write(f"\nTotal local inaccessible: {len(local_inaccessible)}\n\n")
            
            # Write VPS inaccessible
            if vps_inaccessible:
                f.write("🌐 VPS SERVER INACCESSIBLE (lhgi.minipass.me)\n")
                f.write("-" * 45 + "\n")
                for asset in sorted(vps_inaccessible):
                    info = self.asset_results[asset]
                    status = info['vps']['status_code']
                    f.write(f"❌ {asset} (HTTP {status})\n")
                f.write(f"\nTotal VPS inaccessible: {len(vps_inaccessible)}\n\n")
            
            # Summary
            f.write("📊 SUMMARY\n")
            f.write("-" * 10 + "\n")
            f.write(f"Total assets: {len(self.asset_results)}\n")
            f.write(f"Critical missing: {len(critical_missing)}\n")
            f.write(f"Non-critical missing: {len(non_critical_missing)}\n")
            f.write(f"Local inaccessible: {len(local_inaccessible)}\n")
            f.write(f"VPS inaccessible: {len(vps_inaccessible)}\n")
        
        print(f"📝 Missing assets report saved: {missing_file}")
        return missing_file
    
    def generate_json_report(self):
        """Generate comprehensive JSON report."""
        report_file = self.test_dir / "asset_status_report.json"
        
        # Calculate summary statistics
        total_assets = len(self.asset_results)
        file_missing = sum(1 for info in self.asset_results.values() if not info['file_exists'])
        local_inaccessible = sum(1 for info in self.asset_results.values() if not info['local']['accessible'])
        vps_inaccessible = sum(1 for info in self.asset_results.values() if not info['vps']['accessible'])
        critical_issues = sum(1 for info in self.asset_results.values() 
                            if info['is_critical'] and not info['file_exists'])
        
        report = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'app_root': str(self.app_root),
                'local_base_url': self.local_base,
                'vps_base_url': self.vps_base,
                'templates_scanned': len(self.template_assets)
            },
            'summary': {
                'total_assets': total_assets,
                'file_missing': file_missing,
                'local_inaccessible': local_inaccessible,
                'vps_inaccessible': vps_inaccessible,
                'critical_issues': critical_issues,
                'healthy_assets': total_assets - max(file_missing, local_inaccessible, vps_inaccessible)
            },
            'template_assets': dict(self.template_assets),
            'asset_details': self.asset_results
        }
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"📊 JSON report saved: {report_file}")
        return report_file
    
    def print_summary(self):
        """Print summary to console."""
        print(f"\n" + "=" * 60)
        print(f"📊 STATIC ASSET VALIDATION SUMMARY")
        print(f"=" * 60)
        
        total = len(self.asset_results)
        missing_files = sum(1 for info in self.asset_results.values() if not info['file_exists'])
        local_issues = sum(1 for info in self.asset_results.values() if not info['local']['accessible'])
        vps_issues = sum(1 for info in self.asset_results.values() if not info['vps']['accessible'])
        critical_issues = sum(1 for info in self.asset_results.values() 
                            if info['is_critical'] and not info['file_exists'])
        
        print(f"Total assets checked: {total}")
        print(f"Missing files: {missing_files}")
        print(f"Local server issues: {local_issues}")
        print(f"VPS server issues: {vps_issues}")
        print(f"Critical issues: {critical_issues}")
        
        if critical_issues > 0:
            print(f"\n🚨 CRITICAL ISSUES FOUND!")
            print(f"   {critical_issues} critical assets are missing/inaccessible")
            print(f"   This could significantly impact page load performance")
        
        if missing_files == 0 and local_issues == 0 and vps_issues == 0:
            print(f"\n✅ ALL ASSETS ARE HEALTHY!")
        else:
            print(f"\n⚠️  Issues found - check the detailed reports for specifics")
    
    def run(self):
        """Run the complete asset validation process."""
        print(f"🚀 Starting static asset validation...")
        
        # Ensure test directory exists
        self.test_dir.mkdir(exist_ok=True)
        
        start_time = time.time()
        
        try:
            # Analyze all assets
            self.analyze_assets()
            
            # Generate reports
            missing_report = self.generate_missing_assets_report()
            json_report = self.generate_json_report()
            
            # Print summary
            self.print_summary()
            
            elapsed = time.time() - start_time
            print(f"\n⏱️  Validation completed in {elapsed:.2f} seconds")
            print(f"📝 Reports generated:")
            print(f"   - {missing_report}")
            print(f"   - {json_report}")
            
            return {
                'success': True,
                'missing_report': missing_report,
                'json_report': json_report,
                'summary': {
                    'total_assets': len(self.asset_results),
                    'missing_files': sum(1 for info in self.asset_results.values() if not info['file_exists']),
                    'critical_issues': sum(1 for info in self.asset_results.values() 
                                         if info['is_critical'] and not info['file_exists'])
                }
            }
            
        except Exception as e:
            print(f"❌ Error during validation: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Minipass Static Asset Validator')
    parser.add_argument('--app-root', help='Application root directory')
    parser.add_argument('--local-url', default='http://127.0.0.1:8890', 
                       help='Local server URL (default: http://127.0.0.1:8890)')
    parser.add_argument('--vps-url', default='https://lhgi.minipass.me',
                       help='VPS server URL (default: https://lhgi.minipass.me)')
    
    args = parser.parse_args()
    
    checker = StaticAssetChecker(app_root=args.app_root)
    if args.local_url != 'http://127.0.0.1:8890':
        checker.local_base = args.local_url
    if args.vps_url != 'https://lhgi.minipass.me':
        checker.vps_base = args.vps_url
    
    result = checker.run()
    
    # Exit with error code if critical issues found
    if result.get('success') and result.get('summary', {}).get('critical_issues', 0) > 0:
        sys.exit(1)
    elif not result.get('success'):
        sys.exit(2)


if __name__ == '__main__':
    main()