
from backend.core.recommendations_engine import RecommendationsEngine
from backend.core.teacher_profiles import TeacherProfileService

engine = RecommendationsEngine()

session_status = {
    "people": [
        {"id": "P0001", "attention": 35},
        {"id": "P0002", "attention": 75},
        {"id": "P0003", "attention": 55},
    ],
    "engagement_trend": [82.67, 51.33],
    "audio_activity": "Background noise",
}

print("TEACHING RECOMMENDATIONS")
print("========================")
for recommendation in engine.generate_realtime_recommendations(
    session_status
):
    print(recommendation)

profile_service = TeacherProfileService()

sessions = [
    {"name": "Session 1", "engagement": 82.67},
    {"name": "Session 2", "engagement": 51.33},
]

print("\nTEACHER PROFILE")
print("===============")
print(profile_service.get_profile("T001", sessions))
