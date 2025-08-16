-- SQL script to add default Post-Activity Feedback template
-- Run this in the SQLite database

-- Check if template already exists before inserting
INSERT INTO survey_template (
    name,
    description,
    questions,
    created_by,
    created_dt,
    status
)
SELECT 
    'Post-Activity Feedback',
    'A universal feedback template suitable for any activity type. Collect essential feedback about satisfaction, instructor performance, and areas for improvement.',
    '{"questions": [{"id": 1, "text": "How would you rate your overall satisfaction with this activity?", "type": "rating", "required": true, "options": {"min": 1, "max": 5, "labels": {"1": "Very Dissatisfied", "2": "Dissatisfied", "3": "Neutral", "4": "Satisfied", "5": "Very Satisfied"}}}, {"id": 2, "text": "How would you rate the instructor/facilitator?", "type": "rating", "required": true, "options": {"min": 1, "max": 5, "labels": {"1": "Poor", "2": "Fair", "3": "Good", "4": "Very Good", "5": "Excellent"}}}, {"id": 3, "text": "What did you enjoy most about this activity?", "type": "text", "required": false, "options": {"placeholder": "Please share what you enjoyed...", "maxLength": 500}}, {"id": 4, "text": "What aspects could be improved?", "type": "text", "required": false, "options": {"placeholder": "Your suggestions help us improve...", "maxLength": 500}}, {"id": 5, "text": "Would you recommend this activity to others?", "type": "radio", "required": true, "options": {"choices": [{"value": "yes", "label": "Yes, definitely!"}, {"value": "maybe", "label": "Maybe"}, {"value": "no", "label": "No"}]}}], "settings": {"showProgress": true, "allowSkip": false, "randomizeQuestions": false, "estimatedTime": "2-3 minutes"}}',
    1,
    datetime('now'),
    'active'
WHERE NOT EXISTS (
    SELECT 1 FROM survey_template WHERE name = 'Post-Activity Feedback'
);