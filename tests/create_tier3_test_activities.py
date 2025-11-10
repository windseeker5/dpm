#!/usr/bin/env python3
"""
Script to create 84 additional test activities for tier 3 testing.
This will create realistic activities with full details.
"""

from datetime import datetime, timezone
from app import app, db
from models import Activity, Admin

def create_tier3_test_activities():
    """Create 84 realistic test activities for tier 3 testing."""

    with app.app_context():
        # Get the first admin user
        admin = Admin.query.first()
        if not admin:
            print("ERROR: No admin user found in database!")
            print("Please create an admin user first.")
            return

        print(f"Creating 84 activities for admin: {admin.email} (ID: {admin.id})")
        print("-" * 60)

        # Define 84 diverse test activities with realistic data
        test_activities = [
            # Sports Leagues (20)
            {"name": "Spring Baseball League", "type": "baseball", "description": "Competitive spring baseball league for adults. Games twice weekly.", "start_date": datetime(2025, 4, 1, tzinfo=timezone.utc), "end_date": datetime(2025, 7, 31, tzinfo=timezone.utc), "goal_revenue": 5500.0},
            {"name": "Fall Softball League", "type": "softball", "description": "Co-ed softball league. Fun, competitive atmosphere.", "start_date": datetime(2025, 9, 1, tzinfo=timezone.utc), "end_date": datetime(2025, 11, 30, tzinfo=timezone.utc), "goal_revenue": 4200.0},
            {"name": "Indoor Soccer Winter League", "type": "soccer", "description": "Indoor soccer for all ages. Winter season competition.", "start_date": datetime(2025, 12, 1, tzinfo=timezone.utc), "end_date": datetime(2026, 2, 28, tzinfo=timezone.utc), "goal_revenue": 6000.0},
            {"name": "Beach Volleyball Summer Series", "type": "volleyball", "description": "Outdoor beach volleyball tournament series.", "start_date": datetime(2025, 6, 1, tzinfo=timezone.utc), "end_date": datetime(2025, 8, 31, tzinfo=timezone.utc), "goal_revenue": 3800.0},
            {"name": "Flag Football League", "type": "football", "description": "Non-contact flag football league for adults.", "start_date": datetime(2025, 9, 15, tzinfo=timezone.utc), "end_date": datetime(2025, 12, 15, tzinfo=timezone.utc), "goal_revenue": 4500.0},
            {"name": "Rugby Development Program", "type": "rugby", "description": "Youth rugby skills and development program.", "start_date": datetime(2025, 5, 1, tzinfo=timezone.utc), "end_date": datetime(2025, 10, 31, tzinfo=timezone.utc), "goal_revenue": 5200.0},
            {"name": "Lacrosse Spring Season", "type": "lacrosse", "description": "Spring lacrosse league for youth ages 10-16.", "start_date": datetime(2025, 3, 15, tzinfo=timezone.utc), "end_date": datetime(2025, 6, 30, tzinfo=timezone.utc), "goal_revenue": 4800.0},
            {"name": "Field Hockey League", "type": "field_hockey", "description": "Competitive field hockey for women and girls.", "start_date": datetime(2025, 8, 1, tzinfo=timezone.utc), "end_date": datetime(2025, 11, 30, tzinfo=timezone.utc), "goal_revenue": 4000.0},
            {"name": "Badminton Club", "type": "badminton", "description": "Weekly badminton club with coaching and play time.", "start_date": datetime(2025, 9, 1, tzinfo=timezone.utc), "end_date": datetime(2026, 5, 31, tzinfo=timezone.utc), "goal_revenue": 2800.0},
            {"name": "Pickleball Tournament Series", "type": "pickleball", "description": "Monthly pickleball tournaments for all skill levels.", "start_date": datetime(2025, 4, 1, tzinfo=timezone.utc), "end_date": datetime(2025, 10, 31, tzinfo=timezone.utc), "goal_revenue": 3200.0},
            {"name": "Squash Club Championship", "type": "squash", "description": "Competitive squash club with weekly ladder matches.", "start_date": datetime(2025, 10, 1, tzinfo=timezone.utc), "end_date": datetime(2026, 4, 30, tzinfo=timezone.utc), "goal_revenue": 3500.0},
            {"name": "Table Tennis League", "type": "table_tennis", "description": "Indoor table tennis league with tournament play.", "start_date": datetime(2025, 11, 1, tzinfo=timezone.utc), "end_date": datetime(2026, 3, 31, tzinfo=timezone.utc), "goal_revenue": 2500.0},
            {"name": "Curling Club Winter Season", "type": "curling", "description": "Traditional curling club winter league.", "start_date": datetime(2025, 10, 15, tzinfo=timezone.utc), "end_date": datetime(2026, 3, 15, tzinfo=timezone.utc), "goal_revenue": 4200.0},
            {"name": "Bowling League Night", "type": "bowling", "description": "Weekly bowling league with team competition.", "start_date": datetime(2025, 9, 1, tzinfo=timezone.utc), "end_date": datetime(2026, 4, 30, tzinfo=timezone.utc), "goal_revenue": 3600.0},
            {"name": "Golf Tournament Series", "type": "golf", "description": "Monthly golf tournaments at local courses.", "start_date": datetime(2025, 5, 1, tzinfo=timezone.utc), "end_date": datetime(2025, 10, 31, tzinfo=timezone.utc), "goal_revenue": 6500.0},
            {"name": "Disc Golf League", "type": "disc_golf", "description": "Casual disc golf league with weekly rounds.", "start_date": datetime(2025, 4, 15, tzinfo=timezone.utc), "end_date": datetime(2025, 10, 15, tzinfo=timezone.utc), "goal_revenue": 2200.0},
            {"name": "Dodgeball League", "type": "dodgeball", "description": "Adult dodgeball league for fun and competition.", "start_date": datetime(2025, 9, 1, tzinfo=timezone.utc), "end_date": datetime(2025, 12, 31, tzinfo=timezone.utc), "goal_revenue": 3000.0},
            {"name": "Kickball Summer League", "type": "kickball", "description": "Co-ed kickball league with after-game socials.", "start_date": datetime(2025, 5, 15, tzinfo=timezone.utc), "end_date": datetime(2025, 8, 31, tzinfo=timezone.utc), "goal_revenue": 3400.0},
            {"name": "Water Polo Club", "type": "water_polo", "description": "Competitive water polo training and matches.", "start_date": datetime(2025, 6, 1, tzinfo=timezone.utc), "end_date": datetime(2025, 9, 30, tzinfo=timezone.utc), "goal_revenue": 4500.0},
            {"name": "Handball League", "type": "handball", "description": "Team handball league for intermediate players.", "start_date": datetime(2025, 10, 1, tzinfo=timezone.utc), "end_date": datetime(2026, 3, 31, tzinfo=timezone.utc), "goal_revenue": 3800.0},

            # Fitness Classes (15)
            {"name": "HIIT Training Sessions", "type": "fitness", "description": "High-intensity interval training for all fitness levels.", "start_date": datetime(2025, 9, 1, tzinfo=timezone.utc), "end_date": datetime(2026, 6, 30, tzinfo=timezone.utc), "goal_revenue": 4000.0},
            {"name": "Spin Class Series", "type": "cycling", "description": "Indoor cycling classes with energetic instructors.", "start_date": datetime(2025, 9, 1, tzinfo=timezone.utc), "end_date": datetime(2026, 5, 31, tzinfo=timezone.utc), "goal_revenue": 3500.0},
            {"name": "Pilates Mat Classes", "type": "pilates", "description": "Core-focused pilates classes for strength and flexibility.", "start_date": datetime(2025, 9, 1, tzinfo=timezone.utc), "end_date": datetime(2026, 6, 30, tzinfo=timezone.utc), "goal_revenue": 3200.0},
            {"name": "Barre Fitness", "type": "barre", "description": "Ballet-inspired fitness classes for toning and sculpting.", "start_date": datetime(2025, 9, 15, tzinfo=timezone.utc), "end_date": datetime(2026, 5, 31, tzinfo=timezone.utc), "goal_revenue": 3400.0},
            {"name": "Zumba Dance Fitness", "type": "dance", "description": "Fun dance fitness classes with Latin-inspired music.", "start_date": datetime(2025, 9, 1, tzinfo=timezone.utc), "end_date": datetime(2026, 6, 30, tzinfo=timezone.utc), "goal_revenue": 2800.0},
            {"name": "Boot Camp Training", "type": "bootcamp", "description": "Military-style outdoor fitness boot camp.", "start_date": datetime(2025, 5, 1, tzinfo=timezone.utc), "end_date": datetime(2025, 10, 31, tzinfo=timezone.utc), "goal_revenue": 3600.0},
            {"name": "Strength Training Program", "type": "strength", "description": "Progressive strength training for muscle building.", "start_date": datetime(2025, 9, 1, tzinfo=timezone.utc), "end_date": datetime(2026, 5, 31, tzinfo=timezone.utc), "goal_revenue": 4200.0},
            {"name": "Core & Abs Workshop", "type": "core", "description": "Focused core strengthening and abdominal training.", "start_date": datetime(2025, 10, 1, tzinfo=timezone.utc), "end_date": datetime(2025, 12, 31, tzinfo=timezone.utc), "goal_revenue": 2500.0},
            {"name": "Stretching & Mobility", "type": "flexibility", "description": "Improve flexibility and joint mobility with guided stretching.", "start_date": datetime(2025, 9, 1, tzinfo=timezone.utc), "end_date": datetime(2026, 6, 30, tzinfo=timezone.utc), "goal_revenue": 2400.0},
            {"name": "TRX Suspension Training", "type": "trx", "description": "Full-body resistance training using TRX suspension systems.", "start_date": datetime(2025, 9, 15, tzinfo=timezone.utc), "end_date": datetime(2026, 5, 31, tzinfo=timezone.utc), "goal_revenue": 3800.0},
            {"name": "Kettlebell Classes", "type": "kettlebell", "description": "Dynamic kettlebell workouts for strength and cardio.", "start_date": datetime(2025, 9, 1, tzinfo=timezone.utc), "end_date": datetime(2026, 6, 30, tzinfo=timezone.utc), "goal_revenue": 3200.0},
            {"name": "Indoor Rowing Program", "type": "rowing", "description": "Full-body cardio and strength on rowing machines.", "start_date": datetime(2025, 10, 1, tzinfo=timezone.utc), "end_date": datetime(2026, 4, 30, tzinfo=timezone.utc), "goal_revenue": 3000.0},
            {"name": "Senior Fitness Classes", "type": "senior_fitness", "description": "Gentle fitness classes designed for active seniors.", "start_date": datetime(2025, 9, 1, tzinfo=timezone.utc), "end_date": datetime(2026, 6, 30, tzinfo=timezone.utc), "goal_revenue": 2600.0},
            {"name": "Prenatal Fitness", "type": "prenatal", "description": "Safe fitness classes for expectant mothers.", "start_date": datetime(2025, 9, 1, tzinfo=timezone.utc), "end_date": datetime(2026, 6, 30, tzinfo=timezone.utc), "goal_revenue": 2800.0},
            {"name": "Postnatal Recovery", "type": "postnatal", "description": "Postpartum fitness and recovery program for new moms.", "start_date": datetime(2025, 9, 1, tzinfo=timezone.utc), "end_date": datetime(2026, 6, 30, tzinfo=timezone.utc), "goal_revenue": 2800.0},

            # Martial Arts & Combat Sports (12)
            {"name": "Karate for Kids", "type": "karate", "description": "Traditional karate training for children ages 5-12.", "start_date": datetime(2025, 9, 1, tzinfo=timezone.utc), "end_date": datetime(2026, 6, 30, tzinfo=timezone.utc), "goal_revenue": 4500.0},
            {"name": "Brazilian Jiu-Jitsu", "type": "bjj", "description": "Ground fighting and grappling techniques for all levels.", "start_date": datetime(2025, 9, 1, tzinfo=timezone.utc), "end_date": datetime(2026, 8, 31, tzinfo=timezone.utc), "goal_revenue": 5500.0},
            {"name": "Muay Thai Kickboxing", "type": "muay_thai", "description": "Traditional Thai boxing with striking techniques.", "start_date": datetime(2025, 9, 1, tzinfo=timezone.utc), "end_date": datetime(2026, 6, 30, tzinfo=timezone.utc), "goal_revenue": 5000.0},
            {"name": "Taekwondo Classes", "type": "taekwondo", "description": "Korean martial art focusing on kicks and forms.", "start_date": datetime(2025, 9, 1, tzinfo=timezone.utc), "end_date": datetime(2026, 6, 30, tzinfo=timezone.utc), "goal_revenue": 4200.0},
            {"name": "Judo Training Program", "type": "judo", "description": "Olympic judo training with throws and grappling.", "start_date": datetime(2025, 9, 1, tzinfo=timezone.utc), "end_date": datetime(2026, 6, 30, tzinfo=timezone.utc), "goal_revenue": 4800.0},
            {"name": "Krav Maga Self Defense", "type": "krav_maga", "description": "Practical self-defense and combat techniques.", "start_date": datetime(2025, 9, 15, tzinfo=timezone.utc), "end_date": datetime(2026, 5, 31, tzinfo=timezone.utc), "goal_revenue": 5200.0},
            {"name": "MMA Training Camp", "type": "mma", "description": "Mixed martial arts training combining multiple disciplines.", "start_date": datetime(2025, 9, 1, tzinfo=timezone.utc), "end_date": datetime(2026, 6, 30, tzinfo=timezone.utc), "goal_revenue": 6000.0},
            {"name": "Kung Fu Classes", "type": "kung_fu", "description": "Traditional Chinese martial arts training.", "start_date": datetime(2025, 9, 1, tzinfo=timezone.utc), "end_date": datetime(2026, 6, 30, tzinfo=timezone.utc), "goal_revenue": 4500.0},
            {"name": "Aikido Practice", "type": "aikido", "description": "Japanese martial art emphasizing harmony and flow.", "start_date": datetime(2025, 9, 1, tzinfo=timezone.utc), "end_date": datetime(2026, 6, 30, tzinfo=timezone.utc), "goal_revenue": 4000.0},
            {"name": "Capoeira Classes", "type": "capoeira", "description": "Brazilian martial art combining dance, music, and acrobatics.", "start_date": datetime(2025, 9, 1, tzinfo=timezone.utc), "end_date": datetime(2026, 6, 30, tzinfo=timezone.utc), "goal_revenue": 3800.0},
            {"name": "Women's Self Defense", "type": "self_defense", "description": "Practical self-defense techniques for women.", "start_date": datetime(2025, 10, 1, tzinfo=timezone.utc), "end_date": datetime(2025, 12, 31, tzinfo=timezone.utc), "goal_revenue": 3500.0},
            {"name": "Fencing Club", "type": "fencing", "description": "Olympic-style fencing with foil, epee, and sabre.", "start_date": datetime(2025, 9, 1, tzinfo=timezone.utc), "end_date": datetime(2026, 5, 31, tzinfo=timezone.utc), "goal_revenue": 5000.0},

            # Aquatics Programs (8)
            {"name": "Swim Lessons for Beginners", "type": "swimming", "description": "Learn to swim program for children and adults.", "start_date": datetime(2025, 6, 1, tzinfo=timezone.utc), "end_date": datetime(2025, 8, 31, tzinfo=timezone.utc), "goal_revenue": 4500.0},
            {"name": "Advanced Swim Techniques", "type": "swimming", "description": "Stroke refinement and competitive swimming skills.", "start_date": datetime(2025, 9, 1, tzinfo=timezone.utc), "end_date": datetime(2026, 5, 31, tzinfo=timezone.utc), "goal_revenue": 5000.0},
            {"name": "Aqua Aerobics", "type": "aqua_fitness", "description": "Low-impact water aerobics for all fitness levels.", "start_date": datetime(2025, 9, 1, tzinfo=timezone.utc), "end_date": datetime(2026, 6, 30, tzinfo=timezone.utc), "goal_revenue": 3200.0},
            {"name": "Lifeguard Certification", "type": "lifeguard", "description": "Lifeguard training and certification program.", "start_date": datetime(2025, 5, 15, tzinfo=timezone.utc), "end_date": datetime(2025, 6, 30, tzinfo=timezone.utc), "goal_revenue": 3800.0},
            {"name": "Synchronized Swimming", "type": "synchro", "description": "Artistic synchronized swimming program.", "start_date": datetime(2025, 9, 1, tzinfo=timezone.utc), "end_date": datetime(2026, 5, 31, tzinfo=timezone.utc), "goal_revenue": 5200.0},
            {"name": "Scuba Diving Course", "type": "scuba", "description": "Open water scuba certification course.", "start_date": datetime(2025, 6, 1, tzinfo=timezone.utc), "end_date": datetime(2025, 7, 31, tzinfo=timezone.utc), "goal_revenue": 6500.0},
            {"name": "Water Safety Training", "type": "water_safety", "description": "Essential water safety skills for children.", "start_date": datetime(2025, 6, 15, tzinfo=timezone.utc), "end_date": datetime(2025, 8, 31, tzinfo=timezone.utc), "goal_revenue": 2800.0},
            {"name": "Masters Swim Club", "type": "swimming", "description": "Adult competitive swim club with coaching.", "start_date": datetime(2025, 9, 1, tzinfo=timezone.utc), "end_date": datetime(2026, 6, 30, tzinfo=timezone.utc), "goal_revenue": 4200.0},

            # Youth Development (10)
            {"name": "Kids Multi-Sport Camp", "type": "multi_sport", "description": "Summer camp introducing kids to multiple sports.", "start_date": datetime(2025, 7, 1, tzinfo=timezone.utc), "end_date": datetime(2025, 8, 31, tzinfo=timezone.utc), "goal_revenue": 6000.0},
            {"name": "Teen Leadership Program", "type": "leadership", "description": "Leadership development through sports and activities.", "start_date": datetime(2025, 9, 1, tzinfo=timezone.utc), "end_date": datetime(2026, 5, 31, tzinfo=timezone.utc), "goal_revenue": 4500.0},
            {"name": "Little Athletes Program", "type": "preschool", "description": "Sports fundamentals for preschoolers ages 3-5.", "start_date": datetime(2025, 9, 1, tzinfo=timezone.utc), "end_date": datetime(2026, 5, 31, tzinfo=timezone.utc), "goal_revenue": 3800.0},
            {"name": "Junior Golf Academy", "type": "golf", "description": "Golf instruction for juniors ages 8-16.", "start_date": datetime(2025, 5, 1, tzinfo=timezone.utc), "end_date": datetime(2025, 9, 30, tzinfo=timezone.utc), "goal_revenue": 5500.0},
            {"name": "Youth Dance Classes", "type": "dance", "description": "Ballet, jazz, and contemporary dance for kids.", "start_date": datetime(2025, 9, 1, tzinfo=timezone.utc), "end_date": datetime(2026, 6, 30, tzinfo=timezone.utc), "goal_revenue": 4200.0},
            {"name": "Kids Parkour Training", "type": "parkour", "description": "Safe parkour and free-running for children.", "start_date": datetime(2025, 9, 15, tzinfo=timezone.utc), "end_date": datetime(2026, 5, 31, tzinfo=timezone.utc), "goal_revenue": 4000.0},
            {"name": "Youth Cheerleading", "type": "cheerleading", "description": "Cheerleading skills and team performance training.", "start_date": datetime(2025, 9, 1, tzinfo=timezone.utc), "end_date": datetime(2026, 5, 31, tzinfo=timezone.utc), "goal_revenue": 4800.0},
            {"name": "Junior Tennis Program", "type": "tennis", "description": "Tennis skills development for ages 6-14.", "start_date": datetime(2025, 5, 1, tzinfo=timezone.utc), "end_date": datetime(2025, 9, 30, tzinfo=timezone.utc), "goal_revenue": 4500.0},
            {"name": "Kids Climbing Club", "type": "climbing", "description": "Indoor rock climbing for children ages 6-12.", "start_date": datetime(2025, 9, 1, tzinfo=timezone.utc), "end_date": datetime(2026, 6, 30, tzinfo=timezone.utc), "goal_revenue": 4200.0},
            {"name": "Youth Track & Field", "type": "track", "description": "Track and field training and competition for youth.", "start_date": datetime(2025, 4, 15, tzinfo=timezone.utc), "end_date": datetime(2025, 8, 31, tzinfo=timezone.utc), "goal_revenue": 3800.0},

            # Wellness & Mind-Body (9)
            {"name": "Meditation & Mindfulness", "type": "meditation", "description": "Guided meditation and mindfulness practice sessions.", "start_date": datetime(2025, 9, 1, tzinfo=timezone.utc), "end_date": datetime(2026, 6, 30, tzinfo=timezone.utc), "goal_revenue": 2500.0},
            {"name": "Hot Yoga Classes", "type": "hot_yoga", "description": "Heated yoga studio classes for detox and flexibility.", "start_date": datetime(2025, 9, 1, tzinfo=timezone.utc), "end_date": datetime(2026, 6, 30, tzinfo=timezone.utc), "goal_revenue": 4000.0},
            {"name": "Yin Yoga & Restoration", "type": "yin_yoga", "description": "Gentle, restorative yoga for deep relaxation.", "start_date": datetime(2025, 9, 1, tzinfo=timezone.utc), "end_date": datetime(2026, 6, 30, tzinfo=timezone.utc), "goal_revenue": 3200.0},
            {"name": "Power Vinyasa Flow", "type": "vinyasa", "description": "Dynamic flowing yoga sequences for strength.", "start_date": datetime(2025, 9, 1, tzinfo=timezone.utc), "end_date": datetime(2026, 6, 30, tzinfo=timezone.utc), "goal_revenue": 3500.0},
            {"name": "Tai Chi Classes", "type": "tai_chi", "description": "Ancient Chinese moving meditation for balance and calm.", "start_date": datetime(2025, 9, 1, tzinfo=timezone.utc), "end_date": datetime(2026, 6, 30, tzinfo=timezone.utc), "goal_revenue": 2800.0},
            {"name": "Qigong Practice", "type": "qigong", "description": "Chinese energy cultivation through movement and breath.", "start_date": datetime(2025, 9, 1, tzinfo=timezone.utc), "end_date": datetime(2026, 6, 30, tzinfo=timezone.utc), "goal_revenue": 2600.0},
            {"name": "Breathwork Workshop", "type": "breathwork", "description": "Transformative breathing techniques for wellness.", "start_date": datetime(2025, 10, 1, tzinfo=timezone.utc), "end_date": datetime(2025, 12, 31, tzinfo=timezone.utc), "goal_revenue": 2200.0},
            {"name": "Yoga for Athletes", "type": "yoga", "description": "Yoga designed specifically for athletic recovery.", "start_date": datetime(2025, 9, 1, tzinfo=timezone.utc), "end_date": datetime(2026, 6, 30, tzinfo=timezone.utc), "goal_revenue": 3400.0},
            {"name": "Chair Yoga for Seniors", "type": "chair_yoga", "description": "Gentle chair-based yoga for limited mobility.", "start_date": datetime(2025, 9, 1, tzinfo=timezone.utc), "end_date": datetime(2026, 6, 30, tzinfo=timezone.utc), "goal_revenue": 2400.0},

            # Specialty & Recreation (10)
            {"name": "Adult Hockey Skills Clinic", "type": "hockey", "description": "Improve skating and hockey skills at any age.", "start_date": datetime(2025, 10, 1, tzinfo=timezone.utc), "end_date": datetime(2026, 3, 31, tzinfo=timezone.utc), "goal_revenue": 4500.0},
            {"name": "Recreational Skating", "type": "skating", "description": "Open recreational ice skating sessions.", "start_date": datetime(2025, 11, 1, tzinfo=timezone.utc), "end_date": datetime(2026, 3, 31, tzinfo=timezone.utc), "goal_revenue": 2000.0},
            {"name": "Speed Skating Program", "type": "speed_skating", "description": "Competitive speed skating training.", "start_date": datetime(2025, 11, 1, tzinfo=timezone.utc), "end_date": datetime(2026, 3, 15, tzinfo=timezone.utc), "goal_revenue": 5000.0},
            {"name": "Trampoline Park Sessions", "type": "trampoline", "description": "Fun trampoline fitness and free jump sessions.", "start_date": datetime(2025, 9, 1, tzinfo=timezone.utc), "end_date": datetime(2026, 6, 30, tzinfo=timezone.utc), "goal_revenue": 3600.0},
            {"name": "Skateboarding Lessons", "type": "skateboarding", "description": "Skateboarding skills and tricks for all levels.", "start_date": datetime(2025, 5, 1, tzinfo=timezone.utc), "end_date": datetime(2025, 9, 30, tzinfo=timezone.utc), "goal_revenue": 3200.0},
            {"name": "BMX Bike Training", "type": "bmx", "description": "BMX racing and freestyle bike skills.", "start_date": datetime(2025, 5, 15, tzinfo=timezone.utc), "end_date": datetime(2025, 9, 30, tzinfo=timezone.utc), "goal_revenue": 3800.0},
            {"name": "Mountain Biking Club", "type": "mountain_bike", "description": "Trail riding and mountain bike skills development.", "start_date": datetime(2025, 5, 1, tzinfo=timezone.utc), "end_date": datetime(2025, 10, 31, tzinfo=timezone.utc), "goal_revenue": 4200.0},
            {"name": "Triathlon Training Group", "type": "triathlon", "description": "Swim, bike, run training for triathlon events.", "start_date": datetime(2025, 4, 1, tzinfo=timezone.utc), "end_date": datetime(2025, 9, 30, tzinfo=timezone.utc), "goal_revenue": 6000.0},
            {"name": "Running Club", "type": "running", "description": "Group running training for 5K to marathon.", "start_date": datetime(2025, 4, 1, tzinfo=timezone.utc), "end_date": datetime(2025, 11, 30, tzinfo=timezone.utc), "goal_revenue": 2800.0},
            {"name": "Outdoor Adventure Camp", "type": "outdoor", "description": "Hiking, camping, and outdoor survival skills.", "start_date": datetime(2025, 6, 1, tzinfo=timezone.utc), "end_date": datetime(2025, 8, 31, tzinfo=timezone.utc), "goal_revenue": 5500.0},
        ]

        created_count = 0
        failed_count = 0

        for idx, activity_data in enumerate(test_activities, 1):
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

                # Print progress every 10 activities
                if created_count % 10 == 0:
                    print(f"Progress: {created_count}/84 activities created...")

            except Exception as e:
                failed_count += 1
                print(f"✗ Failed to create: {activity_data['name']}")
                print(f"  Error: {str(e)}")
                db.session.rollback()

        print("-" * 60)
        print(f"✅ Successfully created {created_count} out of 84 test activities")
        if failed_count > 0:
            print(f"❌ Failed to create {failed_count} activities")

        # Count total activities
        total_activities = Activity.query.filter_by(created_by=admin.id).count()
        print(f"Total activities for admin {admin.email}: {total_activities}")
        print()
        print("You can now test tier 3 (100 activity limit)!")

if __name__ == "__main__":
    create_tier3_test_activities()
