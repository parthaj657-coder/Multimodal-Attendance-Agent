
class EngagementScorer:
    """
    Calculate transparent, adjustable engagement proxy scores
    for individual time segments.

    Scores describe available activity signals, not a verified
    measurement of attention, understanding, or learning.
    """

    def __init__(
        self,
        presence_weight=0.40,
        movement_weight=0.20,
        speech_weight=0.20,
        inactivity_weight=0.20,
        inactivity_limit_seconds=30.0,
    ):
        weights = {
            "presence": presence_weight,
            "movement": movement_weight,
            "speech": speech_weight,
            "inactivity": inactivity_weight,
        }

        if any(weight < 0 for weight in weights.values()):
            raise ValueError("Weights cannot be negative.")

        if sum(weights.values()) <= 0:
            raise ValueError("At least one weight must be positive.")

        if inactivity_limit_seconds <= 0:
            raise ValueError("Inactivity limit must be positive.")

        self.weights = weights
        self.inactivity_limit_seconds = inactivity_limit_seconds
        self.temporal_profile = []

    @staticmethod
    def _clamp(value, minimum=0.0, maximum=1.0):
        return max(minimum, min(maximum, value))

    @staticmethod
    def _safe_number(value):
        try:
            number = float(value)
            if number != number or abs(number) == float("inf"):
                return None
            return number
        except (TypeError, ValueError):
            return None

    def score_segment(self, fused_data):
        """Score one fused observation and explain the result."""
        if not isinstance(fused_data, dict):
            raise ValueError("fused_data must be a dictionary.")

        if fused_data.get("fusion_status") != "Synchronized":
            result = {
                "timestamp": fused_data.get("fusion_timestamp"),
                "score": None,
                "level": "Unavailable",
                "reason": "Vision and audio data are not synchronized.",
                "components": {},
                "missing_signals": ["synchronized multimodal data"],
            }
            self.temporal_profile.append(result)
            return result

        participants = fused_data.get("participants", [])
        if not isinstance(participants, list):
            participants = []

        audio = fused_data.get("audio", {})
        if not isinstance(audio, dict):
            audio = {}

        components = {}
        explanations = []
        missing = []

        # Presence: based on the proportion of tracked participants
        # whose supplied status is Present.
        if participants:
            present_count = sum(
                1 for p in participants
                if isinstance(p, dict)
                and str(p.get("status", "")).lower() == "present"
            )
            components["presence"] = present_count / len(participants)
            explanations.append(
                f"{present_count} of {len(participants)} tracked "
                "participants have status Present."
            )
        else:
            missing.append("participant presence")
            explanations.append("No participant status data was supplied.")

        # Movement: expected optional field in fused_data:
        # movement_frequency, normalized to the range 0..1.
        movement = self._safe_number(
            fused_data.get("movement_frequency")
        )
        if movement is not None:
            components["movement"] = self._clamp(movement)
            explanations.append(
                "Movement component uses the supplied normalized "
                "movement_frequency."
            )
        else:
            missing.append("movement frequency")

        # Speech activity: prefer a speech_activity_ratio if a future
        # speech detector provides one. Do not treat sound energy as speech.
        speech = self._safe_number(audio.get("speech_activity_ratio"))
        if speech is not None:
            components["speech"] = self._clamp(speech)
            explanations.append(
                "Speech component uses the supplied speech activity ratio."
            )
        else:
            missing.append("speech activity")
            explanations.append(
                "Speech activity was not supplied; active sound alone "
                "is not proof of speech."
            )

        # Inactivity: expected optional duration in seconds.
        inactivity = self._safe_number(
            fused_data.get("inactivity_duration_seconds")
        )
        if inactivity is not None:
            inactivity = max(0.0, inactivity)
            components["inactivity"] = 1.0 - self._clamp(
                inactivity / self.inactivity_limit_seconds
            )
            explanations.append(
                f"Inactivity duration was compared with the "
                f"{self.inactivity_limit_seconds:g}-second limit."
            )
        else:
            missing.append("inactivity duration")

        # Renormalize weights over available signals only.
        available_weight = sum(
            self.weights[name] for name in components
        )

        if available_weight <= 0:
            result = {
                "timestamp": fused_data.get("fusion_timestamp"),
                "score": None,
                "level": "Unavailable",
                "reason": "No scoring components are available.",
                "components": components,
                "missing_signals": missing,
                "explanations": explanations,
            }
            self.temporal_profile.append(result)
            return result

        score = 100.0 * sum(
            components[name] * self.weights[name]
            for name in components
        ) / available_weight

        if score >= 70:
            level = "High activity signal"
        elif score >= 40:
            level = "Moderate activity signal"
        else:
            level = "Low activity signal"

        result = {
            "timestamp": (
                fused_data.get("vision_timestamp")
                or fused_data.get("fusion_timestamp")
            ),
            "score": round(score, 2),
            "level": level,
            "components": {
                key: round(value, 3)
                for key, value in components.items()
            },
            "missing_signals": missing,
            "explanations": explanations,
            "interpretation": (
                "This score summarizes available activity signals. "
                "It is not a validated measure of student engagement."
            ),
        }

        self.temporal_profile.append(result)
        return result

    def get_temporal_profile(self):
        """Return scores in the order segments were analyzed."""
        return list(self.temporal_profile)

    def get_session_summary(self):
        """Summarize available segment scores over time."""
        scored = [
            item for item in self.temporal_profile
            if item.get("score") is not None
        ]

        if not scored:
            return {
                "segments_analyzed": len(self.temporal_profile),
                "segments_scored": 0,
                "average_score": None,
                "message": "No segments had enough data to calculate a score.",
            }

        scores = [item["score"] for item in scored]
        return {
            "segments_analyzed": len(self.temporal_profile),
            "segments_scored": len(scored),
            "average_score": round(sum(scores) / len(scores), 2),
            "highest_score": max(scores),
            "lowest_score": min(scores),
            "message": (
                "Summary of rule-based activity proxy scores, "
                "not a validated engagement measurement."
            ),
        }
