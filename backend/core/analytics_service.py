
from collections import defaultdict
from datetime import datetime, timezone


class AnalyticsService:
    """Create individual student analytics from supplied session records."""

    def get_session_trends(self, session_id, metrics=None):
        """
        Expected metric format:
        {
            "timestamp": 100.0,
            "participant_id": "P0001",
            "presence_duration_seconds": 75,
            "engagement_score": 82.5
        }

        Timestamps may be Unix seconds, ISO strings, or numeric seconds.
        """
        metrics = metrics or []

        participant_data = defaultdict(list)

        for metric in metrics:
            if not isinstance(metric, dict):
                continue

            if metric.get("session_id", session_id) != session_id:
                continue

            participant_id = metric.get("participant_id")
            if not participant_id:
                continue

            participant_data[str(participant_id)].append(metric)

        results = {}

        for participant_id, entries in participant_data.items():
            entries.sort(
                key=lambda item: self._timestamp_key(item.get("timestamp"))
            )

            scores = []
            timeline = []
            attendance_duration = 0.0

            for entry in entries:
                score = self._number(entry.get("engagement_score"))
                if score is not None and 0 <= score <= 100:
                    scores.append(score)

                duration = self._number(
                    entry.get("presence_duration_seconds")
                )
                if duration is not None:
                    attendance_duration = max(
                        attendance_duration, max(0.0, duration)
                    )

                timeline.append({
                    "timestamp": entry.get("timestamp"),
                    "engagement_score": score,
                    "activity": entry.get("activity", "Not specified"),
                })

            average_score = (
                round(sum(scores) / len(scores), 2) if scores else None
            )

            score_change = (
                round(scores[-1] - scores[0], 2)
                if len(scores) >= 2 else None
            )

            results[participant_id] = {
                "participant_id": participant_id,
                "attendance_duration_seconds": round(
                    attendance_duration, 2
                ),
                "attendance_duration_minutes": round(
                    attendance_duration / 60, 2
                ),
                "engagement_score_average": average_score,
                "engagement_score_change": score_change,
                "timeline": timeline,
                "reflection": self._reflection(
                    average_score, score_change
                ),
            }

        return {
            "session_id": session_id,
            "participants": results,
            "participants_analyzed": len(results),
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "note": (
                "Scores are activity indicators, not grades or validated "
                "measures of attention, learning, or ability. "
                "No peer ranking is performed."
            ),
        }

    @staticmethod
    def _number(value):
        try:
            number = float(value)
            if number != number or abs(number) == float("inf"):
                return None
            return number
        except (TypeError, ValueError):
            return None

    @classmethod
    def _timestamp_key(cls, value):
        """Convert supported timestamps into a sortable numeric key."""
        number = cls._number(value)
        if number is not None:
            return number

        if isinstance(value, str):
            try:
                parsed = datetime.fromisoformat(
                    value.replace("Z", "+00:00")
                )
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                return parsed.timestamp()
            except ValueError:
                pass

        return float("inf")

    @staticmethod
    def _reflection(average_score, score_change):
        if average_score is None:
            return (
                "There is not enough scored activity data for a trend "
                "summary yet."
            )

        if score_change is not None and score_change >= 10:
            return (
                "Your activity indicators increased across the recorded "
                "segments. Reflect on what was happening during those times."
            )

        if score_change is not None and score_change <= -10:
            return (
                "Your activity indicators decreased across the recorded "
                "segments. Consider whether a break or different learning "
                "activity might be helpful."
            )

        return (
            "Your recorded activity indicators were relatively stable. "
            "Use the timeline to reflect on which lesson activities "
            "worked best for you."
        )
