from utils import send_email
from datetime import datetime

# Dummy test values
user_email = "ken.dresdell@telus.com"   # 🔁 Replace with your test email
user_name = "Jean-Martin Morin"
pass_code = "abc123xyz789"
created_date = datetime.now().strftime('%Y-%m-%d')
remaining_games = 4

# Optional special message
special_message = "🎉 This is a test email for your hockey pass!"

# Send test email
send_email(
    user_email=user_email,
    subject="📬 Test Email - Hockey Pass Preview",
    user_name=user_name,
    pass_code=pass_code,
    created_date=created_date,
    remaining_games=remaining_games,
    special_message=special_message
)
