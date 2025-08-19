#!/bin/bash

# Test activity dashboard with proper login

# 1. Login and get session cookie
echo "Logging in..."
curl -c cookies.txt -X POST http://127.0.0.1:8890/login \
  -d "email=kdresdell@gmail.com&password=admin123" \
  -L -s -o /dev/null

# 2. Access activity dashboard with cookie
echo "Fetching activity dashboard..."
RESPONSE=$(curl -b cookies.txt -s http://127.0.0.1:8890/activity-dashboard/1)

# 3. Check for filter buttons
echo "Checking for filter buttons..."
echo "$RESPONSE" | grep -c "github-filter-btn" || echo "No filter buttons found"

# 4. Check for specific filter button text
echo "Checking for 'Unpaid' filter..."
echo "$RESPONSE" | grep -o "Unpaid.*filter-count" | head -1

# 5. Check if we got redirected to login
if echo "$RESPONSE" | grep -q "Admin Login"; then
  echo "ERROR: Got redirected to login page!"
fi

# 6. Check for JavaScript functions
echo "Checking for filterPassports function..."
echo "$RESPONSE" | grep -c "function filterPassports" || echo "Function not found"

# Clean up
rm -f cookies.txt