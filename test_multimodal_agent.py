
from backend.core.multimodal_agent import MultimodalAgent

agent = MultimodalAgent()

# Example output from the vision module
vision_data = {
    "participants": [
        {"participant_id": "P0001", "status": "Present"},
        {"participant_id": "P0002", "status": "Present"},
    ]
}

# Example metrics from your audio analysis module
audio_data = {
    "energy_db": -20.0,
    "active_sound_ratio": 0.7,
    "activity": "Active sound",
}

result = agent.analyze(
    vision_data=vision_data,
    audio_data=audio_data,
)

print("MULTIMODAL ANALYSIS RESULT")
print("==========================")

for key, value in result.items():
    print(f"{key}: {value}")

print("\nSESSION SUMMARY")
print(agent.get_session_summary())
