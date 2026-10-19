
from backend.core.engagement_scoring import EngagementScorer

scorer = EngagementScorer()

# Example synchronized data for one time segment.
fused_data = {
    "fusion_timestamp": "2026-10-20T10:00:00+00:00",
    "vision_timestamp": 100.0,
    "audio_timestamp": 101.0,
    "fusion_status": "Synchronized",
    "participant_count": 2,
    "participants": [
        {
            "participant_id": "P0001",
            "status": "Present",
            "presence_duration_seconds": 75,
        },
        {
            "participant_id": "P0002",
            "status": "Present",
            "presence_duration_seconds": 90,
        },
    ],
    "movement_frequency": 0.6,
    "inactivity_duration_seconds": 5,
    "audio": {
        "energy_db": -20.0,
        "active_sound_ratio": 0.7,
        "speech_activity_ratio": 0.7,
        "activity": "Active sound",
    },
}

# Analyze the first segment.
result = scorer.score_segment(fused_data)

print("ENGAGEMENT SCORING RESULT")
print("=========================")
print(result)

# Add a second segment to demonstrate temporal analysis.
second_segment = {
    **fused_data,
    "vision_timestamp": 105.0,
    "audio_timestamp": 106.0,
    "inactivity_duration_seconds": 25,
    "movement_frequency": 0.2,
    "audio": {
        **fused_data["audio"],
        "speech_activity_ratio": 0.2,
    },
}

second_result = scorer.score_segment(second_segment)

print("\nSECOND SEGMENT")
print("==============")
print(second_result)

print("\nTEMPORAL ENGAGEMENT PROFILE")
print("===========================")
for segment in scorer.get_temporal_profile():
    print(segment["timestamp"], segment["score"], segment["level"])

print("\nSESSION SUMMARY")
print("===============")
print(scorer.get_session_summary())
