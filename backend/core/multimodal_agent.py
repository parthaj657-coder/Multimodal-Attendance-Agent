
from datetime import datetime, timezone


class MultimodalAgent:
    """
    Combines vision and audio metrics into explainable,
    rule-based classroom session insights.
    """

    def __init__(self):
        self.session_history = []

    @staticmethod
    def _number(data, key, default=0.0):
        """Read a numeric value safely from a dictionary."""
        try:
            value = float(data.get(key, default))
            if value != value or value in (float("inf"), float("-inf")):
                return float(default)
            return value
        except (TypeError, ValueError, AttributeError):
            return float(default)

    def analyze(
        self,
        vision_data=None,
        audio_data=None,
        timestamp=None,
    ):
        """
        Expected vision_data example:
        {
            "participants": [
                {"participant_id": "P0001", "status": "Present"}
            ]
        }

        Expected audio_data example:
        {
            "energy_db": -20.0,
            "active_sound_ratio": 0.7,
            "activity": "Active sound"
        }
        """
        vision_data = vision_data or {}
        audio_data = audio_data or {}

        if timestamp is None:
            timestamp = datetime.now(timezone.utc).isoformat()

        participants = vision_data.get("participants", [])
        if not isinstance(participants, list):
            participants = []

        participant_ids = set()
        for participant in participants:
            if isinstance(participant, dict):
                participant_id = participant.get("participant_id")
                if participant_id:
                    participant_ids.add(str(participant_id))

        participant_count = len(participant_ids)

        energy_db = self._number(audio_data, "energy_db", -100.0)
        active_ratio = self._number(
            audio_data, "active_sound_ratio", 0.0
        )
        active_ratio = max(0.0, min(1.0, active_ratio))

        audio_activity = str(
            audio_data.get("activity", "Unknown")
        )

        # Audio context: this is sound activity, not verified speech.
        if audio_data.get("activity") == "Silence":
            audio_context = "Quiet audio conditions"
            audio_explanation = (
                "The audio module classified this segment as silence."
            )
        elif audio_activity == "Background noise":
            audio_context = "Background sound detected"
            audio_explanation = (
                "The audio module classified this segment as background noise."
            )
        elif audio_activity == "Active sound":
            audio_context = "Active sound detected"
            audio_explanation = (
                "The audio module detected sound energy above its activity threshold; "
                "this does not confirm that the sound is speech."
            )
        elif audio_data:
            audio_context = "Audio metrics available"
            audio_explanation = (
                "Audio metrics were supplied, but the activity label "
                "was not recognized."
            )
        else:
            audio_context = "Audio data unavailable"
            audio_explanation = (
                "No audio metrics were supplied for this analysis."
            )

        # Vision context describes tracked faces/presence only.
        if participant_count > 0:
            vision_context = "Tracked participants detected"
            vision_explanation = (
                f"The vision input contains {participant_count} unique "
                "participant ID(s) in this snapshot."
            )
        else:
            vision_context = "No tracked participants in this snapshot"
            vision_explanation = (
                "No participant IDs were supplied in the vision input. "
                "This does not prove the classroom is empty."
            )

        # Avoid claiming that sound or face presence proves engagement.
        evidence = [
            {
                "source": "vision",
                "observation": vision_context,
                "explanation": vision_explanation,
            },
            {
                "source": "audio",
                "observation": audio_context,
                "explanation": audio_explanation,
            },
        ]

        recommendations = []

        if not vision_data:
            recommendations.append(
                "Provide current vision-module results for a combined analysis."
            )

        if not audio_data:
            recommendations.append(
                "Provide audio-module metrics for the same time interval."
            )
        elif audio_activity == "Background noise":
            recommendations.append(
                "Review the audio segment if background noise may affect "
                "classroom communication."
            )
        elif audio_activity == "Active sound":
            recommendations.append(
                "Review the segment if you need to determine whether the "
                "detected sound is speech or another sound source."
            )

        if participant_count == 0:
            recommendations.append(
                "Check camera framing and face-detection quality before "
                "drawing conclusions about attendance."
            )

        if not recommendations:
            recommendations.append(
                "Continue collecting synchronized audio and vision data "
                "to evaluate changes over time."
            )

        result = {
            "timestamp": timestamp,
            "participant_count": participant_count,
            "participant_ids": sorted(participant_ids),
            "audio_energy_db": round(energy_db, 2),
            "active_sound_ratio": round(active_ratio, 3),
            "audio_activity": audio_activity,
            "vision_context": vision_context,
            "audio_context": audio_context,
            "engagement_assessment": (
                "Insufficient evidence for a reliable engagement score"
            ),
            "evidence": evidence,
            "recommendations": recommendations,
        }

        self.session_history.append(result)
        return result

    def get_session_summary(self):
        """Return a summary of analyses performed in this session."""
        if not self.session_history:
            return {
                "analyses_count": 0,
                "message": "No multimodal analyses have been performed.",
            }

        ratios = [
            item["active_sound_ratio"]
            for item in self.session_history
        ]

        return {
            "analyses_count": len(self.session_history),
            "average_active_sound_ratio": round(
                sum(ratios) / len(ratios), 3
            ),
            "message": (
                "Summary of sound activity and vision observations. "
                "These metrics do not independently establish engagement."
            ),
        }
