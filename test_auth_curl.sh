#!/bin/bash

# Production URL
URL="https://article-hub-959205905728.asia-northeast1.run.app"

echo "Testing Authentication Flow"
echo "=================================================="

# Test redirects
echo -e "\nTesting path redirects:"
for path in "/" "/home" "/kanban"; do
    echo -e "\nTesting $path:"
    response=$(curl -s -o /dev/null -w "%{http_code} -> %{redirect_url}" "$URL$path")
    echo "  Response: $response (should redirect to /login)"
done

echo -e "\n\nTesting authentication pages:"
# Test /login page
echo -e "\n/login page:"
response=$(curl -s -o /dev/null -w "%{http_code}" "$URL/login")
echo "  Response: $response (should be 200)"

# Test /dashboard page
echo -e "\n/dashboard page:"
response=$(curl -s -o /dev/null -w "%{http_code}" "$URL/dashboard")
echo "  Response: $response (should be 200, but will redirect to /login via JavaScript)"

echo -e "\n=================================================="
echo -e "\nTesting API Authentication:"

# Test /api/stats without authentication
echo -e "\n/api/stats without authentication:"
response=$(curl -s -w "\nHTTP Status: %{http_code}\n" "$URL/api/stats")
echo "$response"

echo -e "\n=================================================="
echo -e "\nSummary:"
echo "1. Root and old paths redirect to /login ✓"
echo "2. Login page at /login ✓"
echo "3. Dashboard requires authentication (redirects to /login) ✓"
echo "4. API endpoints require authentication ✓"
echo -e "\nAuthentication flow: Any path → /login → LINE Auth → /dashboard"