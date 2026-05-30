"""
FRAIL Scale Assessment Questions and Options
"""
ILLNESS_OPTIONS = [
    "Angina",
    "Arthritis",
    "Asthma",
    "Stroke",
    "Cancer",
    "Chronic lung disease",
    "Diabetes",
    "Heart attack",
    "Kidney disease",
    "Hypertension",
]

FRAIL_SCALE_SURVEY = {
    "fatigue": {
        "question": "How much of the time during the past 4 weeks did you feel tired?",
        "description": "This question assesses your energy levels over the past month. Feeling tired 'all or most of the time' may indicate fatigue-related frailty.",
        "options": [
            {"value": True, "label": "All or most of the time"},
            {"value": False, "label": "None or some of the time"}
        ]
    },
    "resistance": {
        "question": "By yourself and not using aids, do you have any difficulty walking up 10 steps without resting?",
        "description": "This measures your lower body strength and endurance. Difficulty with stairs may indicate muscle weakness or reduced physical capacity.",
        "options": [
            {"value": True, "label": "Yes"},
            {"value": False, "label": "No"}
        ]
    },
    "ambulation": {
        "question": "By yourself and not using aids, do you have any difficulty walking several hundred yards?",
        "description": "This assesses your walking endurance and mobility. Difficulty walking several hundred yards may indicate reduced physical function.",
        "options": [
            {"value": True, "label": "Yes, I cannot"},
            {"value": False, "label": "No, I can"}
        ]
    },
    "illnesses": {
        "question": "Did a doctor ever tell you that you have the following diagnosis (check all that apply)",
        "description": "This evaluates your disease burden. Having multiple chronic conditions (5 or more) may contribute to frailty and reduced overall health.",
        "options": [
            # The code is correct as it creates a list comprehension that generates dictionary entries
            # for each illness option with the illness as both the value and label
            {"value": i, "label": str(i)} for i in ILLNESS_OPTIONS]
    },
    "loss_of_weight": {
        "question": "Have you had weight loss of >5% from your weight in past year?",
        "description": "Unintentional weight loss of more than 5% in a year may indicate muscle loss, poor nutrition, or underlying health issues.",
        "options": [
            {"value": True, "label": "Yes"},
            {"value": False, "label": "No"}
        ]
    }
}

def get_FRAIL_scale_questions():
    """Return FRAIL scale assessment questions"""
    return FRAIL_SCALE_SURVEY

def calculate_FRAIL_score(responses):
    """Calculate FRAIL scale score (0-5) from responses"""
    score = 0
    
    if responses.get('fatigue', False):
        score += 1
    if responses.get('resistance', False):
        score += 1
    if responses.get('ambulation', False):
        score += 1
    illnesses = responses.get('illnesses')
    if illnesses is not None:
        illness_count = len(illnesses) if isinstance(illnesses, list) else illnesses
        if illness_count >= 5:
            score += 1
    if responses.get('loss_of_weight', False):
        score += 1
        
    return score

def get_frail_assessment(prefer_form=True):
    """Get FRAIL assessment - automatically selects best approach"""
    if prefer_form:
        return get_assessment_form()
    else:
        return get_assessment_redirect()

def start_frail_assessment():
    """Start FRAIL assessment using default approach (form)"""
    return get_assessment_form()

def get_assessment_redirect():
    """Return redirect info for frontend assessment"""
    return {
        "type": "redirect",
        "assessment": "frail_scale",
        "url": "/assessments/frail",
        "message": "I'll redirect you to the FRAIL Scale Assessment page where you can complete all questions at once."
    }

def get_assessment_form():
    """Return interactive form for chatbox"""
    return {
        "type": "form",
        "assessment": "frail_scale",
        "title": "FRAIL Scale Assessment",
        "questions": FRAIL_SCALE_SURVEY,
        "submit_action": "submit_frail_assessment"
    }

def process_assessment_results(responses):
    """Process assessment results and return complete analysis"""
    score = calculate_FRAIL_score(responses)
    interpretation = interpret_FRAIL_score(score)
    
    return {
        "assessment": "frail_scale",
        "responses": responses,
        "score": score,
        "interpretation": interpretation,
        "recommendations": get_frail_recommendations(interpretation["level"])
    }

def get_frail_recommendations(level):
    """Get recommendations based on frailty level"""
    recommendations = {
        "Robust": ["Maintain current activity level", "Continue healthy lifestyle habits"],
        "Pre-frail": ["Increase physical activity", "Consider strength training", "Consult healthcare provider"],
        "Frail": ["Seek medical evaluation", "Consider supervised exercise program", "Review medications with doctor"]
    }
    return recommendations.get(level, [])

def interpret_FRAIL_score(score):
    """Interpret FRAIL scale score"""
    if score == 0:
        return {"score": score,"level": "Robust", "description": "No frailty"}
    elif score in [1, 2]:
        return {"score": score,"level": "Pre-frail", "description": "Intermediate frailty"}
    elif score >= 3:
        return {"score": score,"level": "Frail", "description": "Frailty syndrome"}
    else:
        return {"score": score,"level": "Unknown", "description": "Invalid score"}