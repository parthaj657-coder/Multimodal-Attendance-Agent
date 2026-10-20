
import csv
from pathlib import Path

csv_path = Path("attendance_logs/attendance_log.csv")
backup_path = Path("attendance_logs/attendance_log_backup.csv")

if not csv_path.exists():
    raise FileNotFoundError(f"Attendance file not found: {csv_path}")

if not backup_path.exists():
    raise FileNotFoundError("Backup file not found. Migration cancelled.")

new_fields = [
    "session_id",
    "participant_id",
    "status",
    "presence_duration_seconds",
    "session_started_at",
    "session_ended_at",
]

with csv_path.open("r", newline="", encoding="utf-8-sig") as file:
    rows = list(csv.reader(file))

if not rows:
    print("Attendance file is empty. Nothing to migrate.")
    raise SystemExit(0)

normalized = []

for row in rows[1:]:
    if not row or not any(value.strip() for value in row):
        continue

    if len(row) == 5:
        participant_id, seconds, minutes, status, updated_at = row
        normalized.append({
            "session_id": "LEGACY",
            "participant_id": participant_id,
            "status": status,
            "presence_duration_seconds": seconds,
            "session_started_at": updated_at,
            "session_ended_at": updated_at,
        })

    elif len(row) == 6:
        session_id, participant_id, status, seconds, started, ended = row
        normalized.append({
            "session_id": session_id,
            "participant_id": participant_id,
            "status": status,
            "presence_duration_seconds": seconds,
            "session_started_at": started,
            "session_ended_at": ended,
        })

    else:
        print(f"Unrecognized row; preserving it in the backup: {row}")

with csv_path.open("w", newline="", encoding="utf-8-sig") as file:
    writer = csv.DictWriter(file, fieldnames=new_fields)
    writer.writeheader()
    writer.writerows(normalized)

print(f"Migration complete: {len(normalized)} records normalized.")
print(f"Backup preserved: {backup_path}")
