
from datetime import datetime, timezone


class DataFusion:
    """Synchronize and combine vision and audio observations."""

    def __init__(self, max_time_difference_seconds=2.0):
        self.max_time_difference_seconds = max_time_difference_seconds

    @staticmethod
    def _parse_timestamp(value):
        """Convert ISO timestamps or numeric seconds to comparable time."""
        if isinstance(value, (int, float)):
            return float(value)

        if isinstance(value, str):
            try:
                return datetime.fromisoformat(
                    value.replace("Z", "+00:00")
                ).timestamp()
            except ValueError:
                return None

        return None

    def fuse(self, vision_data, audio_data):
        """
        Combine vision and audio data.

        Vision example:
        {
            "timestamp": 100.0,
            "participants": [
                {
                    "participant_id": "P0001",
                    "presence_duration_seconds": 75,
                    "position": [320, 240]
                }
            ]
        }

        Audio example:
        {
            "timestamp": 101.0,
            "energy_db": -20,
            "active_sound_ratio": 0.7,
            "activity": "Active sound"
        }
        """
        vision_data = vision_data or {}
        audio_data = audio_data or {}

        vision_time = self._parse_timestamp(
            vision_data.get("timestamp")
        )
        audio_time = self._parse_timestamp(
            audio_data.get("timestamp")
        )

        synchronized = False
        time_difference = None

        if vision_time is not None and audio_time is not None:
            time_difference = abs(vision_time - audio_time)
            synchronized = (
                time_difference <= self.max_time_difference_seconds
            )

        participants = vision_data.get("participants", [])
        if not isinstance(participants, list):
            participants = []

        participant_summaries = []
        for participant in participants:
            if not isinstance(participant, dict):
                continue

            participant_summaries.append({
                "participant_id": participant.get("participant_id"),
                "presence_duration_seconds": participant.get(
                    "presence_duration_seconds"
                ),
                "position": participant.get("position"),
                "status": participant.get("status", "Unknown"),
            })

        fused = {
            "fusion_timestamp": datetime.now(timezone.utc).isoformat(),
            "vision_timestamp": vision_data.get("timestamp"),
            "audio_timestamp": audio_data.get("timestamp"),
            "synchronized": synchronized,
            "time_difference_seconds": (
                round(time_difference, 3)
                if time_difference is not None
                else None
            ),
            "participant_count": len(participant_summaries),
            "participants": participant_summaries,
            "audio": {
                "energy_db": audio_data.get("energy_db"),
                "active_sound_ratio": audio_data.get(
                    "active_sound_ratio"
                ),
                "activity": audio_data.get("activity", "Unknown"),
            },
        }

        if not vision_data or not audio_data:
            fused["fusion_status"] = "Incomplete data"
        elif vision_time is None or audio_time is None:
            fused["fusion_status"] = "Timestamp unavailable"
        elif not synchronized:
            fused["fusion_status"] = "Timestamps not aligned"
        else:
            fused["fusion_status"] = "Synchronized"

        return fused
