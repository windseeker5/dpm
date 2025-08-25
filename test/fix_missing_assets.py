#!/usr/bin/env python3
"""
Fix Missing Static Assets Script

This script automatically fixes the most common missing asset issues
by creating missing files, symlinks, or default placeholders.

Usage: python test/fix_missing_assets.py
"""

import os
import shutil
from pathlib import Path

class AssetFixer:
    def __init__(self, app_root=None):
        self.app_root = Path(app_root) if app_root else Path(__file__).parent.parent
        self.static_dir = self.app_root / "static"
        self.fixes_applied = []
        
    def create_missing_directory(self, dir_path):
        """Create missing directory if it doesn't exist."""
        full_path = self.static_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created directory: {dir_path}")
            self.fixes_applied.append(f"Created directory: {dir_path}")
            return True
        return False
    
    def create_symlink_or_copy(self, source, target):
        """Create symlink or copy file if source exists."""
        source_path = self.static_dir / source
        target_path = self.static_dir / target
        
        if source_path.exists() and not target_path.exists():
            try:
                # Ensure target directory exists
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Try symlink first, fallback to copy
                try:
                    os.symlink(source_path.resolve(), target_path)
                    print(f"✅ Symlinked: {target} -> {source}")
                    self.fixes_applied.append(f"Symlinked: {target} -> {source}")
                except OSError:
                    shutil.copy2(source_path, target_path)
                    print(f"✅ Copied: {source} -> {target}")
                    self.fixes_applied.append(f"Copied: {source} -> {target}")
                return True
            except Exception as e:
                print(f"❌ Failed to link/copy {source} -> {target}: {e}")
        return False
    
    def create_placeholder_image(self, image_path, width=100, height=100, text="PLACEHOLDER"):
        """Create a simple placeholder image using SVG."""
        target_path = self.static_dir / image_path
        
        if not target_path.exists():
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create a simple SVG placeholder
            svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
  <rect width="100%" height="100%" fill="#f8f9fa" stroke="#dee2e6" stroke-width="2"/>
  <text x="50%" y="50%" font-family="Arial, sans-serif" font-size="12" 
        text-anchor="middle" dominant-baseline="middle" fill="#6c757d">
    {text}
  </text>
</svg>'''
            
            # If it's a PNG/JPG, create SVG with same name but different extension for now
            if image_path.endswith(('.png', '.jpg', '.jpeg')):
                svg_path = target_path.with_suffix('.svg')
                with open(svg_path, 'w') as f:
                    f.write(svg_content)
                print(f"✅ Created placeholder SVG: {svg_path.relative_to(self.static_dir)}")
                self.fixes_applied.append(f"Created placeholder: {image_path}")
            else:
                with open(target_path, 'w') as f:
                    f.write(svg_content)
                print(f"✅ Created placeholder: {image_path}")
                self.fixes_applied.append(f"Created placeholder: {image_path}")
            return True
        return False
    
    def fix_tabler_dist_references(self):
        """Fix references to tabler/dist/ paths by creating symlinks to correct paths."""
        fixes = [
            ("tabler/css/tabler.min.css", "tabler/dist/css/tabler.min.css"),
            ("tabler/js/tabler.min.js", "tabler/dist/js/tabler.min.js"),
        ]
        
        for source, target in fixes:
            self.create_symlink_or_copy(source, target)
    
    def fix_missing_logos_and_images(self):
        """Fix missing logos and common images."""
        # Use existing logos where possible
        logo_fixes = [
            ("assets/brand/logo/primary/logo.png", "logo.png"),
            ("minipass_logo.png", "uploads/logo.png"),
        ]
        
        for source, target in logo_fixes:
            self.create_symlink_or_copy(source, target)
        
        # Create placeholder images for missing ones
        placeholder_images = [
            ("currency-dollar.png", 50, 50, "💰"),
            ("facebook.png", 50, 50, "f"),
            ("instagram.png", 50, 50, "📷"),
            ("good-news.png", 50, 50, "✅"),
            ("hand-rock.png", 50, 50, "🤘"),
            ("thumb-down.png", 50, 50, "👎"),
            ("ticket.png", 50, 50, "🎫"),
            ("default_signup.jpg", 300, 200, "DEFAULT\nSIGNUP"),
            ("uploads/activity_images/activity_name.jpg", 400, 300, "ACTIVITY\nIMAGE"),
        ]
        
        for img_path, width, height, text in placeholder_images:
            self.create_placeholder_image(img_path, width, height, text)
    
    def fix_upload_directories(self):
        """Ensure upload directories exist."""
        upload_dirs = [
            "uploads",
            "uploads/activity_images",
            "uploads/receipts",
            "uploads/avatars",
            "uploads/email_logos",
        ]
        
        for dir_path in upload_dirs:
            self.create_missing_directory(dir_path)
    
    def run_all_fixes(self):
        """Run all asset fixes."""
        print("🔧 Starting asset fixes...")
        
        # Fix directory structure
        print("\n📁 Creating missing directories...")
        self.fix_upload_directories()
        
        # Fix Tabler distribution path issues
        print("\n🎨 Fixing Tabler framework paths...")
        self.fix_tabler_dist_references()
        
        # Fix missing images and logos
        print("\n🖼️  Creating missing images and logos...")
        self.fix_missing_logos_and_images()
        
        # Summary
        print(f"\n✅ Asset fixes completed!")
        print(f"📊 Total fixes applied: {len(self.fixes_applied)}")
        
        if self.fixes_applied:
            print("\n🔧 Fixes applied:")
            for fix in self.fixes_applied:
                print(f"   - {fix}")
        
        return len(self.fixes_applied)

def main():
    fixer = AssetFixer()
    fixes_count = fixer.run_all_fixes()
    
    if fixes_count > 0:
        print(f"\n🎉 Successfully applied {fixes_count} fixes!")
        print("💡 Tip: Re-run the static asset checker to verify fixes")
        print("Command: python test/static_asset_checker.py")
    else:
        print("\n💯 No fixes needed - all assets are already present!")

if __name__ == '__main__':
    main()