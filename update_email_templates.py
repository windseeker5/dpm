#!/usr/bin/env python3
"""
Update email templates for activity #4 to avoid Gmail Promotions folder
"""
import sqlite3
import json
import os

db_path = os.path.join(os.path.dirname(__file__), 'instance', 'minipass.db')

# New email templates with:
# - No emojis in subjects
# - Simplified transactional titles
# - Enhanced conclusion text
new_templates = {
    "newPass": {
        "subject": "Votre passeport numérique",
        "title": "Votre passeport numérique est disponible",
        "intro_text": "<p>Bonjour <strong>{{ pass_data.user.name }}</strong>,</p>\n<p>Votre passeport numérique vient d'être créé.</p>\n<p>Il vous donne accès à <strong>{{ pass_data.uses_remaining }}</strong> participations pour <strong>{{ pass_data.activity.name }}</strong>.</p>\n{% if pass_data.activity.location_address_formatted %}\n<p>📍 <strong>Lieu :</strong> {{ pass_data.activity.location_address_formatted }}</p>\n{% endif %}\n<p>Présentez simplement le code QR ci-dessous lors de chaque participation.</p>",
        "conclusion_text": "{% if not pass_data.paid %}<p><strong>⚠️ Rappel important :</strong></p>\n<p>Votre passeport n'est pas encore payé. Merci de compléter le paiement de <strong>{{ \"%.2f\"|format(pass_data.sold_amt) }}$</strong> pour activer votre accès.</p>{% endif %}\n<p>&nbsp;</p>\n<p>Merci de faire partie de cette aventure. Si vous avez des questions ou besoin d'assistance, n'hésitez pas à nous contacter directement.</p>\n<p>À très bientôt,<br>\n<em><strong>L'équipe</strong></em></p>",
        "custom_message": "",
        "cta_text": "Voir mon passeport",
        "cta_url": "https://minipass.me/my-passes"
    },
    "paymentReceived": {
        "subject": "Confirmation de paiement",
        "title": "Paiement confirmé",
        "intro_text": "<p>Bonjour <strong>{{ pass_data.user.name }}</strong>,</p>\n<p>Nous avons bien reçu votre paiement de <strong>{{ \"%.2f\"|format(pass_data.sold_amt) }}$</strong>.</p>\n<p>Votre passeport numérique pour <strong>{{ pass_data.activity.name }}</strong> est maintenant actif et prêt à être utilisé.</p>\n{% if pass_data.activity.location_address_formatted %}\n<p>📍 <strong>Lieu :</strong> {{ pass_data.activity.location_address_formatted }}</p>\n{% endif %}\n<p>Il vous reste <strong>{{ pass_data.uses_remaining }}</strong> participations.</p>",
        "conclusion_text": "<p>Merci de votre confiance. Votre passeport est maintenant actif et vous pouvez commencer à l'utiliser dès aujourd'hui.</p>\n<p>Si vous avez des questions ou besoin d'assistance, n'hésitez pas à nous contacter directement. Nous sommes là pour vous aider.</p>\n<p>À très bientôt,<br>\n<em><strong>L'équipe</strong></em></p>",
        "custom_message": "",
        "cta_text": "Voir mon passeport",
        "cta_url": "https://minipass.me/my-passes"
    },
    "latePayment": {
        "subject": "Rappel de paiement en attente",
        "title": "Petit rappel amical",
        "intro_text": "<p>Bonjour <strong>{{ pass_data.user.name }}</strong>,</p>\n<p>Votre passeport numérique pour <strong>{{ pass_data.activity.name }}</strong> est en attente de paiement.</p>\n<p>Pour activer votre accès, merci de compléter le paiement de <strong>{{ \"%.2f\"|format(pass_data.sold_amt) }}$</strong>.</p>\n{% if pass_data.activity.location_address_formatted %}\n<p>📍 <strong>Lieu :</strong> {{ pass_data.activity.location_address_formatted }}</p>\n{% endif %}",
        "conclusion_text": "<p>Si vous avez des questions ou rencontrez un problème concernant le paiement, n'hésitez pas à nous contacter. Nous sommes disponibles pour vous aider.</p>\n<p>Merci de votre compréhension,<br>\n<em><strong>L'équipe</strong></em></p>",
        "custom_message": "",
        "cta_text": "Effectuer le paiement",
        "cta_url": "https://minipass.me/payment"
    },
    "signup": {
        "subject": "Confirmation d'inscription",
        "title": "Inscription confirmée",
        "intro_text": "<p>Bonjour <strong>{{ user_name }}</strong>,</p>\n<p>Votre inscription à <strong>{{ activity_name }}</strong> est confirmée.</p>\n{% if activity.location_address_formatted %}\n<p>📍 <strong>Lieu :</strong> {{ activity.location_address_formatted }}</p>\n{% endif %}\n<p>Dès réception de votre paiement, votre passeport numérique vous sera envoyé automatiquement.</p>",
        "conclusion_text": "<p>Merci de faire partie de cette aventure. Nous sommes impatients de vous accueillir.</p>\n<p>Si vous avez des questions concernant votre inscription ou le processus de paiement, n'hésitez pas à nous contacter.</p>\n<p>À très bientôt,<br>\n<em><strong>L'équipe</strong></em></p>",
        "custom_message": "",
        "cta_text": "Voir les détails",
        "cta_url": "https://minipass.me/my-signups"
    },
    "redeemPass": {
        "subject": "Confirmation de participation",
        "title": "Participation enregistrée",
        "intro_text": "<p>Bonjour <strong>{{ pass_data.user.name }}</strong>,</p>\n<p>Une participation vient d'être utilisée sur votre passeport numérique pour <strong>{{ pass_data.activity.name }}</strong>.</p>\n{% if pass_data.activity.location_address_formatted %}\n<p>📍 <strong>Lieu :</strong> {{ pass_data.activity.location_address_formatted }}</p>\n{% endif %}\n<p><strong>Participations restantes :</strong> {{ pass_data.uses_remaining }}</p>",
        "conclusion_text": "{% if not pass_data.paid %}<p><strong>⚠️ Rappel important :</strong></p>\n<p>Votre passeport n'est pas encore payé. Merci de compléter le paiement de <strong>{{ \"%.2f\"|format(pass_data.sold_amt) }}$</strong> pour continuer à profiter de vos participations.</p>{% endif %}\n<p>&nbsp;</p>\n<p>Merci de faire partie de cette aventure. Nous espérons que vous appréciez votre expérience.</p>\n<p>N'hésitez pas à nous contacter si vous avez des questions concernant vos participations restantes ou tout autre sujet.</p>\n<p>À très bientôt,<br>\n<em><strong>L'équipe</strong></em></p>",
        "custom_message": "",
        "cta_text": "Voir mon passeport",
        "cta_url": "https://minipass.me/my-passes"
    },
    "survey_invitation": {
        "subject": "Votre avis nous intéresse",
        "title": "Nous aimerions connaître votre avis",
        "intro_text": "<p>Bonjour,</p>\n<p>Vous avez récemment participé à <strong>{{ activity_name }}</strong> et nous aimerions connaître votre avis.</p>\n<p>Quelques minutes suffisent pour répondre à notre sondage. Vos commentaires nous aident à améliorer nos services.</p>\n{% if activity.location_address_formatted %}\n<p>📍 <strong>Lieu :</strong> {{ activity.location_address_formatted }}</p>\n{% endif %}",
        "conclusion_text": "<p>Merci d'avance pour votre temps et vos précieux commentaires. Votre opinion compte beaucoup pour nous.</p>\n<p>Si vous avez des questions ou souhaitez nous contacter directement, n'hésitez pas à nous écrire.</p>\n<p>Cordialement,<br>\n<em><strong>L'équipe</strong></em></p>",
        "custom_message": "",
        "cta_text": "Répondre au sondage",
        "cta_url": "{survey_url}"
    }
}

print("🔧 Updating email templates for activity #4...")
print(f"📁 Database: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Get current templates
    cursor.execute("SELECT email_templates FROM activity WHERE id = 4")
    result = cursor.fetchone()

    if not result or not result[0]:
        print("❌ No existing templates found for activity #4")
        exit(1)

    print("✅ Found existing templates")

    # Update with new templates
    cursor.execute(
        "UPDATE activity SET email_templates = ? WHERE id = 4",
        (json.dumps(new_templates, ensure_ascii=False),)
    )

    conn.commit()
    print("✅ Successfully updated email templates!")
    print("\n📋 Changes made:")
    print("  • Removed ALL emojis from subject lines")
    print("  • Simplified titles to be transactional")
    print("  • Enhanced conclusion text (2-3 more sentences)")
    print("  • Kept functional emoji 📍 for location")
    print("\n🎯 Ready to test!")

except Exception as e:
    print(f"❌ Error: {e}")
    conn.rollback()
    raise
finally:
    conn.close()
