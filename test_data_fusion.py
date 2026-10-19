
from backend.core.data_fusion import DataFusion
from backend.core.ai_suggestions import AISuggestionEngine

fusion = DataFusion(max_time_difference_seconds=2.0)
suggestion_engine = AISuggestionEngine()

# Example vision data at 100 seconds
vision_data = {
    "timestamp": 100.0,
    "participants": [
        {
            "participant_id": "P0001",
            "presence_duration_seconds": 75,
            "position": [320, 240],
            "status": "Present",
        },
        {
            "participant_id": "P0002",
            "presence_duration_seconds": 90,
            "position": [520, 260],
            "status": "Present",
        },
    ],
}

# Example audio data at 101 seconds
audio_data = {
    "timestamp": 101.0,
    "energy_db": -20.0,
    "active_sound_ratio": 0.7,
    "activity": "Active sound",
}

fused_data = fusion.fuse(vision_data, audio_data)

print("FUSED MULTIMODAL DATA")
print("=====================")
print(fused_data)

suggestions = suggestion_engine.generate_suggestions(fused_data)

print("\nCLASSROOM SUGGESTIONS")
print("====================")
print(suggestions)
