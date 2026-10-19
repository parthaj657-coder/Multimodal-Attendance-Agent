
class AISuggestionEngine:
    """Generate explainable classroom suggestions from fused data."""

    def generate_suggestions(self, session_data):
        if not isinstance(session_data, dict):
            return self._fallback_suggestions()

        fusion_status = session_data.get("fusion_status")

        if fusion_status != "Synchronized":
            return {
                "assessment": "Incomplete multimodal evidence",
                "suggestions": [
                    "Check that vision and audio timestamps are available "
                    "and aligned before interpreting classroom activity."
                ],
                "evidence": [
                    f"Fusion status: {fusion_status or 'Unknown'}"
                ],
            }

        suggestions = []
        evidence = []

        participants = session_data.get("participants", [])
        participant_count = session_data.get("participant_count", 0)
        audio = session_data.get("audio", {})

        if participant_count > 0:
            evidence.append(
                f"{participant_count} tracked participant(s) in the "
                "vision snapshot."
            )
        else:
            suggestions.append(
                "Check camera framing and face detection before drawing "
                "conclusions about attendance."
            )
            evidence.append("No tracked participants in this snapshot.")

        activity = str(audio.get("activity", "Unknown"))
        active_ratio = audio.get("active_sound_ratio")

        if activity == "Silence":
            evidence.append("The audio module classified this segment as silence.")
            suggestions.append(
                "Review the lesson context to determine whether a quiet "
                "period is expected."
            )
        elif activity == "Background noise":
            evidence.append(
                "The audio module classified this segment as background noise."
            )
            suggestions.append(
                "Consider reducing background noise if it interferes "
                "with classroom communication."
            )
        elif activity == "Active sound":
            evidence.append(
                "The audio module detected active sound; this does not "
                "confirm that speech is present."
            )
            suggestions.append(
                "Review the audio segment if you need to determine whether "
                "the sound is speech, music, or another source."
            )
        else:
            evidence.append("Audio activity is unknown or unavailable.")
            suggestions.append(
                "Check audio input and preprocessing before interpreting "
                "the sound activity."
            )

        if isinstance(active_ratio, (int, float)):
            evidence.append(
                f"Active-sound ratio: {active_ratio:.3f}."
            )

        if not suggestions:
            suggestions.append(
                "Continue collecting aligned observations to assess "
                "changes over the session."
            )

        return {
            "assessment": (
                "Observations combined; engagement cannot be established "
                "from face presence and sound activity alone."
            ),
            "suggestions": suggestions,
            "evidence": evidence,
        }

    @staticmethod
    def _fallback_suggestions():
        return {
            "assessment": "Insufficient data",
            "suggestions": [
                "Provide valid fused vision and audio data before "
                "generating suggestions."
            ],
            "evidence": [],
        }
