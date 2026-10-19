
import cv2

from backend.core.camera_service import CameraService
from backend.core.face_detection import FaceDetector
from backend.core.face_tracking import FaceTracker
from backend.core.attendance import AttendanceManager


def main():
    camera = CameraService(camera_id=0)
    detector = FaceDetector()
    tracker = FaceTracker(max_missing_frames=10)
    attendance = AttendanceManager(
        threshold_seconds=60,
        output_dir="attendance_logs",
    )

    try:
        tracker.reset()
        attendance.reset()
        camera.start()

        print("Attendance started. Press Q to quit.")

        while True:
            frame = camera.get_frame()

            if frame is None:
                print("Could not read camera frame.")
                break

            detections = detector.process_frame(frame)
            tracks = tracker.update(detections)

            visible_ids = [
                track["participant_id"] for track in tracks
            ]
            records = attendance.update(visible_ids)

            for track in tracks:
                x, y, w, h = track["bbox"]
                pid = track["participant_id"]
                record = records.get(pid, {})

                label = (
                    f"{pid} | {record.get('status', 'Pending')} | "
                    f"{record.get('presence_duration_seconds', 0):.1f}s"
                )

                cv2.rectangle(
                    frame, (x, y), (x + w, y + h),
                    (0, 200, 160), 2
                )
                cv2.putText(
                    frame, label, (x, max(20, y - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    (0, 200, 160), 2
                )

            cv2.imshow("Attendance System - Press Q to Quit", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    finally:
        camera.stop()
        cv2.destroyAllWindows()

        records = attendance.finish()

        print("\nFinal attendance:")
        for record in records.values():
            print(record)

        print("\nCSV saved to:", attendance.csv_path)


if __name__ == "__main__":
    main()
