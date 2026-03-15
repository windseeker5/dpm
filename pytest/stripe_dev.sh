#!/bin/bash
# Stripe local dev helper
# - Grabs the webhook signing secret from stripe listen
# - Updates the local SQLite DB automatically
# - Starts forwarding to localhost:5000/stripe/webhook

DB="/home/kdresdell/Documents/DEV/minipass_env/app/instance/minipass.db"
FORWARD_URL="localhost:5000/stripe/webhook"

echo "[stripe_dev] Fetching webhook signing secret..."
SECRET=$(stripe listen --print-secret 2>/dev/null)

if [ -z "$SECRET" ]; then
  echo "[stripe_dev] ERROR: Could not get secret. Is stripe CLI installed and logged in?"
  exit 1
fi

echo "[stripe_dev] Got secret: $SECRET"
echo "[stripe_dev] Updating database..."

sqlite3 "$DB" "UPDATE setting SET value='$SECRET' WHERE key='STRIPE_WEBHOOK_SECRET';"

if [ $? -ne 0 ]; then
  echo "[stripe_dev] ERROR: Failed to update database."
  exit 1
fi

echo "[stripe_dev] DB updated. Starting stripe listen -> $FORWARD_URL"
echo ""

stripe listen --forward-to "$FORWARD_URL"
