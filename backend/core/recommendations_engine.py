
class RecommendationsEngine:
    """Generate explainable, rule-based classroom recommendations."""

    def generate_realtime_recommendations(self, session_status):
        if not isinstance(session_status, dict):
            return [{
                "type": "warning",
                "message": "Session data is invalid. Check the input."
            }]

        recommendations = []
        people = session_status.get("people", [])

        # Check individual activity scores when provided.
        valid_scores = []
        for person in people if isinstance(people, list) else []:
            if not isinstance(person, dict):
                continue

            try:
                score = float(person["attention"])
            except (KeyError, TypeError, ValueError):
                continue

            valid_scores.append(score)

            if score < 40:
                recommendations.append({
                    "type": "alert",
                    "message": (
                        f"Participant {person.get('id', 'Unknown')} has "
                        f"a low activity proxy score ({score:.1f}). "
                        "Consider a brief interactive check-in."
                    )
                })

        # Check overall activity when individual scores are available.
        if valid_scores:
            average_score = sum(valid_scores) / len(valid_scores)

            if len(valid_scores) > 2 and average_score < 60:
                recommendations.append({
                    "type": "warning",
                    "message": (
                        f"The average activity proxy score is "
                        f"{average_score:.1f}. Consider a short discussion, "
                        "question, or interactive activity."
                    )
                })

        # Check trends from temporal scoring results.
        trend = session_status.get("engagement_trend", [])
        if isinstance(trend, list) and len(trend) >= 2:
            try:
                previous = float(trend[-2])
                current = float(trend[-1])

                if previous - current >= 15:
                    recommendations.append({
                        "type": "warning",
                        "message": (
                            "The activity proxy score dropped noticeably "
                            "between recent segments. Consider checking "
                            "whether a change of pace would help."
                        )
                    })
                elif current - previous >= 15:
                    recommendations.append({
                        "type": "info",
                        "message": (
                            "The activity proxy score increased between "
                            "recent segments. Review what changed in the "
                            "lesson during that period."
                        )
                    })
            except (TypeError, ValueError):
                pass

        # Sound classification is not proof of speech.
        audio_activity = session_status.get("audio_activity")
        if audio_activity == "Background noise":
            recommendations.append({
                "type": "warning",
                "message": (
                    "Background noise was detected by the audio module. "
                    "Check the room or microphone if it is disrupting "
                    "classroom communication."
                )
            })

        if not recommendations:
            recommendations.append({
                "type": "info",
                "message": (
                    "No rule-based alerts were triggered. Continue "
                    "reviewing the session context and collected metrics."
                )
            })

        return recommendations
