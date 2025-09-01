#!/usr/bin/env python3
"""
Debug script to check KPI chart initialization in activity dashboard
"""
import requests
from bs4 import BeautifulSoup
import re

def check_activity_dashboard():
    """Check activity dashboard for chart containers and initialization"""
    
    try:
        # Get activity dashboard page
        response = requests.get('http://localhost:5000/activity-dashboard/1')
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        print("=== CHART CONTAINER CHECK ===")
        
        # Check for chart containers
        chart_ids = ['revenue-chart', 'active-users-chart', 'passports-created-chart', 'unpaid-passports-chart']
        for chart_id in chart_ids:
            chart_div = soup.find('div', {'id': chart_id})
            if chart_div:
                print(f"✓ Found {chart_id}: {chart_div}")
            else:
                print(f"✗ Missing {chart_id}")
        
        print("\n=== JAVASCRIPT FUNCTION CHECK ===")
        
        # Check for JavaScript functions
        script_tags = soup.find_all('script')
        js_content = '\n'.join([script.string or '' for script in script_tags if script.string])
        
        functions_to_check = [
            'initializeChartsWithData',
            'initializeApexChartsForKPI',
            'initializeKPIBarChart'
        ]
        
        for func_name in functions_to_check:
            if func_name in js_content:
                print(f"✓ Found function: {func_name}")
            else:
                print(f"✗ Missing function: {func_name}")
        
        print("\n=== APEX CHARTS LIBRARY CHECK ===")
        
        # Check for ApexCharts library
        apex_script = soup.find('script', src=re.compile(r'apexcharts'))
        if apex_script:
            print(f"✓ Found ApexCharts library: {apex_script.get('src')}")
        else:
            print("✗ ApexCharts library not found")
        
        print("\n=== KPI DATA CHECK ===")
        
        # Check for kpiData variable
        if 'const kpiData' in js_content:
            print("✓ Found kpiData variable")
            # Extract kpiData
            kpi_match = re.search(r'const kpiData = ({.*?});', js_content, re.DOTALL)
            if kpi_match:
                print("✓ kpiData contains data")
                kpi_data_str = kpi_match.group(1)
                if 'active_users' in kpi_data_str:
                    print("✓ active_users data found")
                if 'passports_created' in kpi_data_str:
                    print("✓ passports_created data found")
                if 'unpaid_passports' in kpi_data_str:
                    print("✓ unpaid_passports data found")
        else:
            print("✗ kpiData variable not found")
            
    except Exception as e:
        print(f"Error checking activity dashboard: {e}")

if __name__ == "__main__":
    check_activity_dashboard()