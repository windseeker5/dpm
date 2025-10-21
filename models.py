# models.py (UPDATED - TIMEZONE AWARE)
import uuid
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone   
 


# ✅ Define db here (not in app.py)
db = SQLAlchemy()


class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=True)  # Added for personalization
    last_name = db.Column(db.String(50), nullable=True)   # Added for personalization
    avatar_filename = db.Column(db.String(255), nullable=True)  # For custom avatar uploads
    
    @property
    def full_name(self):
        """Get full name, falling back to email if names not set"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.email.split('@')[0]  # Use email prefix as fallback
    
    @property
    def display_name(self):
        """Get display name for welcome messages"""
        if self.first_name:
            return self.first_name
        else:
            return self.email.split('@')[0]  # Use email prefix as fallback


class AdminActionLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    admin_email = db.Column(db.String(150))
    action = db.Column(db.Text)



# This should be deleted ....
class Pass(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pass_code = db.Column(db.String(16), unique=True, nullable=False)
    user_name = db.Column(db.String(100), nullable=False)
    user_email = db.Column(db.String(100), nullable=False)
    sold_amt = db.Column(db.Float, default=50)
    games_remaining = db.Column(db.Integer, default=4)
    phone_number = db.Column(db.String(20), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey("admin.id"))
    # pass_created_dt = db.Column(db.DateTime, default=datetime.now(timezone.utc))  # ✅ UTC-aware

    pass_created_dt = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)  # ✅ FIXED!
    )

    paid_ind = db.Column(db.Boolean, default=False)
    paid_date = db.Column(db.DateTime, nullable=True)  # ✅ manually set with UTC
    activity = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    # in models.py (Pass model)
    marked_paid_by = db.Column(db.String(120), nullable=True)

 



# ✅ Generalized SaaS models (non-conflicting with current Pass logic)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    # email = db.Column(db.String(100), unique=True)

    phone_number = db.Column(db.String(20))
    
    # Email preferences
    email_opt_out = db.Column(db.Boolean, default=False, nullable=False)
    
    # Organization relationship for email context
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=True)

    signups = db.relationship("Signup", backref="user", lazy=True)
    passports = db.relationship("Passport", backref="user", lazy=True)




class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    type = db.Column(db.String(50))  # e.g., "hockey", "yoga"
    description = db.Column(db.Text)
    start_date = db.Column(db.DateTime, nullable=True)
    end_date = db.Column(db.DateTime, nullable=True)
    image_filename = db.Column(db.String(255), nullable=True)
    logo_filename = db.Column(db.String(255), nullable=True)  # Activity-specific logo for email templates
    created_by = db.Column(db.Integer, db.ForeignKey("admin.id"))
    created_dt = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    status = db.Column(db.String(50), default="active")
    
    # Email template customizations (JSON)
    email_templates = db.Column(db.JSON, nullable=True)
    
    # Organization relationship for email context
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=True)

    # Location fields for geospatial data and sharing
    location_address_raw = db.Column(db.Text, nullable=True)  # What admin typed
    location_address_formatted = db.Column(db.Text, nullable=True)  # Google's corrected/formatted address
    location_coordinates = db.Column(db.String(100), nullable=True)  # "lat,lng" for shareable map links

    signups = db.relationship("Signup", backref="activity", lazy=True)
    passports = db.relationship("Passport", backref="activity", lazy=True)


class PassportType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    activity_id = db.Column(db.Integer, db.ForeignKey("activity.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)  # e.g., "Regular", "Substitute"
    type = db.Column(db.String(50), nullable=False)   # "permanent" or "substitute"
    price_per_user = db.Column(db.Float, default=0.0)
    sessions_included = db.Column(db.Integer, default=1)
    target_revenue = db.Column(db.Float, default=0.0)
    payment_instructions = db.Column(db.Text)
    created_dt = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    status = db.Column(db.String(50), default="active")  # "active", "archived", "deleted"
    archived_at = db.Column(db.DateTime, nullable=True)
    archived_by = db.Column(db.String(120), nullable=True)
    
    activity = db.relationship("Activity", backref="passport_types")


class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    activity_id = db.Column(db.Integer, db.ForeignKey("activity.id"), nullable=False)
    date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    category = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    created_by = db.Column(db.String(100))  # admin email or name
    receipt_filename = db.Column(db.String(255), nullable=True)

    activity = db.relationship("Activity", backref="expenses")



class Income(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    activity_id = db.Column(db.Integer, db.ForeignKey("activity.id"), nullable=False)
    date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    category = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    note = db.Column(db.Text)
    created_by = db.Column(db.String(100))  # admin email or name

    receipt_filename = db.Column(db.String(255), nullable=True)  # ✅ Add this

    activity = db.relationship("Activity", backref="incomes")







class Signup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey("activity.id"), nullable=False)
    passport_type_id = db.Column(db.Integer, db.ForeignKey("passport_type.id"), nullable=True)  # Added for passport type tracking
    subject = db.Column(db.String(200))
    description = db.Column(db.Text)
    form_url = db.Column(db.String(500))
    form_data = db.Column(db.Text)  # JSON string
    signed_up_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    paid = db.Column(db.Boolean, default=False)
    paid_at = db.Column(db.DateTime)
    passport_id = db.Column(db.Integer, db.ForeignKey("passport.id"))
    status = db.Column(db.String(50), default="pending")


class Passport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pass_code = db.Column(db.String(16), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey("activity.id"), nullable=False)
    passport_type_id = db.Column(db.Integer, db.ForeignKey("passport_type.id"), nullable=True)  # New field
    passport_type_name = db.Column(db.String(100), nullable=True)  # Preserved type name for historical display
    sold_amt = db.Column(db.Float, default=0.0)
    uses_remaining = db.Column(db.Integer, default=0)
    created_by = db.Column(db.Integer, db.ForeignKey("admin.id"))
    created_dt = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    paid = db.Column(db.Boolean, default=False)
    paid_date = db.Column(db.DateTime)
    marked_paid_by = db.Column(db.String(120))
    notes = db.Column(db.Text)

    # Relationships (user and activity are defined via backrefs on User and Activity models)
    signups = db.relationship("Signup", backref="passport", lazy=True)
    passport_type = db.relationship("PassportType", backref="passports")



class Redemption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    passport_id = db.Column(db.Integer, db.ForeignKey("passport.id"), nullable=False)  # 🟢 FIXED
    date_used = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    redeemed_by = db.Column(db.String(100), nullable=True)



class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)


class EbankPayment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.now(timezone.utc))  # ✅ UTC-aware
    from_email = db.Column(db.String(150))
    subject = db.Column(db.Text)
    bank_info_name = db.Column(db.String(100))
    bank_info_amt = db.Column(db.Float)
    matched_pass_id = db.Column(db.Integer, db.ForeignKey("pass.id"), nullable=True)
    matched_name = db.Column(db.String(100))
    matched_amt = db.Column(db.Float)
    name_score = db.Column(db.Integer)
    result = db.Column(db.String(50))
    mark_as_paid = db.Column(db.Boolean, default=False)
    note = db.Column(db.Text, nullable=True)



class ReminderLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pass_id = db.Column(db.Integer, db.ForeignKey("pass.id"), nullable=False)
    reminder_sent_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class EmailLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    to_email = db.Column(db.String(150), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    pass_code = db.Column(db.String(16), nullable=True)
    template_name = db.Column(db.String(100), nullable=True)
    context_json = db.Column(db.Text)
    result = db.Column(db.String(50))  # SENT or FAILED
    error_message = db.Column(db.Text, nullable=True)


# ✅ Place index right after the model class
db.Index('ix_signup_status', Signup.status)


# ================================
# 📋 SURVEY SYSTEM MODELS
# ================================

class SurveyTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    questions = db.Column(db.Text)  # JSON string containing questions
    created_by = db.Column(db.Integer, db.ForeignKey("admin.id"))
    created_dt = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    status = db.Column(db.String(50), default="active")  # active, archived
    
    # Relationships
    surveys = db.relationship("Survey", backref="template", lazy=True)


class Survey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    activity_id = db.Column(db.Integer, db.ForeignKey("activity.id"), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey("survey_template.id"), nullable=False)
    passport_type_id = db.Column(db.Integer, db.ForeignKey("passport_type.id"), nullable=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    survey_token = db.Column(db.String(32), unique=True, nullable=False)  # For URL generation
    created_by = db.Column(db.Integer, db.ForeignKey("admin.id"))
    created_dt = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    status = db.Column(db.String(50), default="active")  # active, closed, archived
    email_sent = db.Column(db.Boolean, default=False)
    email_sent_dt = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    activity = db.relationship("Activity", backref="surveys")
    passport_type = db.relationship("PassportType", backref="surveys")
    responses = db.relationship("SurveyResponse", backref="survey", lazy=True)


class SurveyResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    survey_id = db.Column(db.Integer, db.ForeignKey("survey.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    passport_id = db.Column(db.Integer, db.ForeignKey("passport.id"), nullable=True)
    response_token = db.Column(db.String(32), unique=True, nullable=False)
    responses = db.Column(db.Text)  # JSON string containing all answers
    completed = db.Column(db.Boolean, default=False)
    completed_dt = db.Column(db.DateTime, nullable=True)
    started_dt = db.Column(db.DateTime, nullable=True)  # When user first accessed survey
    invited_dt = db.Column(db.DateTime, nullable=True)  # When invitation was sent
    created_dt = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))  # When record was created
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    
    # Relationships
    user = db.relationship("User", backref="survey_responses")
    passport = db.relationship("Passport", backref="survey_responses")


# ✅ Survey indexes for performance
db.Index('ix_survey_token', Survey.survey_token)
db.Index('ix_survey_response_token', SurveyResponse.response_token)
db.Index('ix_survey_activity', Survey.activity_id)
db.Index('ix_survey_response_survey', SurveyResponse.survey_id)


# ================================
# 🤖 AI CHATBOT SYSTEM MODELS
# ================================

class ChatConversation(db.Model):
    """Chat conversation sessions for the AI analytics chatbot"""
    id = db.Column(db.Integer, primary_key=True)
    admin_email = db.Column(db.String(150), nullable=False)
    session_token = db.Column(db.String(32), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    status = db.Column(db.String(20), default='active')  # active, archived, deleted
    
    # Relationships
    messages = db.relationship("ChatMessage", backref="conversation", lazy=True, cascade="all, delete-orphan")


class ChatMessage(db.Model):
    """Individual chat messages and AI responses"""
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey("chat_conversation.id"), nullable=False)
    message_type = db.Column(db.String(20), nullable=False)  # user, assistant, system, error
    content = db.Column(db.Text, nullable=False)
    sql_query = db.Column(db.Text, nullable=True)  # Generated SQL (if applicable)
    query_result = db.Column(db.Text, nullable=True)  # JSON result (if applicable)
    ai_provider = db.Column(db.String(50), nullable=True)  # ollama, anthropic, openai
    ai_model = db.Column(db.String(100), nullable=True)  # Model used for this message
    tokens_used = db.Column(db.Integer, default=0)
    cost_cents = db.Column(db.Integer, default=0)  # Cost in cents
    response_time_ms = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Index for performance
    __table_args__ = (
        db.Index('ix_chat_message_conversation', 'conversation_id'),
        db.Index('ix_chat_message_type', 'message_type'),
        db.Index('ix_chat_message_created', 'created_at'),
    )


class QueryLog(db.Model):
    """Query execution log for monitoring and analytics"""
    id = db.Column(db.Integer, primary_key=True)
    admin_email = db.Column(db.String(150), nullable=False)
    original_question = db.Column(db.Text, nullable=False)
    generated_sql = db.Column(db.Text, nullable=False)
    execution_status = db.Column(db.String(20), nullable=False)  # success, error, blocked
    execution_time_ms = db.Column(db.Integer, nullable=True)
    rows_returned = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text, nullable=True)
    ai_provider = db.Column(db.String(50), nullable=True)
    ai_model = db.Column(db.String(100), nullable=True)
    tokens_used = db.Column(db.Integer, default=0)
    cost_cents = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Indexes for performance and analytics
    __table_args__ = (
        db.Index('ix_query_log_admin', 'admin_email'),
        db.Index('ix_query_log_status', 'execution_status'),
        db.Index('ix_query_log_created', 'created_at'),
        db.Index('ix_query_log_provider', 'ai_provider'),
    )


class ChatUsage(db.Model):
    """Daily usage tracking for cost management"""
    id = db.Column(db.Integer, primary_key=True)
    admin_email = db.Column(db.String(150), nullable=False)
    date = db.Column(db.Date, nullable=False)
    total_queries = db.Column(db.Integer, default=0)
    total_tokens = db.Column(db.Integer, default=0)
    total_cost_cents = db.Column(db.Integer, default=0)
    provider_usage = db.Column(db.Text, nullable=True)  # JSON with per-provider stats
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Unique constraint on admin_email + date
    __table_args__ = (
        db.UniqueConstraint('admin_email', 'date', name='uq_chat_usage_admin_date'),
        db.Index('ix_chat_usage_date', 'date'),
    )


# Organization Model for Multi-tenant Email Settings
class Organization(db.Model):
    """Organization model to support multi-tenant email configurations"""
    __tablename__ = 'organizations'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    domain = db.Column(db.String(100), unique=True, nullable=False)  # e.g., 'lhgi' from lhgi@minipass.me
    
    # Email Configuration
    email_enabled = db.Column(db.Boolean, default=False)
    mail_server = db.Column(db.String(255), nullable=True)  # e.g., 'mail.minipass.me'
    mail_port = db.Column(db.Integer, default=587)
    mail_use_tls = db.Column(db.Boolean, default=True)
    mail_use_ssl = db.Column(db.Boolean, default=False)
    mail_username = db.Column(db.String(255), nullable=True)  # e.g., 'lhgi@minipass.me'
    mail_password = db.Column(db.String(500), nullable=True)  # Encrypted password
    mail_sender_name = db.Column(db.String(255), nullable=True)  # e.g., 'LHGI'
    mail_sender_email = db.Column(db.String(255), nullable=True)  # Override sender email if different
    
    # Additional settings
    is_active = db.Column(db.Boolean, default=True)
    fallback_to_system_email = db.Column(db.Boolean, default=True)  # Fallback to system Gmail if org email fails
    
    # Audit fields
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    created_by = db.Column(db.String(255), nullable=True)
    updated_by = db.Column(db.String(255), nullable=True)
    
    # Relationships
    activities = db.relationship('Activity', backref='organization', lazy=True)
    users = db.relationship('User', backref='organization', lazy=True)
    
    def __repr__(self):
        return f'<Organization {self.name} ({self.domain})>'
    
    @property
    def full_email_address(self):
        """Get the full email address for this organization"""
        return f"{self.domain}@minipass.me"
    
    def get_email_config(self):
        """Get email configuration as dictionary"""
        if not self.email_enabled:
            return None
        
        return {
            'MAIL_SERVER': self.mail_server,
            'MAIL_PORT': self.mail_port,
            'MAIL_USE_TLS': self.mail_use_tls,
            'MAIL_USE_SSL': self.mail_use_ssl,
            'MAIL_USERNAME': self.mail_username,
            'MAIL_PASSWORD': self.mail_password,
            'MAIL_DEFAULT_SENDER': self.mail_sender_email or self.full_email_address,
            'SENDER_NAME': self.mail_sender_name or self.name
        }


# ✅ Additional indexes for chatbot performance
db.Index('ix_chat_conversation_admin', ChatConversation.admin_email)
db.Index('ix_chat_conversation_token', ChatConversation.session_token)
db.Index('ix_chat_conversation_status', ChatConversation.status)