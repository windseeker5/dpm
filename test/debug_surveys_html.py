"""
Debug script to capture and analyze the actual HTML output from the surveys page
"""

import requests
import re
from urllib.parse import urljoin

BASE_URL = 'http://127.0.0.1:8890'
TEST_EMAIL = 'kdresdell@gmail.com'
TEST_PASSWORD = 'admin123'

def debug_surveys_html():
    """Capture and analyze the surveys page HTML"""
    print("🔍 Debugging surveys page HTML output...")
    
    session = requests.Session()
    
    try:
        # Login
        login_url = urljoin(BASE_URL, '/login')
        login_page = session.get(login_url)
        
        csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', login_page.text)
        if not csrf_match:
            print("❌ Could not find CSRF token")
            return
            
        csrf_token = csrf_match.group(1)
        
        login_data = {
            'email': TEST_EMAIL,
            'password': TEST_PASSWORD,
            'csrf_token': csrf_token
        }
        
        login_response = session.post(login_url, data=login_data)
        
        # Get surveys page
        surveys_url = urljoin(BASE_URL, '/surveys')
        surveys_response = session.get(surveys_url)
        
        if surveys_response.status_code != 200:
            print(f"❌ Failed to get surveys page: {surveys_response.status_code}")
            return
            
        html = surveys_response.text
        
        # Save the full HTML for analysis
        with open('tests/surveys_debug_output.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("📄 Saved full HTML to tests/surveys_debug_output.html")
        
        # Extract and analyze the table section
        print("\n🔍 Analyzing table and footer sections...")
        
        # Look for the main table card
        table_card_start = html.find('<div class="card main-table-card"')
        if table_card_start == -1:
            print("❌ Could not find main table card")
            return
            
        # Find the end of this card
        card_depth = 0
        pos = table_card_start
        while pos < len(html):
            if html[pos:pos+5] == '<div ':
                card_depth += 1
            elif html[pos:pos+6] == '</div>':
                card_depth -= 1
                if card_depth == 0:
                    table_card_end = pos + 6
                    break
            pos += 1
        
        if 'table_card_end' in locals():
            table_section = html[table_card_start:table_card_end]
            
            # Save table section for detailed analysis
            with open('tests/table_section_debug.html', 'w', encoding='utf-8') as f:
                f.write(table_section)
            print("📄 Saved table section to tests/table_section_debug.html")
            
            # Check what's in the table section
            print("\n📊 Table section analysis:")
            print(f"   • Contains 'card-footer': {'card-footer' in table_section}")
            print(f"   • Contains 'pagination': {'pagination' in table_section}")
            print(f"   • Contains 'Showing': {'Showing' in table_section}")
            print(f"   • Contains 'entries': {'entries' in table_section}")
            print(f"   • Contains 'page-link': {'page-link' in table_section}")
            
            # Look for the actual footer content
            footer_start = table_section.find('card-footer')
            if footer_start != -1:
                # Extract some context around the footer
                footer_context_start = max(0, footer_start - 200)
                footer_context_end = min(len(table_section), footer_start + 1000)
                footer_context = table_section[footer_context_start:footer_context_end]
                
                print("\n📋 Card footer context:")
                print("-" * 40)
                print(footer_context)
                print("-" * 40)
            else:
                print("❌ No card-footer found in table section")
        
        # Check if there are any surveys data
        print("\n📋 Checking for survey data...")
        
        # Look for table rows
        tbody_pattern = r'<tbody>(.*?)</tbody>'
        tbody_match = re.search(tbody_pattern, html, re.DOTALL)
        
        if tbody_match:
            tbody_content = tbody_match.group(1)
            # Count actual data rows (not empty state)
            data_rows = tbody_content.count('<tr>') - tbody_content.count('No surveys found')
            print(f"   • Found {data_rows} survey data rows")
            
            if data_rows == 0:
                print("   • Showing empty state (no surveys in database)")
            else:
                print(f"   • Showing {data_rows} surveys")
        
        # Look for template variables that might not be rendered
        print("\n🔧 Checking for unrendered template variables...")
        
        template_vars = [
            'pagination',
            'current_filters',
            'statistics'
        ]
        
        for var in template_vars:
            if f"{{ {var}" in html or f"{{{{ {var}" in html:
                print(f"⚠️  Found unrendered template variable: {var}")
            else:
                print(f"✅ Template variable {var} appears to be rendered")
        
        # Check what's actually in the pagination area
        print("\n🔍 Looking for pagination-related content...")
        
        # Search for content around where pagination should be
        patterns = [
            r'No entries found',
            r'Showing \d+',
            r'entries',
            r'pagination',
            r'page-link',
            r'page-item'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            if matches:
                print(f"   • Found pattern '{pattern}': {matches[:3]}...")  # Show first 3 matches
            else:
                print(f"   • No matches for pattern '{pattern}'")
        
        print("\n✅ Debug analysis complete!")
        print("📄 Check the saved HTML files for detailed inspection:")
        print("   • tests/surveys_debug_output.html (full page)")
        print("   • tests/table_section_debug.html (table section only)")
        
    except Exception as e:
        print(f"❌ Debug failed: {str(e)}")

if __name__ == "__main__":
    debug_surveys_html()