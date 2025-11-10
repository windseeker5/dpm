#!/usr/bin/env python3
"""
Script to create 13 test activities for tier 2 testing.
This will create realistic activities with full details.
"""

from datetime import datetime, timezone
from app import app, db
from models import Activity, Admin

def create_test_activities():
    """Create 13 realistic test activities."""

    with app.app_context():
        # Get the first admin user
        admin = Admin.query.first()
        if not admin:
            print("ERROR: No admin user found in database!")
            print("Please create an admin user first.")
            return

        print(f"Creating activities for admin: {admin.email} (ID: {admin.id})")
        print("-" * 60)

        # Define 13 diverse test activities with realistic data
        test_activities = [
            {
                "name": "Winter Hockey League",
                "type": "hockey",
                "description": "Competitive adult hockey league running throughout the winter season. All skill levels welcome.",
                "start_date": datetime(2025, 11, 1, tzinfo=timezone.utc),
                "end_date": datetime(2026, 3, 31, tzinfo=timezone.utc),
                "goal_revenue": 8000.0
            },
            {
                "name": "Summer Basketball Camp",
                "type": "basketball",
                "description": "Intensive basketball skills camp for youth ages 8-14. Focus on fundamentals and team play.",
                "start_date": datetime(2025, 7, 1, tzinfo=timezone.utc),
                "end_date": datetime(2025, 8, 31, tzinfo=timezone.utc),
                "goal_revenue": 5000.0
            },
            {
                "name": "Morning Yoga Sessions",
                "type": "yoga",
                "description": "Relaxing morning yoga classes for all experience levels. Focus on flexibility and mindfulness.",
                "start_date": datetime(2025, 9, 1, tzinfo=timezone.utc),
                "end_date": datetime(2026, 6, 30, tzinfo=timezone.utc),
                "goal_revenue": 3500.0
            },
            {
                "name": "Competitive Swim Team",
                "type": "swimming",
                "description": "Year-round competitive swimming program for ages 6-18. Train for regional competitions.",
                "start_date": datetime(2025, 9, 15, tzinfo=timezone.utc),
                "end_date": datetime(2026, 6, 15, tzinfo=timezone.utc),
                "goal_revenue": 6000.0
            },
            {
                "name": "Youth Soccer League",
                "type": "soccer",
                "description": "Spring soccer league for kids ages 5-12. Focus on skill development and fun.",
                "start_date": datetime(2025, 4, 1, tzinfo=timezone.utc),
                "end_date": datetime(2025, 6, 30, tzinfo=timezone.utc),
                "goal_revenue": 4500.0
            },
            {
                "name": "Tennis Tournament Series",
                "type": "tennis",
                "description": "Monthly tennis tournament series for intermediate and advanced players.",
                "start_date": datetime(2025, 5, 1, tzinfo=timezone.utc),
                "end_date": datetime(2025, 10, 31, tzinfo=timezone.utc),
                "goal_revenue": 3000.0
            },
            {
                "name": "CrossFit Bootcamp",
                "type": "fitness",
                "description": "High-intensity CrossFit training program. 12-week transformation challenge.",
                "start_date": datetime(2025, 10, 1, tzinfo=timezone.utc),
                "end_date": datetime(2025, 12, 31, tzinfo=timezone.utc),
                "goal_revenue": 4000.0
            },
            {
                "name": "Kids Gymnastics",
                "type": "gymnastics",
                "description": "Gymnastics classes for children ages 3-10. Build strength, flexibility, and coordination.",
                "start_date": datetime(2025, 9, 1, tzinfo=timezone.utc),
                "end_date": datetime(2026, 5, 31, tzinfo=timezone.utc),
                "goal_revenue": 5500.0
            },
            {
                "name": "Adult Volleyball League",
                "type": "volleyball",
                "description": "Recreational volleyball league for adults. Teams of 6, weekly games.",
                "start_date": datetime(2025, 6, 1, tzinfo=timezone.utc),
                "end_date": datetime(2025, 9, 30, tzinfo=timezone.utc),
                "goal_revenue": 3200.0
            },
            {
                "name": "Figure Skating Program",
                "type": "skating",
                "description": "Figure skating lessons and performance program. All ages and skill levels.",
                "start_date": datetime(2025, 10, 15, tzinfo=timezone.utc),
                "end_date": datetime(2026, 3, 15, tzinfo=timezone.utc),
                "goal_revenue": 7000.0
            },
            {
                "name": "Boxing Training Camp",
                "type": "boxing",
                "description": "Boxing training camp for fitness and competition. Focus on technique and conditioning.",
                "start_date": datetime(2025, 8, 1, tzinfo=timezone.utc),
                "end_date": datetime(2025, 11, 30, tzinfo=timezone.utc),
                "goal_revenue": 4200.0
            },
            {
                "name": "Ultimate Frisbee League",
                "type": "frisbee",
                "description": "Co-ed ultimate frisbee league. Fun, competitive games every weekend.",
                "start_date": datetime(2025, 5, 15, tzinfo=timezone.utc),
                "end_date": datetime(2025, 8, 31, tzinfo=timezone.utc),
                "goal_revenue": 2500.0
            },
            {
                "name": "Martial Arts Classes",
                "type": "martial_arts",
                "description": "Traditional martial arts training for all ages. Build discipline, fitness, and self-defense skills.",
                "start_date": datetime(2025, 9, 1, tzinfo=timezone.utc),
                "end_date": datetime(2026, 8, 31, tzinfo=timezone.utc),
                "goal_revenue": 6500.0
            }
        ]

        created_count = 0

        for activity_data in test_activities:
            try:
                # Create activity with all details
                activity = Activity(
                    name=activity_data["name"],
                    type=activity_data["type"],
                    description=activity_data["description"],
                    start_date=activity_data["start_date"],
                    end_date=activity_data["end_date"],
                    status="active",
                    created_by=admin.id,
                    goal_revenue=activity_data["goal_revenue"]
                )

                db.session.add(activity)
                db.session.commit()

                created_count += 1
                print(f"✓ Created: {activity.name} (ID: {activity.id})")
                print(f"  Type: {activity.type} | Revenue Goal: ${activity.goal_revenue:,.2f}")
                print(f"  Duration: {activity.start_date.strftime('%Y-%m-%d')} to {activity.end_date.strftime('%Y-%m-%d')}")
                print()

            except Exception as e:
                print(f"✗ Failed to create: {activity_data['name']}")
                print(f"  Error: {str(e)}")
                print()
                db.session.rollback()

        print("-" * 60)
        print(f"Summary: Successfully created {created_count} out of 13 test activities")

        # Count total activities
        total_activities = Activity.query.filter_by(created_by=admin.id).count()
        print(f"Total activities for admin {admin.email}: {total_activities}")
        print()
        print("You can now test tier 2 (15 activity limit)!")

if __name__ == "__main__":
    create_test_activities()
