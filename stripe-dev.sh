#!/usr/bin/env bash
# stripe-dev.sh — Start stripe listen and auto-update STRIPE_WEBHOOK_SECRET in local DB

DB="instance/minipass.db"
FLASK_URL="localhost:5000/stripe/webhook"

echo "🔌 Starting Stripe listener → $FLASK_URL"
echo ""

# Start stripe listen, capture output line by line
stripe listen --forward-to "$FLASK_URL" 2>&1 | while IFS= read -r line; do
    echo "$line"

    # Detect the webhook signing secret line
    if echo "$line" | grep -q "webhook signing secret is"; then
        SECRET=$(echo "$line" | grep -o 'whsec_[A-Za-z0-9]*')
        if [ -n "$SECRET" ]; then
            echo ""
            echo "✅ Got secret: $SECRET"
            echo "   Updating STRIPE_WEBHOOK_SECRET in $DB ..."
            sqlite3 "$DB" "UPDATE setting SET value='$SECRET' WHERE key='STRIPE_WEBHOOK_SECRET';"
            echo "   Done. Flask will now accept webhooks."
            echo ""
        fi
    fi
done
