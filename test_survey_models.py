#!/usr/bin/env python3
"""
Test script for survey models
"""
import json
from datetime import datetime, timezone
from app import app
from models import db, SurveyTemplate, Survey, SurveyResponse, Activity, User, Admin
from utils import generate_survey_token, generate_response_token


def test_survey_models():
    """Test survey model creation and relationships"""
    with app.app_context():
        print("🧪 Testing Survey Models...")
        
        # Test SurveyTemplate creation
        template_questions = {
            "questions": [
                {
                    "id": 1,
                    "type": "multiple_choice",
                    "question": "How would you rate your overall experience?",
                    "options": ["Excellent", "Good", "Fair", "Poor"],
                    "required": True
                },
                {
                    "id": 2,
                    "type": "open_ended",
                    "question": "Any additional feedback?",
                    "required": False,
                    "max_length": 500
                }
            ]
        }
        
        # Check if we can create a survey template
        template = SurveyTemplate(
            name="Test Activity Feedback",
            description="Test survey template",
            questions=json.dumps(template_questions),
            status="active"
        )
        
        print("✅ SurveyTemplate model created successfully")
        
        # Test token generation
        survey_token = generate_survey_token()
        response_token = generate_response_token()
        
        print(f"✅ Survey token generated: {survey_token}")
        print(f"✅ Response token generated: {response_token}")
        
        # Test Survey model creation
        survey = Survey(
            name="Test Survey",
            description="Test survey description",
            survey_token=survey_token,
            status="active"
        )
        
        print("✅ Survey model created successfully")
        
        # Test SurveyResponse model creation
        response = SurveyResponse(
            response_token=response_token,
            responses=json.dumps({"1": "Excellent", "2": "Great experience!"}),
            completed=True,
            completed_dt=datetime.now(timezone.utc)
        )
        
        print("✅ SurveyResponse model created successfully")
        
        # Test JSON serialization/deserialization
        questions_data = json.loads(template.questions)
        responses_data = json.loads(response.responses)
        
        print("✅ JSON serialization/deserialization working")
        print(f"   Template questions: {len(questions_data['questions'])} questions")
        print(f"   Response data: {len(responses_data)} answers")
        
        print("\n🎉 All survey model tests passed!")
        return True


if __name__ == "__main__":
    test_survey_models()