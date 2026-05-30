"""
Rockwood Mitnitski Frailty Survey Questions and Options
Based on the provided image of a 40-item deficit list.
"""

ROCKWOOD_MITNITSKI_SURVEY = {
    "eyesight": {
        "question": "1. Eyesight",
        "description": "Assesses visual impairment that can affect daily activities.",
        "options": [
            {"value": 1, "label": "No difficulty"},
            {"value": 2, "label": "Some difficulty"},
            {"value": 3, "label": "A great deal of difficulty"},
            {"value": 4, "label": "Cannot do at all"},
            {"value": 5, "label": "Completely blind"}
        ]
    },
    "hearing": {
        "question": "2. Hearing",
        "description": "Assesses hearing impairment that can affect communication and safety.",
        "options": [
            {"value": 1, "label": "No difficulty"},
            {"value": 2, "label": "Some difficulty"},
            {"value": 3, "label": "A great deal of difficulty"},
            {"value": 4, "label": "Cannot do at all"},
            {"value": 5, "label": "Completely deaf"}
        ]
    },
    "help_to_eat": {
        "question": "3. Help to eat",
        "description": "Assesses the ability to perform activities of daily living related to eating.",
        "options": [
            {"value": 1, "label": "No difficulty"},
            {"value": 2, "label": "Some difficulty"},
            {"value": 3, "label": "Cannot do at all"}
        ]
    },
    "help_to_dress_and_undress": {
        "question": "4. Help to dress and undress",
        "description": "Assesses the ability to perform activities of daily living related to dressing.",
        "options": [
            {"value": 1, "label": "No difficulty"},
            {"value": 2, "label": "Some difficulty"},
            {"value": 3, "label": "Cannot do at all"}
        ]
    },
    "ability_to_take_care_of_appearance": {
        "question": "5. Ability to take care of appearance",
        "description": "Assesses the ability to perform activities of daily living related to personal grooming.",
        "options": [
            {"value": 1, "label": "No difficulty"},
            {"value": 2, "label": "Some difficulty"},
            {"value": 3, "label": "Cannot do at all"}
        ]
    },
    "help_to_walk": {
        "question": "6. Help to walk",
        "description": "Assesses mobility and physical function related to walking.",
        "options": [
            {"value": 1, "label": "No difficulty"},
            {"value": 2, "label": "Some difficulty"},
            {"value": 3, "label": "Cannot do at all"}
        ]
    },
    "help_to_get_in_and_out_of_bed": {
        "question": "7. Help to get in and out of bed",
        "description": "Assesses the ability to transfer between bed and an upright position.",
        "options": [
            {"value": 1, "label": "No difficulty"},
            {"value": 2, "label": "Some difficulty"},
            {"value": 3, "label": "Cannot do at all"}
        ]
    },
    "help_to_take_a_bath_or_shower": {
        "question": "8. Help to take a bath or shower",
        "description": "Assesses the ability to perform personal hygiene activities.",
        "options": [
            {"value": 1, "label": "No difficulty"},
            {"value": 2, "label": "Some difficulty"},
            {"value": 3, "label": "Cannot do at all"}
        ]
    },
    "help_to_go_to_the_bathroom": {
        "question": "9. Help to go to the bathroom",
        "description": "Assesses the ability to use the bathroom independently.",
        "options": [
            {"value": 1, "label": "No difficulty"},
            {"value": 2, "label": "Some difficulty"},
            {"value": 3, "label": "Cannot do at all"}
        ]
    },
    "help_to_use_the_telephone": {
        "question": "10. Help to use the telephone",
        "description": "Assesses the ability to use a telephone for communication.",
        "options": [
            {"value": 1, "label": "No difficulty"},
            {"value": 2, "label": "Some difficulty"},
            {"value": 3, "label": "Cannot do at all"}
        ]
    },
    "help_to_get_to_place_out_of_walking_distance": {
        "question": "11. Help to get to place out of walking distance",
        "description": "Assesses the ability to travel for errands and social activities.",
        "options": [
            {"value": 1, "label": "No difficulty"},
            {"value": 2, "label": "Some difficulty"},
            {"value": 3, "label": "Cannot do at all"}
        ]
    },
    "help_in_shopping": {
        "question": "12. Help in shopping",
        "description": "Assesses the ability to shop for groceries or necessities.",
        "options": [
            {"value": 1, "label": "No difficulty"},
            {"value": 2, "label": "Some difficulty"},
            {"value": 3, "label": "Cannot do at all"}
        ]
    },
    "help_to_prepare_own_meals": {
        "question": "13. Help to prepare own meals",
        "description": "Assesses the ability to prepare meals independently.",
        "options": [
            {"value": 1, "label": "No difficulty"},
            {"value": 2, "label": "Some difficulty"},
            {"value": 3, "label": "Cannot do at all"}
        ]
    },
    "help_to_do_housework": {
        "question": "14. Help to do housework",
        "description": "Assesses the ability to maintain a household.",
        "options": [
            {"value": 1, "label": "No difficulty"},
            {"value": 2, "label": "Some difficulty"},
            {"value": 3, "label": "Cannot do at all"}
        ]
    },
    "ability_to_take_medicine": {
        "question": "15. Ability to take medicine",
        "description": "Assesses the ability to manage and take medication as prescribed.",
        "options": [
            {"value": 1, "label": "No difficulty"},
            {"value": 2, "label": "Some difficulty"},
            {"value": 3, "label": "Cannot do at all"}
        ]
    },
    "ability_to_handle_own_money": {
        "question": "16. Ability to handle own money",
        "description": "Assesses the ability to manage personal finances.",
        "options": [
            {"value": 1, "label": "No difficulty"},
            {"value": 2, "label": "Some difficulty"},
            {"value": 3, "label": "Cannot do at all"}
        ]
    },
    "self_rating_of_health": {
        "question": "17. Self-rating of health",
        "description": "A subjective assessment of overall health status.",
        "options": [
            {"value": 1, "label": "Excellent"},
            {"value": 2, "label": "Very good"},
            {"value": 3, "label": "Good"},
            {"value": 4, "label": "Fair"},
            {"value": 5, "label": "Poor"}
        ]
    },
    "troubles_prevent_normal_activities": {
        "question": "18. Troubles prevent normal activities",
        "description": "Assesses how health troubles interfere with regular daily life.",
        "options": [
            {"value": 1, "label": "No, not at all"},
            {"value": 2, "label": "Yes, some of the time"},
            {"value": 3, "label": "Yes, a great deal of the time"}
        ]
    },
    "living_alone": {
        "question": "19. Living alone",
        "description": "Indicates social support and living situation.",
        "options": [
            {"value": 1, "label": "No"},
            {"value": 2, "label": "Yes"}
        ]
    },
    "having_a_cough": {
        "question": "20. Having a cough",
        "description": "Presence of respiratory symptoms.",
        "options": [
            {"value": 1, "label": "No"},
            {"value": 2, "label": "Yes"}
        ]
    },
    "feeling_tired": {
        "question": "21. Feeling tired",
        "description": "Presence of fatigue, a common symptom of frailty.",
        "options": [
            {"value": 1, "label": "No"},
            {"value": 2, "label": "Yes"}
        ]
    },
    "nose_stuffed_up_or_sneezing": {
        "question": "22. Nose stuffed up or sneezing",
        "description": "Presence of upper respiratory symptoms.",
        "options": [
            {"value": 1, "label": "No"},
            {"value": 2, "label": "Yes"}
        ]
    },
    "high_blood_pressure": {
        "question": "23. High blood pressure",
        "description": "Presence of a diagnosed chronic condition.",
        "options": [
            {"value": 1, "label": "No"},
            {"value": 2, "label": "Yes"}
        ]
    },
    "heart_and_circulation_problems": {
        "question": "24. Heart and circulation problems",
        "description": "Presence of a diagnosed cardiovascular condition.",
        "options": [
            {"value": 1, "label": "No"},
            {"value": 2, "label": "Yes"}
        ]
    },
    "stroke_or_effects_of_stroke": {
        "question": "25. Stroke or effects of stroke",
        "description": "Presence of a cerebrovascular event and its ongoing effects.",
        "options": [
            {"value": 1, "label": "No"},
            {"value": 2, "label": "Yes"}
        ]
    },
    "arthritis_or_rheumatism": {
        "question": "26. Arthritis or rheumatism",
        "description": "Presence of musculoskeletal conditions that can cause pain and limit mobility.",
        "options": [
            {"value": 1, "label": "No"},
            {"value": 2, "label": "Yes"}
        ]
    },
    "parkinsons_disease": {
        "question": "27. Parkinson's disease",
        "description": "Presence of a neurodegenerative disorder affecting motor skills.",
        "options": [
            {"value": 1, "label": "No"},
            {"value": 2, "label": "Yes"}
        ]
    },
    "eye_trouble": {
        "question": "28. Eye trouble",
        "description": "Presence of chronic eye conditions.",
        "options": [
            {"value": 1, "label": "No"},
            {"value": 2, "label": "Yes"}
        ]
    },
    "ear_trouble": {
        "question": "29. Ear trouble",
        "description": "Presence of chronic ear conditions.",
        "options": [
            {"value": 1, "label": "No"},
            {"value": 2, "label": "Yes"}
        ]
    },
    "dental_problems": {
        "question": "30. Dental problems",
        "description": "Presence of oral health issues that can affect nutrition.",
        "options": [
            {"value": 1, "label": "No"},
            {"value": 2, "label": "Yes"}
        ]
    },
    "chest_problems": {
        "question": "31. Chest problems",
        "description": "Presence of chronic chest or respiratory conditions.",
        "options": [
            {"value": 1, "label": "No"},
            {"value": 2, "label": "Yes"}
        ]
    },
    "trouble_with_stomach": {
        "question": "32. Trouble with stomach",
        "description": "Presence of chronic digestive issues.",
        "options": [
            {"value": 1, "label": "No"},
            {"value": 2, "label": "Yes"}
        ]
    },
    "kidney_trouble": {
        "question": "33. Kidney trouble",
        "description": "Presence of chronic kidney disease.",
        "options": [
            {"value": 1, "label": "No"},
            {"value": 2, "label": "Yes"}
        ]
    },
    "losing_control_of_bladder": {
        "question": "34. Losing control of bladder",
        "description": "Presence of urinary incontinence.",
        "options": [
            {"value": 1, "label": "No"},
            {"value": 2, "label": "Yes"}
        ]
    },
    "losing_control_of_bowels": {
        "question": "35. Losing control of bowels",
        "description": "Presence of bowel incontinence.",
        "options": [
            {"value": 1, "label": "No"},
            {"value": 2, "label": "Yes"}
        ]
    },
    "diabetes": {
        "question": "36. Diabetes",
        "description": "Presence of a diagnosed metabolic condition.",
        "options": [
            {"value": 1, "label": "No"},
            {"value": 2, "label": "Yes"}
        ]
    },
    "trouble_with_feet_or_ankles": {
        "question": "37. Trouble with feet or ankles",
        "description": "Presence of chronic lower extremity problems that affect mobility.",
        "options": [
            {"value": 1, "label": "No"},
            {"value": 2, "label": "Yes"}
        ]
    },
    "trouble_with_nerves": {
        "question": "38. Trouble with nerves",
        "description": "Presence of neurological issues or neuropathy.",
        "options": [
            {"value": 1, "label": "No"},
            {"value": 2, "label": "Yes"}
        ]
    },
    "skin_problems": {
        "question": "39. Skin problems",
        "description": "Presence of chronic skin conditions.",
        "options": [
            {"value": 1, "label": "No"},
            {"value": 2, "label": "Yes"}
        ]
    },
    "fractures": {
        "question": "40. Fractures",
        "description": "Presence of a history of broken bones, indicating bone fragility.",
        "options": [
            {"value": 1, "label": "No"},
            {"value": 2, "label": "Yes"}
        ]
    }
}

def get_rockwood_mitnitski_questions():
    """Return the Rockwood Mitnitski frailty survey questions."""
    return ROCKWOOD_MITNITSKI_SURVEY

def calculate_rockwood_mitnitski_score(responses):
    """
    Calculate the frailty index score (0-1) from responses.
    This is a simplified calculation for demonstration purposes.
    The actual Rockwood Frailty Index requires more complex calculations
    based on the number of deficits present.
    """
    total_deficits = len(ROCKWOOD_MITNITSKI_SURVEY)
    answered_deficits = 0
    frailty_score = 0
    for key, value in responses.items():
        if value is not None and value != 1:
            answered_deficits += 1
            frailty_score += 1

    if total_deficits == 0:
        return 0
    
    return frailty_score / total_deficits

def interpret_rockwood_mitnitski_score(score):
    """
    Interpret the Rockwood Mitnitski frailty index score.
    Scores are typically interpreted as follows:
    < 0.1: Robust
    0.1 to 0.2: Pre-frail
    > 0.25: Frail
    """
    if score < 0.1:
        return {"score": score, "level": "Robust", "description": "No significant frailty."}
    elif 0.1 <= score <= 0.2:
        return {"score": score, "level": "Pre-frail", "description": "Intermediate level of frailty."}
    elif score > 0.2:
        return {"score": score, "level": "Frail", "description": "Frailty syndrome."}
    else:
        return {"score": score, "level": "Unknown", "description": "Invalid score."}

if __name__ == '__main__':
    # This is a basic example of how the functions could be used.
    # In a real application, 'responses' would come from user input.
    sample_responses = {
        "eyesight": 2,
        "hearing": 2,
        "help_to_eat": 1,
        "help_to_dress_and_undress": 1,
        "ability_to_take_care_of_appearance": 1,
        "help_to_walk": 2,
        "help_to_get_in_and_out_of_bed": 1,
        "help_to_take_a_bath_or_shower": 1,
        "help_to_go_to_the_bathroom": 1,
        "help_to_use_the_telephone": 1,
        "help_to_get_to_place_out_of_walking_distance": 1,
        "help_in_shopping": 1,
        "help_to_prepare_own_meals": 1,
        "help_to_do_housework": 1,
        "ability_to_take_medicine": 1,
        "ability_to_handle_own_money": 1,
        "self_rating_of_health": 4,
        "troubles_prevent_normal_activities": 2,
        "living_alone": 2,
        "having_a_cough": 1,
        "feeling_tired": 1,
        "nose_stuffed_up_or_sneezing": 1,
        "high_blood_pressure": 2,
        "heart_and_circulation_problems": 1,
        "stroke_or_effects_of_stroke": 1,
        "arthritis_or_rheumatism": 2,
        "parkinsons_disease": 1,
        "eye_trouble": 1,
        "ear_trouble": 1,
        "dental_problems": 2,
        "chest_problems": 1,
        "trouble_with_stomach": 1,
        "kidney_trouble": 1,
        "losing_control_of_bladder": 1,
        "losing_control_of_bowels": 1,
        "diabetes": 1,
        "trouble_with_feet_or_ankles": 1,
        "trouble_with_nerves": 1,
        "skin_problems": 1,
        "fractures": 1
    }
    
    score = calculate_rockwood_mitnitski_score(sample_responses)
    interpretation = interpret_rockwood_mitnitski_score(score)

    print(f"Calculated Frailty Index Score: {score:.2f}")
    print(f"Interpretation: {interpretation['level']} - {interpretation['description']}")
