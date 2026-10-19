
from backend.core.analytics_service import AnalyticsService

service = AnalyticsService()

sample_metrics = [
    {
        "session_id": 1,
        "timestamp": 100,
        "participant_id": "P0001",
        "presence_duration_seconds": 60,
        "engagement_score": 55,
        "activity": "First segment",
    },
    {
        "session_id": 1,
        "timestamp": 105,
        "participant_id": "P0001",
        "presence_duration_seconds": 65,
        "engagement_score": 72,
        "activity": "Second segment",
    },
    {
        "session_id": 1,
        "timestamp": 110,
        "participant_id": "P0002",
        "presence_duration_seconds": 90,
        "engagement_score": 60,
        "activity": "First segment",
    },
]

result = service.get_session_trends(
    session_id=1,
    metrics=sample_metrics,
)

print("STUDENT SESSION ANALYTICS")
print("=========================")
print(result)

print("\nINDIVIDUAL REFLECTIONS")
print("======================")
for participant_id, data in result["participants"].items():
    print(participant_id, ":", data["reflection"])
