
import csv
import time
import uuid
from datetime import datetime
from pathlib import Path


class AttendanceManager:
    def __init__(self, threshold_seconds=60, output_dir="attendance_logs"):
        self.threshold_seconds = threshold_seconds
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.csv_path = str(self.output_dir / "attendance_log.csv")
        self.history_fields = [
            "session_id",
            "participant_id",
            "status",
            "presence_duration_seconds",
            "session_started_at",
            "session_ended_at",
        ]

        self.session_id = None
        self.session_started_at = None
        self.records = {}
        self.session_finished = True
        self.reset()

    def reset(self):
        """Start a fresh in-memory session without deleting saved history."""
        self.session_id = uuid.uuid4().hex[:8].upper()
        self.session_started_at = datetime.now().isoformat(timespec="seconds")
        self.records = {}
        self.session_finished = False

    def update(self, visible_ids, timestamp=None):
        """Update cumulative presence for currently visible participant IDs."""
        now = time.monotonic() if timestamp is None else timestamp
        visible_ids = set(visible_ids)

        for participant_id in visible_ids:
            if participant_id not in self.records:
                self.records[participant_id] = {
                    "participant_id": participant_id,
                    "status": "Pending",
                    "presence_duration_seconds": 0.0,
                    "_first_seen": now,
                    "_last_seen": now,
                    "_accumulated_seconds": 0.0,
                }

            record = self.records[participant_id]
            last_seen = record["_last_seen"]
            gap = max(0.0, now - last_seen)

            # Count only short gaps as continuous presence. This avoids
            # adding a long period when a participant disappears.
            if participant_id in visible_ids:
                if gap <= 2.0:
                    record["_accumulated_seconds"] += gap
                else:
                    # Resume counting after a long disappearance.
                    record["_first_seen"] = now

            record["_last_seen"] = now
            record["presence_duration_seconds"] = round(
                record["_accumulated_seconds"], 1
            )
            record["status"] = (
                "Present"
                if record["presence_duration_seconds"] >= self.threshold_seconds
                else "Pending"
            )

        return self.get_attendance()

    def get_attendance(self):
        """Return current session records without internal tracking fields."""
        result = {}
        for participant_id, record in self.records.items():
            result[participant_id] = {
                key: value
                for key, value in record.items()
                if not key.startswith("_")
            }
        return result

    def finish(self):
        """Append this session's records to history without replacing old rows."""
        if self.session_finished:
            return self.get_attendance()

        records = self.get_attendance()
        ended_at = datetime.now().isoformat(timespec="seconds")
        file_exists = Path(self.csv_path).exists()
        needs_header = (
            not file_exists or Path(self.csv_path).stat().st_size == 0
        )

        try:
            with open(self.csv_path, "a", newline="", encoding="utf-8-sig") as file:
                writer = csv.DictWriter(file, fieldnames=self.history_fields)

                if needs_header:
                    writer.writeheader()

                for participant in records.values():
                    writer.writerow({
                        "session_id": self.session_id,
                        "participant_id": participant["participant_id"],
                        "status": participant["status"],
                        "presence_duration_seconds":
                            participant["presence_duration_seconds"],
                        "session_started_at": self.session_started_at,
                        "session_ended_at": ended_at,
                    })
        except PermissionError as exc:
            raise PermissionError(
                f"Cannot write {self.csv_path}. Close the CSV in Excel "
                "or another application, then stop the session again."
            ) from exc

        self.session_finished = True
        return records
