from frail_scale_survey import get_FRAIL_scale_questions, calculate_FRAIL_score, interpret_FRAIL_score
from rockwood_mintnitski_survey import get_rockwood_mitnitski_questions, calculate_rockwood_mitnitski_score, interpret_rockwood_mitnitski_score
import os
import sys
try:
    from schemas import FrailtyScoreTypeEnum
except ImportError:
    # Add toolkit layer path
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../livewell-core/python'))
    from schemas import FrailtyScoreTypeEnum


class AssessmentUtils:
    def __init__(self):
        pass

    @staticmethod
    def get_FRAIL_survey():
        """Get FRAIL scale assessment questions"""
        return get_FRAIL_scale_questions()
    
    @staticmethod
    def calculate_score(assessment_type, responses):
        """Calculate FRAIL scale score from responses"""
        if assessment_type == FrailtyScoreTypeEnum.FRAIL_SCALE.value:
            return calculate_FRAIL_score(responses)
        elif assessment_type == FrailtyScoreTypeEnum.ROCKWOOD_MITNITSKI.value:
            return calculate_rockwood_mitnitski_score(responses)
    
    @staticmethod
    def interpret_score(assessment_type, score):
        """Interpret FRAIL scale score"""
        if assessment_type == FrailtyScoreTypeEnum.FRAIL_SCALE.value:
            return interpret_FRAIL_score(score)
        elif assessment_type == FrailtyScoreTypeEnum.ROCKWOOD_MITNITSKI.value:
            return interpret_rockwood_mitnitski_score(score)
    
    @staticmethod
    def get_rockwood_mitnitski_survey():
        """Get Rockwood-Mitnitski assessment questions"""
        return get_rockwood_mitnitski_questions()
       
    @staticmethod
    def calculate_rockwood_mitnitski_score(responses):
        """Calculate Rockwood-Mitnitski score from responses"""
        return calculate_rockwood_mitnitski_score(responses)
    
    @staticmethod
    def interpret_rockwood_mitnitski_score(score):
        """Interpret Rockwood-Mitnitski score"""
        return interpret_rockwood_mitnitski_score(score)
    
    
    
if "__main__" == __name__:
    # test the calculate_score
    responses = {
        "fatigue": False,
        "resistance": False,
        "ambulation": False,
        "illnesses": 10,
        "loss_of_weight": False
    }
    score = AssessmentUtils.calculate_score(responses)
    fs = AssessmentUtils.interpret_score(score)
    print(f"score {fs['score']}, level {fs['level']}, description {fs['description']}")