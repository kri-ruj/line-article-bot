#!/bin/bash

echo "🔧 LINE Bot Setup Script"
echo "========================"
echo ""
echo "Please get your tokens from:"
echo "https://developers.line.biz/console/"
echo ""

read -p "Enter your LINE Channel Access Token: " TOKEN
read -p "Enter your LINE Channel Secret: " SECRET
read -p "Enter your LIFF ID (optional): " LIFF

# Create .env file
cat > .env << EOF
LINE_CHANNEL_ACCESS_TOKEN=$TOKEN
LINE_CHANNEL_SECRET=$SECRET
LIFF_ID=$LIFF
EOF

echo ""
echo "✅ Created .env file with your credentials"
echo ""
echo "Now run:"
echo "source .env"
echo "export LINE_CHANNEL_ACCESS_TOKEN LINE_CHANNEL_SECRET LIFF_ID"
echo ""
echo "Then restart the server:"
echo "lsof -ti:5001 | xargs kill -9"
echo "python3 app_liff_integrated.py"