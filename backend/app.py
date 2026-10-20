
import asyncio
import time

import cv2
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect

from backend.core.camera_service import CameraService
from backend.core.face_detection import FaceDetector
from backend.core.face_tracking import FaceTracker
from backend.core.attendance import AttendanceManager


app = FastAPI(
    title="Multimodal Attendance & Engagement Agent",
    version="1.0.0",
)

camera = CameraService(camera_id=0)
detector = FaceDetector()
tracker = FaceTracker(max_missing_frames=10)
attendance = AttendanceManager(
    threshold_seconds=60,
    output_dir="attendance_logs",
)

camera_lock = asyncio.Lock()
session_running = False
camera_task = None


async def process_camera():
    """Continuously read the webcam and update attendance."""
    global session_running

    try:
        while session_running:
            async with camera_lock:
                if not session_running:
                    break
                frame = await asyncio.to_thread(camera.get_frame)

            if frame is None:
                await asyncio.sleep(0.1)
                continue

            now = time.monotonic()

            detections = await asyncio.to_thread(
                detector.process_frame, frame
            )
            tracks = tracker.update(detections, timestamp=now)

            visible_ids = [
                track["participant_id"] for track in tracks
            ]
            records = attendance.update(visible_ids, timestamp=now)

            for track in tracks:
                x, y, w, h = track["bbox"]
                pid = track["participant_id"]
                record = records.get(pid, {})

                label = (
                    f"{pid} | {record.get('status', 'Pending')} | "
                    f"{record.get('presence_duration_seconds', 0):.1f}s"
                )

                cv2.rectangle(
                    frame, (x, y), (x + w, y + h), (0, 200, 160), 2
                )
                cv2.putText(
                    frame, label, (x, max(20, y - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 160), 2
                )

            cv2.imshow("Live Attendance - Press Q to close preview", frame)

            # Q closes the preview and stops the attendance session.
            if cv2.waitKey(1) & 0xFF == ord("q"):
                session_running = False
                break

            await asyncio.sleep(0.01)

    except asyncio.CancelledError:
        pass
    finally:
        cv2.destroyAllWindows()


@app.get("/")
def home():
    return {"message": "Attendance API is running", "status": "ready"}


@app.post("/attendance/start")
async def start_attendance():
    global session_running, camera_task

    async with camera_lock:
        if session_running:
            return {"message": "Attendance session is already running"}

        try:
            tracker.reset()
            attendance.reset()
            await asyncio.to_thread(camera.start)
            session_running = True
            camera_task = asyncio.create_task(process_camera())
        except Exception as exc:
            session_running = False
            await asyncio.to_thread(camera.stop)
            raise HTTPException(
                status_code=500,
                detail=f"Could not start attendance: {exc}",
            ) from exc

    return {"message": "Attendance session started", "preview": "Opening webcam window"}


@app.get("/attendance")
def get_attendance():
    return {
        "participants": list(attendance.get_attendance().values()),
        "csv_path": attendance.csv_path,
    }


@app.post("/attendance/stop")
async def stop_attendance():
    global session_running, camera_task

    async with camera_lock:
        if not session_running:
            return {"message": "No active attendance session"}

        session_running = False

    if camera_task is not None:
        camera_task.cancel()
        await asyncio.gather(camera_task, return_exceptions=True)
        camera_task = None

    async with camera_lock:
        await asyncio.to_thread(camera.stop)
        records = attendance.finish()

    cv2.destroyAllWindows()

    return {
        "message": "Attendance session stopped",
        "participants": list(records.values()),
        "csv_path": attendance.csv_path,
    }


@app.websocket("/ws/attendance")
async def attendance_websocket(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            if session_running:
                await websocket.send_json({
                    "status": "running",
                    "participants": list(
                        attendance.get_attendance().values()
                    ),
                })
            else:
                await websocket.send_json({
                    "status": "stopped",
                    "message": "Start attendance using POST /attendance/start",
                })

            await asyncio.sleep(1)

    except WebSocketDisconnect:
        pass


@app.on_event("shutdown")
async def shutdown_event():
    global session_running, camera_task

    session_running = False

    if camera_task is not None:
        camera_task.cancel()
        await asyncio.gather(camera_task, return_exceptions=True)
        camera_task = None

    await asyncio.to_thread(camera.stop)
    cv2.destroyAllWindows()
