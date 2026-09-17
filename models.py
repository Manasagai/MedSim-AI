from pydantic import BaseModel, Field
from typing import List

class PatientProfile(BaseModel):
    name: str
    age: int
    gender: str
    occupation: str
    past_medical_history: List[str]

class VitalSigns(BaseModel):
    heart_rate: str
    blood_pressure: str
    respiratory_rate: str
    temperature: str
    oxygen_saturation: str

class Question(BaseModel):
    question_text: str
    expected_answer: str
    scoring_guidance: str

class Scenario(BaseModel):
    profile: PatientProfile
    chief_complaint: str
    initial_presentation: str
    vital_signs: VitalSigns
    investigation_results: str
    questions: List[Question]
    instructor_notes: str
    hidden_diagnosis: str
