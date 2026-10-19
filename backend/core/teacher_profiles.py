
class TeacherProfileService:
    """Summarize teacher session data supplied by the application."""

    def get_profile(self, teacher_id, sessions=None):
        sessions = sessions or []

        valid_scores = []
        class_history = []

        for session in sessions:
            if not isinstance(session, dict):
                continue

            try:
                score = float(session["engagement"])
            except (KeyError, TypeError, ValueError):
                continue

            if not 0 <= score <= 100:
                continue

            name = session.get("name", "Unnamed session")
            valid_scores.append(score)

            class_history.append({
                "name": name,
                "engagement": round(score, 2),
            })

        average = (
            round(sum(valid_scores) / len(valid_scores), 2)
            if valid_scores else None
        )

        trend = (
            round(valid_scores[-1] - valid_scores[0], 2)
            if len(valid_scores) >= 2 else None
        )

        return {
            "teacher_id": teacher_id,
            "effectiveness_score": average,
            "trend_change": trend,
            "sessions_analyzed": len(valid_scores),
            "class_history": class_history,
            "note": (
                "Scores summarize supplied activity proxy data; "
                "they are not validated measures of teaching effectiveness."
            ),
        }
