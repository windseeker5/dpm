#!/usr/bin/env python3
"""
Validate that the activity card placeholder fix is properly implemented
"""
import re

def validate_dashboard_fix():
    print("🔍 Validating Activity Card Placeholder Fix...")
    
    try:
        # Read the dashboard template
        with open('templates/dashboard.html', 'r') as f:
            content = f.read()
        
        # Check for the fixed placeholder pattern (desktop version)
        desktop_pattern = r'<div class="img-responsive img-responsive-21x9 card-img-top"\s+style="[^"]*position:\s*relative[^"]*">\s*<div style="position:\s*absolute[^"]*display:\s*flex[^"]*">\s*<i class="ti ti-calendar-event"'
        
        desktop_matches = re.search(desktop_pattern, content, re.MULTILINE | re.DOTALL)
        
        if desktop_matches:
            print("✅ Desktop placeholder fix: FOUND")
        else:
            print("❌ Desktop placeholder fix: NOT FOUND")
            return False
        
        # Count total occurrences of the fixed pattern
        all_fixed_patterns = re.findall(r'position:\s*relative[^>]*>\s*<div style="position:\s*absolute[^>]*>', content)
        
        if len(all_fixed_patterns) >= 2:
            print(f"✅ Found {len(all_fixed_patterns)} properly fixed placeholder containers (desktop + mobile)")
        else:
            print(f"❌ Expected at least 2 fixed containers, found {len(all_fixed_patterns)}")
            return False
        
        # Check that old broken pattern is removed (direct flex on img-responsive container)
        broken_pattern = r'class="img-responsive img-responsive-21x9 card-img-top"\s+style="[^"]*display:\s*flex;\s*align-items:\s*center;\s*justify-content:\s*center[^"]*">\s*<i class="ti ti-calendar-event"'
        broken_matches = re.findall(broken_pattern, content)
        
        if len(broken_matches) == 0:
            print("✅ Old broken pattern: REMOVED")
        else:
            print(f"❌ Found {len(broken_matches)} instances of old broken pattern still present")
            return False
        
        # Validate the structure is correct
        correct_structure_pattern = r'position:\s*relative[^>]*>\s*<div style="position:\s*absolute;\s*top:\s*0;\s*left:\s*0;\s*right:\s*0;\s*bottom:\s*0;\s*display:\s*flex;\s*align-items:\s*center;\s*justify-content:\s*center[^>]*>\s*<i class="ti ti-calendar-event"'
        
        structure_matches = re.findall(correct_structure_pattern, content)
        
        if len(structure_matches) >= 2:
            print(f"✅ Correct nested structure: FOUND ({len(structure_matches)} instances)")
        else:
            print(f"❌ Correct nested structure: Expected at least 2, found {len(structure_matches)}")
            return False
        
        print("\n🎉 All validations passed! The activity card placeholder fix is properly implemented.")
        
        # Show the fix details
        print("\n📋 Fix Summary:")
        print("• Changed from direct flexbox on .img-responsive container")
        print("• Now uses position: relative on container + position: absolute on inner flex div")
        print("• This properly centers the icon within the aspect-ratio maintained by Tabler's .img-responsive-21x9")
        print("• Fix applied to both desktop and mobile layouts")
        
        return True
        
    except FileNotFoundError:
        print("❌ dashboard.html template not found")
        return False
    except Exception as e:
        print(f"❌ Error validating fix: {e}")
        return False

if __name__ == "__main__":
    success = validate_dashboard_fix()
    exit(0 if success else 1)