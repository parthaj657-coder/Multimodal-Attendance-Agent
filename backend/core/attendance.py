
import csv
import os
import time
from datetime import datetime, timezone


class AttendanceManager:
    def __init__(
        self,
        threshold_seconds=60,
        output_dir="attendance_logs",
    ):
        if threshold_seconds < 0:
            raise ValueError("Threshold cannot be negative.")

        self.threshold_seconds = float(threshold_seconds)
        self.output_dir = os.path.abspath(output_dir)
        os.makedirs(self.output_dir, exist_ok=True)

        self.csv_path = os.path.join(
            self.output_dir, "attendance_log.csv"
        )

        self.total_seconds = {}
        self.active_since = {}
        self.last_timestamp = None

        self._write_csv({})

    def reset(self):
        """Reset accumulated attendance for a new session."""
        self.total_seconds.clear()
        self.active_since.clear()
        self.last_timestamp = None
        self._write_csv({})

    def update(self, visible_ids, timestamp=None):
        now = time.monotonic() if timestamp is None else float(timestamp)

        if (
            self.last_timestamp is not None
            and now < self.last_timestamp
        ):
            raise ValueError("Timestamp cannot move backwards.")

        visible_ids = {
            str(pid).strip()
            for pid in visible_ids
            if pid is not None and str(pid).strip()
        }

        # Close intervals for participants no longer visible.
        for pid in list(self.active_since):
            if pid not in visible_ids:
                started = self.active_since.pop(pid)
                elapsed = max(0.0, now - started)
                self.total_seconds[pid] = (
                    self.total_seconds.get(pid, 0.0) + elapsed
                )

        # Start intervals for newly visible participants.
        for pid in visible_ids:
            if pid not in self.active_since:
                self.active_since[pid] = now
                self.total_seconds.setdefault(pid, 0.0)

        self.last_timestamp = now
        records = self.get_attendance(now)
        self._write_csv(records)
        return records

    def _duration(self, pid, now):
        duration = self.total_seconds.get(pid, 0.0)

        if pid in self.active_since:
            duration += max(0.0, now - self.active_since[pid])

        return duration

    def get_attendance(self, timestamp=None):
        now = (
            time.monotonic()
            if timestamp is None
            else float(timestamp)
        )

        participant_ids = (
            set(self.total_seconds) | set(self.active_since)
        )
        records = {}

        for pid in sorted(participant_ids):
            duration = self._duration(pid, now)

            records[pid] = {
                "participant_id": pid,
                "presence_duration_seconds": round(duration, 2),
                "presence_duration_minutes": round(
                    duration / 60.0, 2
                ),
                "status": (
                    "Present"
                    if duration >= self.threshold_seconds
                    else "Pending"
                ),
            }

        return records

    def _write_csv(self, records):
        updated = datetime.now(timezone.utc).isoformat()

        with open(
            self.csv_path,
            "w",
            newline="",
            encoding="utf-8",
        ) as file:
            writer = csv.writer(file)
            writer.writerow([
                "participant_id",
                "presence_duration_seconds",
                "presence_duration_minutes",
                "status",
                "last_updated_utc",
            ])

            for pid, record in sorted(records.items()):
                writer.writerow([
                    pid,
                    record["presence_duration_seconds"],
                    record["presence_duration_minutes"],
                    record["status"],
                    updated,
                ])

    def finish(self, timestamp=None):
        now = time.monotonic() if timestamp is None else float(timestamp)

        if (
            self.last_timestamp is not None
            and now < self.last_timestamp
        ):
            raise ValueError("Timestamp cannot move backwards.")

        # Close all active intervals.
        for pid, started in list(self.active_since.items()):
            self.total_seconds[pid] = (
                self.total_seconds.get(pid, 0.0)
                + max(0.0, now - started)
            )

        self.active_since.clear()
        self.last_timestamp = now

        records = self.get_attendance(now)
        self._write_csv(records)
        return records
