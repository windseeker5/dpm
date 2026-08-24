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
    reset_token = db.Column(db.String(255), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)
    
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


class PushSubscription(db.Model):
    """Stores push notification subscriptions for admins"""
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("admin.id", ondelete="CASCADE"), nullable=False)
    endpoint = db.Column(db.Text, nullable=False, unique=True)  # Push service URL
    p256dh_key = db.Column(db.Text, nullable=False)  # Public key for encryption
    auth_key = db.Column(db.Text, nullable=False)  # Auth secret
    user_agent = db.Column(db.String(255), nullable=True)  # Browser/device info
    created_dt = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_used_dt = db.Column(db.DateTime, nullable=True)  # Track last successful push

    # Relationships
    admin = db.relationship("Admin", backref="push_subscriptions")

    __table_args__ = (
        db.Index('ix_push_subscription_admin', 'admin_id'),
    )




# ✅ Generalized SaaS models (non-conflicting with current Pass logic)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    # email = db.Column(db.String(100), unique=True)

    phone_number = db.Column(db.String(20))
    
    # Email preferences
    email_opt_out = db.Column(db.Boolean, default=False, nullable=False)

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
    offer_passport_renewal = db.Column(db.Boolean, default=False, nullable=False)

    # Email template customizations (JSON)
    email_templates = db.Column(db.JSON, nullable=True)

    # Location fields for geospatial data and sharing
    location_address_raw = db.Column(db.Text, nullable=True)  # What admin typed
    location_address_formatted = db.Column(db.Text, nullable=True)  # Google's corrected/formatted address
    location_coordinates = db.Column(db.String(100), nullable=True)  # "lat,lng" for shareable map links

    # Financial tracking
    goal_revenue = db.Column(db.Float, default=0.0, nullable=True)  # Revenue goal for progress tracking (existing column)

    # Workflow configuration
    workflow_type = db.Column(db.String(50), default="approval_first")  # "approval_first" | "payment_first"
    allow_quantity_selection = db.Column(db.Boolean, default=False)     # Show qty picker on signup

    # Quantity limits
    is_quantity_limited = db.Column(db.Boolean, default=False)
    max_sessions = db.Column(db.Integer, nullable=True)                 # Total capacity
    show_remaining_quantity = db.Column(db.Boolean, default=False)      # Display "X left" on form

    # Session scheduling (dated slots with per-slot seats). Gates ALL scheduling behaviour:
    # when False the activity behaves exactly as it did before the feature existed.
    # When True, ActivitySlot.capacity governs availability and max_sessions is ignored
    # (see utils.get_remaining_capacity).
    uses_scheduling = db.Column(db.Boolean, default=False, nullable=False, server_default="0")

    # Stripe credit card payments
    accept_credit_card = db.Column(db.Boolean, default=False)

    # Discord integration
    discord_webhook_url = db.Column(db.String(500), nullable=True)
    discord_invite_url = db.Column(db.String(500), nullable=True)

    signups = db.relationship("Signup", backref="activity", lazy=True)
    passports = db.relationship("Passport", backref="activity", lazy=True)

    def get_inherited_activity_ids(self):
        """IDs of activities whose passports this activity's dashboard may view/act on. One hop only."""
        return [link.source_activity_id for link in self.inherited_links]


class ActivityPassportInheritance(db.Model):
    """
    Directed link: `activity` (the dashboard being viewed) may act on passports
    that natively belong to `source_activity`. Non-transitive (one hop only —
    if A inherits from B and B inherits from C, A does NOT get C's passports).
    No passport/user/redemption rows are ever created by this table; it only
    expands query scope in activity_dashboard and preserves redirect context
    in the passport action endpoints.
    """
    __tablename__ = "activity_passport_inheritance"

    id = db.Column(db.Integer, primary_key=True)
    activity_id = db.Column(db.Integer, db.ForeignKey("activity.id", ondelete="CASCADE"), nullable=False)
    source_activity_id = db.Column(db.Integer, db.ForeignKey("activity.id", ondelete="CASCADE"), nullable=False)
    created_dt = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    created_by = db.Column(db.Integer, db.ForeignKey("admin.id"), nullable=True)

    __table_args__ = (
        db.UniqueConstraint("activity_id", "source_activity_id", name="uq_activity_inheritance_pair"),
    )

    activity = db.relationship(
        "Activity", foreign_keys=[activity_id],
        backref=db.backref("inherited_links", cascade="all, delete-orphan"),
    )
    source_activity = db.relationship("Activity", foreign_keys=[source_activity_id])


class PassportType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    activity_id = db.Column(db.Integer, db.ForeignKey("activity.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)  # e.g., "Regular", "Substitute"
    type = db.Column(db.String(50), nullable=False)   # "permanent" or "substitute"
    price_per_user = db.Column(db.Float, default=0.0)
    sessions_included = db.Column(db.Integer, default=1)
    target_revenue = db.Column(db.Float, default=0.0)
    payment_instructions = db.Column(db.Text)
    use_custom_payment_instructions = db.Column(db.Boolean, default=False, nullable=False)
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

    # Payment tracking fields (Cash Flow Accounting)
    payment_status = db.Column(db.String(20), default="paid")
    # Values: "unpaid", "paid", "cancelled"

    payment_date = db.Column(db.DateTime, nullable=True)
    # Actual date payment was made

    due_date = db.Column(db.DateTime, nullable=True)
    # When unpaid bill is due

    payment_method = db.Column(db.String(50), nullable=True)
    # Values: "e-transfer", "cash", "cheque", "credit_card", "other"

    stripe_transaction_id = db.Column(db.Integer, db.ForeignKey('stripe_transaction.id'), nullable=True)

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

    # Payment tracking fields (Cash Flow Accounting)
    payment_status = db.Column(db.String(20), default="received")
    # Values: "pending", "received", "cancelled"

    payment_date = db.Column(db.DateTime, nullable=True)
    # Actual date payment was received

    payment_method = db.Column(db.String(50), nullable=True)
    # Values: "e-transfer", "cash", "cheque", "credit_card", "other"

    activity = db.relationship("Activity", backref="incomes")







class StripeTransaction(db.Model):
    __tablename__ = "stripe_transaction"
    id           = db.Column(db.Integer, primary_key=True)
    session_id   = db.Column(db.String(100), unique=True, nullable=True)   # Checkout session
    charge_id    = db.Column(db.String(100), nullable=True)                 # Stripe charge ID
    payout_id    = db.Column(db.String(100), nullable=True)                 # Stripe payout ID
    gross_amount = db.Column(db.Float, nullable=False)                      # Full customer charge
    stripe_fee   = db.Column(db.Float, nullable=True)                       # 2.9% + $0.30
    net_amount   = db.Column(db.Float, nullable=True)                       # Deposited to bank
    charge_date  = db.Column(db.DateTime, nullable=False)
    payout_date  = db.Column(db.DateTime, nullable=True)
    status       = db.Column(db.String(20), default="pending")              # pending | paid_out | refunded
    created_at   = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    # Links
    signup_id    = db.Column(db.Integer, db.ForeignKey("signup.id"),   nullable=True)
    passport_id  = db.Column(db.Integer, db.ForeignKey("passport.id"), nullable=True)
    income_id    = db.Column(db.Integer, db.ForeignKey("income.id"),   nullable=True)  # Income to update on payout
    signup   = db.relationship("Signup",   backref="stripe_transactions")
    passport = db.relationship("Passport", backref="stripe_transactions")


class Signup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey("activity.id"), nullable=False)
    passport_type_id = db.Column(db.Integer, db.ForeignKey("passport_type.id", ondelete="SET NULL"), nullable=True)  # Added for passport type tracking
    subject = db.Column(db.String(200))
    description = db.Column(db.Text)
    form_url = db.Column(db.String(500))
    form_data = db.Column(db.Text)  # JSON string
    signed_up_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    paid = db.Column(db.Boolean, default=False)
    paid_at = db.Column(db.DateTime)
    passport_id = db.Column(db.Integer, db.ForeignKey("passport.id", ondelete="SET NULL"))
    status = db.Column(db.String(50), default="pending")

    # Quantity selection for payment-first workflow
    requested_sessions = db.Column(db.Integer, default=1)    # User's chosen quantity
    requested_amount = db.Column(db.Float, default=0.0)      # Calculated total (price x qty)

    # Signup code for reliable payment matching (format: MP-INS-0001234)
    signup_code = db.Column(db.String(20), unique=True, nullable=True)

    # Stripe credit card payment fields
    payment_method = db.Column(db.String(20), default="interac")  # "interac" or "stripe"
    stripe_checkout_session_id = db.Column(db.String(255), nullable=True)

    # Session scheduling: the held/confirmed seat for this signup, if the activity uses
    # scheduling. One-to-one (enforced by UNIQUE(signup_id) on slot_booking). Deliberately
    # NOT a Signup.slot_id column — a second source of truth would drift on cancel/rebook.
    slot_booking = db.relationship("SlotBooking", backref="signup", uselist=False, lazy=True)


class Passport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pass_code = db.Column(db.String(16), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey("activity.id"), nullable=False)
    passport_type_id = db.Column(db.Integer, db.ForeignKey("passport_type.id", ondelete="SET NULL"), nullable=True)  # New field
    passport_type_name = db.Column(db.String(100), nullable=True)  # Preserved type name for historical display
    sold_amt = db.Column(db.Float, default=0.0)
    uses_remaining = db.Column(db.Integer, default=0)
    created_by = db.Column(db.Integer, db.ForeignKey("admin.id"))
    created_dt = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    paid = db.Column(db.Boolean, default=False)
    paid_date = db.Column(db.DateTime)
    marked_paid_by = db.Column(db.String(120))
    notes = db.Column(db.Text)
    payment_method = db.Column(db.String(50), nullable=True)
    # Values: "stripe", "interac", "cash", "pos", "cheque"
    # NULL = legacy/unknown (historical passports)

    # Relationships (user and activity are defined via backrefs on User and Activity models)
    signups = db.relationship("Signup", backref="passport", lazy=True)
    passport_type = db.relationship("PassportType", backref="passports")



class Redemption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    passport_id = db.Column(db.Integer, db.ForeignKey("passport.id", ondelete="CASCADE"), nullable=False)
    date_used = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    redeemed_by = db.Column(db.String(100), nullable=True)
    # Soft reference (not a FK, same convention as EmailLog.pass_code) to the activity whose
    # dashboard this redemption was performed from, only set when it differs from the passport's
    # native activity_id (i.e. redeemed via cross-activity passport inheritance).
    context_activity_id = db.Column(db.Integer, nullable=True)


# ================================
# 📅 SESSION SCHEDULING MODELS
# ================================
# Naming note: these are called "Sessions" in the UI, but NEVER `Session` in code —
# that name collides with Flask's `session` object and with the credit fields
# `sessions_included` / `requested_sessions` / `max_sessions`, which all mean CREDITS.
# Here, a "slot" is a dated occurrence with seats; a "credit" is still a credit.

class ActivitySlot(db.Model):
    """One dated occurrence of an activity, with a hard seat limit.

    Only meaningful when the parent Activity has uses_scheduling=True.
    """
    __tablename__ = "activity_slot"

    id = db.Column(db.Integer, primary_key=True)
    activity_id = db.Column(db.Integer, db.ForeignKey("activity.id", ondelete="CASCADE"),
                            nullable=False, index=True)

    # ⚠️ NAIVE LOCAL WALL-CLOCK — same convention as Activity.start_date/end_date and the
    # <input type="datetime-local"> fields in activity_form.html. NEVER compare these to
    # datetime.now(timezone.utc); use datetime.now() (naive) for "is this slot in the future".
    # Every other datetime on this model is UTC-aware. Do not mix them.
    starts_at = db.Column(db.DateTime, nullable=False)
    ends_at = db.Column(db.DateTime, nullable=True)

    capacity = db.Column(db.Integer, nullable=False, default=1)
    # ⚠️ seats_taken is the ADMISSION CONTROL variable, not a cache of COUNT(bookings).
    # It is only ever mutated by conditional UPDATE statements (see utils.claim_slot_seat).
    # Never do `slot.seats_taken += 1` through the ORM — that is a lost-update race.
    seats_taken = db.Column(db.Integer, nullable=False, default=0, server_default="0")

    label = db.Column(db.String(120), nullable=True)   # Optional admin override of the display name
    status = db.Column(db.String(20), nullable=False, default="active", server_default="active")
    # Values: "active" | "cancelled". Never hard-delete a slot that has bookings.

    created_dt = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))  # UTC-aware
    created_by = db.Column(db.Integer, db.ForeignKey("admin.id"), nullable=True)

    # passive_deletes=True stops SQLAlchemy trying to NULL out activity_id when the parent
    # Activity is deleted (which fails, since the column is NOT NULL). Deletion is handled
    # explicitly in delete_activity, with the DB-level ON DELETE CASCADE as the backstop.
    activity = db.relationship(
        "Activity",
        backref=db.backref("slots", passive_deletes=True),
        passive_deletes=True,
    )

    __table_args__ = (
        # Makes slot generation idempotent: a double-clicked "Generate" or a re-submitted
        # form cannot create duplicate slots. Also forbids parallel tracks at the same
        # time, which is an accepted and deliberate limitation.
        db.UniqueConstraint("activity_id", "starts_at", name="uq_activity_slot_start"),
        db.Index("ix_activity_slot_activity_status_start", "activity_id", "status", "starts_at"),
        # Last line of defence against a counter bug silently overselling.
        db.CheckConstraint("seats_taken >= 0", name="ck_activity_slot_seats_nonneg"),
        db.CheckConstraint("seats_taken <= capacity", name="ck_activity_slot_seats_le_cap"),
    )

    @property
    def seats_left(self):
        return max(0, (self.capacity or 0) - (self.seats_taken or 0))

    @property
    def is_full(self):
        return self.seats_left <= 0


class SlotBooking(db.Model):
    """A seat reserved in an ActivitySlot — the ledger behind ActivitySlot.seats_taken.

    Lifecycle:  held ──► confirmed ──► cancelled
                     └─► expired ───► cancelled

    The row IS the seat hold. It is created in the same transaction as the Signup,
    BEFORE any Passport exists (a passport may not appear for days on the Interac +
    admin-approval path), which is why passport_id is nullable.
    """
    __tablename__ = "slot_booking"

    id = db.Column(db.Integer, primary_key=True)
    slot_id = db.Column(db.Integer, db.ForeignKey("activity_slot.id", ondelete="CASCADE"),
                        nullable=False, index=True)
    # Denormalised so admin lists can filter by activity without joining through activity_slot.
    activity_id = db.Column(db.Integer, db.ForeignKey("activity.id", ondelete="CASCADE"),
                            nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # The seat is held by the signup first; the passport is bound later, on creation.
    signup_id = db.Column(db.Integer, db.ForeignKey("signup.id", ondelete="SET NULL"), nullable=True)
    passport_id = db.Column(db.Integer, db.ForeignKey("passport.id", ondelete="SET NULL"), nullable=True)

    status = db.Column(db.String(20), nullable=False, default="held", server_default="held")
    # Values: "held" | "confirmed" | "expired" | "cancelled".
    # "expired" is recoverable (a late e-transfer can re-claim the seat); "cancelled" is terminal.

    # Makes refunds idempotent — without this a double-cancel would refund two credits.
    credit_consumed = db.Column(db.Boolean, nullable=False, default=False, server_default="0")
    held_until = db.Column(db.DateTime, nullable=True)  # UTC-aware; NULL once confirmed

    created_dt = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    confirmed_dt = db.Column(db.DateTime, nullable=True)
    cancelled_dt = db.Column(db.DateTime, nullable=True)
    cancelled_reason = db.Column(db.String(50), nullable=True)

    # Set when the admin checks this person in for this session (UTC, naive as stored).
    # NULL = booked but not yet attended. This is what makes check-in idempotent: a scan
    # fulfils an unattended booking (no credit taken, it was paid at booking time), whereas
    # a scan with no unattended booking is a walk-in and DOES cost a credit.
    attended_dt = db.Column(db.DateTime, nullable=True)

    # Same reasoning as ActivitySlot.activity: slot_id is NOT NULL, so the ORM must not
    # try to nullify it when a slot is deleted.
    slot = db.relationship(
        "ActivitySlot",
        backref=db.backref("bookings", passive_deletes=True),
        lazy=True,
        passive_deletes=True,
    )
    user = db.relationship("User", backref="slot_bookings")
    passport = db.relationship("Passport", backref="slot_bookings")

    __table_args__ = (
        db.Index("ix_slot_booking_slot_status", "slot_id", "status"),
        db.Index("ix_slot_booking_expiry", "status", "held_until"),   # drives the expiry sweeper
        db.Index("ix_slot_booking_passport", "passport_id"),
        # One slot per signup, enforced at the DB level. SQLite treats NULLs as distinct,
        # so admin-created bookings (signup_id IS NULL) are unaffected.
        db.UniqueConstraint("signup_id", name="uq_slot_booking_signup"),
        # One passport cannot hold two live seats in the same slot.
        db.Index("uq_slot_booking_passport_slot", "passport_id", "slot_id", unique=True,
                 sqlite_where=db.text("passport_id IS NOT NULL AND status IN ('held','confirmed')")),
    )


class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)


class EbankPayment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))  # ✅ UTC-aware (when bot processed)
    from_email = db.Column(db.String(150))
    reply_to_email = db.Column(db.String(150))  # Real sender from Reply-To header
    subject = db.Column(db.Text)
    bank_info_name = db.Column(db.String(100))
    bank_info_amt = db.Column(db.Float)
    matched_pass_id = db.Column(db.Integer, db.ForeignKey("passport.id", ondelete="SET NULL"), nullable=True)  # ✅ Fixed to reference passport table
    matched_name = db.Column(db.String(100))
    matched_amt = db.Column(db.Float)
    name_score = db.Column(db.Integer)
    result = db.Column(db.String(50))
    mark_as_paid = db.Column(db.Boolean, default=False)
    note = db.Column(db.Text, nullable=True)
    email_received_date = db.Column(db.DateTime, nullable=True)  # When payment email was actually received
    email_uid = db.Column(db.String(50), nullable=True)  # IMAP UID for moving email later



class ReminderLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    passport_id = db.Column(db.Integer, db.ForeignKey("passport.id", ondelete="CASCADE"), nullable=False)  # ✅ Fixed to reference passport table
    reminder_sent_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class EmailLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    to_email = db.Column(db.String(150), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    pass_code = db.Column(db.String(16), nullable=True)
    template_name = db.Column(db.String(100), nullable=True)
    context_json = db.Column(db.Text)
    result = db.Column(db.String(50))  # SENT or FAILED
    error_message = db.Column(db.Text, nullable=True)


class AnnouncementLog(db.Model):
    __tablename__ = 'announcement_log'
    id              = db.Column(db.Integer, primary_key=True)
    activity_id     = db.Column(db.Integer, db.ForeignKey('activity.id'), nullable=False)
    sent_at         = db.Column(db.DateTime(timezone=True), nullable=False)
    subject         = db.Column(db.String(150), nullable=False)
    message         = db.Column(db.Text, nullable=False)
    sent_by         = db.Column(db.String(200))
    recipient_count = db.Column(db.Integer, default=0)


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
    passport_type_id = db.Column(db.Integer, db.ForeignKey("passport_type.id", ondelete="SET NULL"), nullable=True)
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
    survey_id = db.Column(db.Integer, db.ForeignKey("survey.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    passport_id = db.Column(db.Integer, db.ForeignKey("passport.id", ondelete="SET NULL"), nullable=True)
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
    ai_answer = db.Column(db.Text, nullable=True)  # Natural language answer returned to user
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
