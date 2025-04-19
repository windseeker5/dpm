from models import db, User, Activity, Pass

# 1. Create dummy Activity
activity = Activity(
    name="Legacy Hockey Activity",
    type="hockey",
    sessions_included=4,
    price_per_user=50.0,
    description="Auto-imported from previous system",
)
db.session.add(activity)
db.session.commit()

# 2. Convert flat user data to User rows
passes = Pass.query.all()
user_cache = {}

for p in passes:
    key = (p.user_name.strip().lower(), p.user_email.strip().lower())
    if key not in user_cache:
        user = User(name=p.user_name.strip(), email=p.user_email.strip(), phone_number=p.phone_number)
        db.session.add(user)
        db.session.flush()
        user_cache[key] = user.id
    p.user_id = user_cache[key]
    p.activity_id = activity.id
    p.uses_remaining = p.games_remaining

db.session.commit()
