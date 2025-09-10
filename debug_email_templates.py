# Debug Email Templates
# Run this in Flask shell: flask shell

from models import Activity, db
from utils_email_defaults import get_default_email_templates

# Get first activity
activity = Activity.query.first()
print(f"Activity: {activity.name}")

# Check email templates
if activity.email_templates:
    print(f"Custom templates: {list(activity.email_templates.keys())}")
else:
    print("No custom templates - using defaults")

# Test defaults loading
defaults = get_default_email_templates()
print(f"Available defaults: {list(defaults.keys())}")

# Test template merging
template_key = 'newPass'
current = activity.email_templates.get(template_key, {}) if activity.email_templates else {}
default = defaults.get(template_key, {})

merged = {
    'subject': current.get('subject') or default.get('subject', ''),
    'title': current.get('title') or default.get('title', ''),
    'intro_text': current.get('intro_text') or default.get('intro_text', ''),
    'conclusion_text': current.get('conclusion_text') or default.get('conclusion_text', '')
}

print(f"Merged template for {template_key}:")
for key, value in merged.items():
    print(f"  {key}: {value[:50]}{'...' if len(value) > 50 else ''}")
