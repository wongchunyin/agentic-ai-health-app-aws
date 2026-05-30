"""
Livewell Core Schemas
Pydantic models for data validation
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Union, Dict, Any
from enum import Enum
from datetime import datetime

class Metadata(BaseModel):
    created_at: Optional[str] = Field(None, description="When the record was created")
    updated_at: Optional[str] = Field(None, description="When the record was last updated")
    created_by: Optional[str] = Field(None, description="Who created the record")
    updated_by: Optional[str] = Field(None, description="Who last updated the record")
    version: Optional[int] = Field(1, description="Record version number")
    source: Optional[str] = Field(None, description="Data source (e.g., 'mobile_app', 'web', 'api')")

class GenderEnum(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"

class ProviderEnum(str, Enum):
    GOOGLE = "google"
    OAUTH = "oauth"
    EMAIL = "email"

class ActionTypeEnum(str, Enum):
    PHYSICAL = "physical"
    MENTAL = "mental"
    DIET = "diet"
    MEDICAL = "medical"

class FrailtyScoreTypeEnum(str, Enum):
    ROCKWOOD_MITNITSKI = "ROCKWOOD_MITNITSKI"
    FRAIL_SCALE = "FRAIL"
    CLINICAL_FRAILTY_SCALE = "CLINICAL_FRAILTY_SCALE"
    FRIED_FRAILTY_PHENOTYPE = "FRIED_FRAILTY_PHENOTYPE"

class AssessmentStatusEnum(str, Enum):
    COMPLETED = "completed"
    INCOMPLETE = "incomplete"

class PlanStatusEnum(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    COMPLETED = "completed"
    CANCELED = "canceled"

class PlanTypeEnum(str, Enum):
    MANUALLY_CREATED = "manually_created"
    GENERATED = "generated"

class ActionDetail(BaseModel):
    name: str = Field(..., description="Activity name")
    action_type: Optional[str] = Field(None, description="Activity type")
    description: str = Field(..., description="Activity description")

class ContextDetail(BaseModel):
    location: str = Field(..., description="Where to perform (indoor/outdoor)")
    condition: Optional[str] = Field(None, description="Under what condition")

class FrequencyDetail(BaseModel):
    value: int = Field(..., description="Frequency value")
    unit: str = Field(..., description="Frequency unit (per day/week/month)")

class DurationDetail(BaseModel):
    value: int = Field(..., description="Duration value")
    unit: str = Field(..., description="Duration unit (hours/minutes/seconds)")

class TimeDetail(BaseModel):
    frequency: FrequencyDetail = Field(..., description="How often to perform")
    duration: Optional[DurationDetail] = Field(None, description="How long to perform")

class AACTTPlan(BaseModel):
    plan_id: str = Field(..., description="Unique identifier for the plan")
    plan_type: Optional[PlanTypeEnum] = Field(None, description="Type of plan (manually_created or generated)")
    action: ActionDetail = Field(..., description="Action details with name and description")
    actor: str = Field(..., description="Who performs the action")
    context: ContextDetail = Field(..., description="Context details with location and condition")
    target: str = Field(..., description="Target or goal")
    time: TimeDetail = Field(..., description="Time details with frequency and optional duration")
    created_at: Optional[str] = None
    end_at: Optional[str] = Field(None, description="When the plan ends")
    is_active: Optional[bool] = True
    
    # Duration validation removed - duration is optional for all plan types
    

class FrailScale(BaseModel):
    fatigue: Optional[bool] = Field(None, description="Do you feel fatigued?")
    resistance: Optional[bool] = Field(None, description="Cannot walk up 1 flight of stairs?")
    ambulation: Optional[bool] = Field(None, description="Cannot walk 1 block?")
    illnesses: Optional[Union[int, List[str]]] = Field(None, description="Number of illnesses (0-10) or list of illness names")
    
    @validator('illnesses')
    def validate_illnesses(cls, v):
        if v is not None:
            if isinstance(v, int) and (v < 0 or v > 10):
                raise ValueError('Illnesses count must be between 0 and 10')
            elif isinstance(v, list) and len(v) > 10:
                raise ValueError('Cannot have more than 10 illnesses')
        return v
    loss_of_weight: Optional[bool] = Field(None, description="Weight loss >5% in past year?")
    
    
    def calculate_score(self) -> int:
        """Calculate FRAIL scale score (0-5)"""
        score = 0
        if self.fatigue is True:
            score += 1
        if self.resistance is True:
            score += 1
        if self.ambulation is True:
            score += 1
        if self.illnesses is not None:
            illness_count = len(self.illnesses) if isinstance(self.illnesses, list) else self.illnesses
            if illness_count >= 5:
                score += 1
        if self.loss_of_weight is True:
            score += 1
        return score

class RockwoodMitnitski(BaseModel):
    eyesight: Optional[int] = Field(None, ge=1, le=5)
    hearing: Optional[int] = Field(None, ge=1, le=5)
    help_to_eat: Optional[int] = Field(None, ge=1, le=3)
    help_to_dress_and_undress: Optional[int] = Field(None, ge=1, le=3)
    ability_to_take_care_of_appearance: Optional[int] = Field(None, ge=1, le=3)
    help_to_walk: Optional[int] = Field(None, ge=1, le=3)
    help_to_get_in_and_out_of_bed: Optional[int] = Field(None, ge=1, le=3)
    help_to_take_a_bath_or_shower: Optional[int] = Field(None, ge=1, le=3)
    help_to_go_to_the_bathroom: Optional[int] = Field(None, ge=1, le=3)
    help_to_use_the_telephone: Optional[int] = Field(None, ge=1, le=3)
    help_to_get_to_place_out_of_walking_distance: Optional[int] = Field(None, ge=1, le=3)
    help_in_shopping: Optional[int] = Field(None, ge=1, le=3)
    help_to_prepare_own_meals: Optional[int] = Field(None, ge=1, le=3)
    help_to_do_housework: Optional[int] = Field(None, ge=1, le=3)
    ability_to_take_medicine: Optional[int] = Field(None, ge=1, le=3)
    ability_to_handle_own_money: Optional[int] = Field(None, ge=1, le=3)
    self_rating_of_health: Optional[int] = Field(None, ge=1, le=5)
    troubles_prevent_normal_activities: Optional[int] = Field(None, ge=1, le=3)
    living_alone: Optional[int] = Field(None, ge=1, le=2)
    having_a_cough: Optional[int] = Field(None, ge=1, le=2)
    feeling_tired: Optional[int] = Field(None, ge=1, le=2)
    nose_stuffed_up_or_sneezing: Optional[int] = Field(None, ge=1, le=2)
    high_blood_pressure: Optional[int] = Field(None, ge=1, le=2)
    heart_and_circulation_problems: Optional[int] = Field(None, ge=1, le=2)
    stroke_or_effects_of_stroke: Optional[int] = Field(None, ge=1, le=2)
    arthritis_or_rheumatism: Optional[int] = Field(None, ge=1, le=2)
    parkinsons_disease: Optional[int] = Field(None, ge=1, le=2)
    eye_trouble: Optional[int] = Field(None, ge=1, le=2)
    ear_trouble: Optional[int] = Field(None, ge=1, le=2)
    dental_problems: Optional[int] = Field(None, ge=1, le=2)
    chest_problems: Optional[int] = Field(None, ge=1, le=2)
    trouble_with_stomach: Optional[int] = Field(None, ge=1, le=2)
    kidney_trouble: Optional[int] = Field(None, ge=1, le=2)
    losing_control_of_bladder: Optional[int] = Field(None, ge=1, le=2)
    losing_control_of_bowels: Optional[int] = Field(None, ge=1, le=2)
    diabetes: Optional[int] = Field(None, ge=1, le=2)
    trouble_with_feet_or_ankles: Optional[int] = Field(None, ge=1, le=2)
    trouble_with_nerves: Optional[int] = Field(None, ge=1, le=2)
    skin_problems: Optional[int] = Field(None, ge=1, le=2)
    fractures: Optional[int] = Field(None, ge=1, le=2)
    
    def calculate_score(self) -> float:
        """Calculate Rockwood-Mitnitski Frailty Index (0.0-1.0)"""
        total_questions = 40
        deficit_count = 0
        
        for field_name, field_value in self.__dict__.items():
            if field_value is not None and field_value > 1:
                deficit_count += 1
        
        return round(deficit_count / total_questions, 3)

class FrailtyAssessmentHistory(BaseModel):
    assessment_id: str = Field(..., min_length=1)
    timestamp: str = Field(..., description="When the assessment was conducted")
    assessment_type: FrailtyScoreTypeEnum = Field(..., description="Type of frailty assessment")
    score: float = Field(..., description="Frailty score from the assessment")
    assessment_data: Optional[dict] = Field(None, description="Assessment-specific data based on assessment_type")
    status: Optional[AssessmentStatusEnum] = Field(None, description="Assessment completion status")
    assessment_result: Optional[dict] = Field(None, description="Score interpretation result")
    notes: Optional[str] = None
    metadata: Optional[Metadata] = None


    @validator('assessment_id')
    def assessment_id_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Assessment ID cannot be empty')
        return v.strip()
    
    @validator('timestamp')
    def validate_timestamp(cls, v):
        if not v.strip():
            raise ValueError('Timestamp cannot be empty')
        return v.strip()
    
    @validator('status', pre=True, always=True)
    def set_status_based_on_data(cls, v, values):
        # If status is already provided, use it (handle both enum and string values)
        if v:
            if isinstance(v, str):
                # Convert string to enum if needed
                try:
                    return AssessmentStatusEnum(v)
                except ValueError:
                    pass
            return v
            
        # Auto-determine status based on assessment_data completeness
        assessment_data = values.get('assessment_data')
        assessment_type = values.get('assessment_type')
        
        if not assessment_data or not assessment_type:
            return AssessmentStatusEnum.INCOMPLETE
            
        if assessment_type == FrailtyScoreTypeEnum.FRAIL_SCALE:
            required_fields = ['fatigue', 'resistance', 'ambulation', 'illnesses', 'loss_of_weight']
            for field in required_fields:
                if field not in assessment_data or assessment_data[field] is None:
                    return AssessmentStatusEnum.INCOMPLETE
            return AssessmentStatusEnum.COMPLETED
        elif assessment_type == FrailtyScoreTypeEnum.ROCKWOOD_MITNITSKI:
            # Check if at least some fields are filled for Rockwood-Mitnitski
            filled_fields = sum(1 for v in assessment_data.values() if v is not None)
            if filled_fields < 40:
                return AssessmentStatusEnum.INCOMPLETE
            return AssessmentStatusEnum.COMPLETED
            
        return AssessmentStatusEnum.COMPLETED
    
    @validator('assessment_data')
    def validate_assessment_data(cls, v, values):
        if not v:
            return v

        assessment_type = values.get('assessment_type')

        if assessment_type == FrailtyScoreTypeEnum.FRAIL_SCALE.value:
            if 'illnesses' in v and v['illnesses'] is not None:
                illnesses = v['illnesses']
                if isinstance(illnesses, int):
                    if illnesses < 0 or illnesses > 10:
                        raise ValueError('FRAIL scale illnesses count must be 0-10')
                elif isinstance(illnesses, list):
                    if len(illnesses) > 10:
                        raise ValueError('FRAIL scale cannot have more than 10 illnesses')
                else:
                    raise ValueError('FRAIL scale illnesses must be integer count or list of illness names')

        elif assessment_type == FrailtyScoreTypeEnum.ROCKWOOD_MITNITSKI.value:
            # Rockwood-Mitnitski uses individual question fields, no validation needed here
            pass

        return v

    class Config:
        use_enum_values = True

    def convertJSON(self):
        """Convert profile to JSON string"""
        return self.json()
    
    def convertDict(self):
        """Convert profile to dictionary"""
        return self.dict()
    


    # @validator('assessment_data')
    # def validate_assessment_data(cls, v, values):
    #     if not v:
    #         return v
        
        # assessment_type = values.get('assessment_type')
        
        # if assessment_type == FrailtyScoreTypeEnum.FRAIL_SCALE.value:
        #     required_fields = ['fatigue', 'resistance', 'ambulation', 'illnesses', 'loss_of_weight']
        #     for field in required_fields:
        #         if field not in v:
        #             raise ValueError(f'FRAIL scale missing required field: {field}')
        #     if not isinstance(v['illnesses'], int) or v['illnesses'] < 0 or v['illnesses'] > 11:
        #         raise ValueError('FRAIL scale illnesses must be integer 0-11')
        
        # elif assessment_type == FrailtyScoreTypeEnum.ROCKWOOD_MITNITSKI.value:
        #     if 'deficits' not in v:
        #         raise ValueError('Rockwood-Mitnitski missing required field: deficits')
        #     deficits = v['deficits']
        #     if not isinstance(deficits, list):
        #         raise ValueError('Rockwood-Mitnitski deficits must be a list')
        #     for deficit in deficits:
        #         if deficit not in [0.0, 0.5, 1.0]:
        #             raise ValueError('Rockwood-Mitnitski deficit values must be 0.0, 0.5, or 1.0')
        
        # return v

class DayOfWeekEnum(str, Enum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"

class TimeSlot(BaseModel):
    start_time: str = Field(..., description="Start time in HH:MM format (24-hour)")
    end_time: str = Field(..., description="End time in HH:MM format (24-hour)")
    
    @validator('start_time', 'end_time')
    def validate_time_format(cls, v):
        import re
        if not re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', v):
            raise ValueError('Time must be in HH:MM format (24-hour)')
        return v

class PreferredFitnessDay(BaseModel):
    day: DayOfWeekEnum = Field(..., description="Day of the week")
    available: bool = Field(..., description="Whether user is available for workout on this day")
    time_slots: Optional[List[TimeSlot]] = Field(None, description="Available time periods for workout")
    notes: Optional[str] = Field(None, description="Additional notes for this day")

class UserPreferences(BaseModel):
    physical_activities_like: Optional[List[str]] = None
    physical_activities_dislike: Optional[List[str]] = None
    mental_activities_like: Optional[List[str]] = None
    mental_activities_dislike: Optional[List[str]] = None
    diet_activities_like: Optional[List[str]] = None
    diet_activities_dislike: Optional[List[str]] = None
    medical_activities_like: Optional[List[str]] = None
    medical_activities_dislike: Optional[List[str]] = None
    preferred_fitness_days: Optional[List[PreferredFitnessDay]] = Field(None, description="Weekly fitness schedule preferences")

class Address(BaseModel):
    street: Optional[str] = Field(None, max_length=200, description="Street address")
    city: Optional[str] = Field(None, max_length=100, description="City")
    state_province: Optional[str] = Field(None, max_length=100, description="State/Province/Region")
    postal_code: Optional[str] = Field(None, max_length=20, description="Postal/ZIP code")
    country: Optional[str] = Field(None, max_length=100, description="Country")
    
class Profile(BaseModel):
    user_id: str = Field(..., min_length=1, description="Unique user identifier")
    email: EmailStr
    email_validated: Optional[bool] = Field(None, description="Whether the email has been verified")
    first_name: str = Field(..., min_length=1, max_length=50)
    middle_name: Optional[str] = Field(None, min_length=1, max_length=50)
    family_name: str = Field(..., min_length=1, max_length=50)
    preferred_name: Optional[str] = Field(None, min_length=1, max_length=50)
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    dob: Optional[str] = Field(None, description="Date of birth in YYYY-MM-DD format")
    gender: Optional[GenderEnum] = None
    height: Optional[float] = Field(None, description="Height in centimeters")
    weight: Optional[float] = Field(None, description="Weight in kilograms")
    address: Optional[Address] = Field(None, description="User's address")
    # location: Optional[str] = Field(None, min_length=2, max_length=100)
    user_preferences: Optional[UserPreferences] = None
    preferred_fitness_days: Optional[List[PreferredFitnessDay]] = Field(None, description="Weekly fitness schedule preferences")
    plans: Optional[List[AACTTPlan]] = None
    provider: Optional[ProviderEnum] = None
    sms_permission: Optional[bool] = Field(None, description="Permission to send SMS notifications")
    email_permission: Optional[bool] = Field(None, description="Permission to send email notifications")
    frailty_history: Optional[List[FrailtyAssessmentHistory]] = None
    metadata: Optional[Metadata] = None
    activity_score: Optional[int] = Field(None, description="Activities score from the assessment")
    allowShareName: Optional[bool] = Field(False, description="Whether to allow sharing of name")
    allowSMS: Optional[bool] = Field(None, description="Whether to allow SMS notifications")
    allowEmail: Optional[bool] = Field(None, description="Whether to allow email notifications")
    
    @validator('first_name', 'family_name')
    def names_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Name fields cannot be empty')
        return v.strip()
    
    # @validator('preferred_name')
    # def preferred_name_must_not_be_empty(cls, v):
    #     if v and not v.strip():
    #         raise ValueError('Preferred name cannot be empty')
    #     return v.strip() if v else v
    
    @validator('full_name')
    def full_name_must_not_be_empty(cls, v):
        if v and not v.strip():
            raise ValueError('Full name cannot be empty')
        return v.strip() if v else v
    
    @validator('dob')
    def validate_dob(cls, v):
        if v:
            import re
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', v):
                raise ValueError('Date of birth must be in YYYY-MM-DD format')
        return v
    
    # @validator('location')
    # def location_must_not_be_empty(cls, v):
    #     if v and not v.strip():
    #         raise ValueError('Location cannot be empty')
    #     return v.strip() if v else v
    
    def convertJSON(self):
        """Convert profile to JSON string"""
        return self.json()
    
    def convertDict(self):
        """Convert profile to dictionary"""
        return self.dict()
    
    class Config:
        use_enum_values = True


