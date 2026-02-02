"""
Email Template Defaults Manager
This module handles loading and providing default email templates for new activities.
"""

import json
import os

def get_default_email_templates():
    """
    Load default email templates from the config file.
    
    Returns:
        dict: Dictionary containing default email templates for all types
    """
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'email_defaults.json')
    
    # If config file doesn't exist, return minimal defaults
    if not os.path.exists(config_path):
        return {
            'newPass': {
                'subject': 'Your Digital Pass is Ready!',
                'title': 'Welcome!',
                'intro_text': '<p>Your digital pass has been created.</p>',
                'conclusion_text': '<p>Thank you!</p>',
                'custom_message': '',
                'cta_text': 'View Pass',
                'cta_url': 'https://minipass.me/my-passes'
            },
            'paymentReceived': {
                'subject': 'Payment Received',
                'title': 'Payment Confirmed',
                'intro_text': '<p>We have received your payment.</p>',
                'conclusion_text': '<p>Thank you!</p>',
                'custom_message': ''
            },
            'latePayment': {
                'subject': 'Payment Reminder',
                'title': 'Payment Reminder',
                'intro_text': '<p>You have a pending payment.</p>',
                'conclusion_text': '<p>Thank you!</p>',
                'custom_message': ''
            },
            'signup': {
                'subject': 'Registration Confirmed',
                'title': 'Welcome!',
                'intro_text': '<p>Your registration is confirmed.</p>',
                'conclusion_text': '<p>Thank you!</p>',
                'custom_message': ''
            },
            'signup_payment_first': {
                'subject': 'Registration Confirmed - Payment Instructions',
                'title': 'Registration Confirmed',
                'intro_text': '<p>Your registration is confirmed. Please complete payment.</p>',
                'conclusion_text': '<p>Thank you!</p>',
                'custom_message': ''
            },
            'redeemPass': {
                'subject': 'Pass Redeemed',
                'title': 'Enjoy!',
                'intro_text': '<p>Your pass has been redeemed.</p>',
                'conclusion_text': '<p>Thank you!</p>',
                'custom_message': ''
            },
            'survey_invitation': {
                'subject': 'We Value Your Feedback',
                'title': 'Share Your Experience',
                'intro_text': '<p>Please share your feedback.</p>',
                'conclusion_text': '<p>Thank you!</p>',
                'custom_message': '',
                'cta_text': 'Take Survey',
                'cta_url': '{survey_url}'
            }
        }
    
    # Load from config file
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading email defaults: {e}")
        # Return the minimal defaults if there's an error
        return get_default_email_templates.__defaults__[0] if hasattr(get_default_email_templates, '__defaults__') else {}


def update_default_email_templates(new_defaults):
    """
    Update the default email templates in the config file.
    
    Args:
        new_defaults (dict): New default templates to save
    
    Returns:
        bool: True if successful, False otherwise
    """
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'email_defaults.json')
    
    try:
        # Ensure config directory exists
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        # Save the new defaults
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(new_defaults, f, ensure_ascii=False, indent=4)
        
        return True
    except Exception as e:
        print(f"Error saving email defaults: {e}")
        return False