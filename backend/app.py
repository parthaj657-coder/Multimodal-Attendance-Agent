
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
websocket_lock = asyncio.Lock()
session_running = False


@app.get("/")
def home():
    return {
        "message": "Attendance API is running",
        "status": "ready",
    }


@app.post("/attendance/start")
async def start_attendance():
    global session_running

    async with camera_lock:
        if session_running:
            return {"message": "Attendance session is already running"}

        try:
            tracker.reset()
            attendance.reset()
            await asyncio.to_thread(camera.start)
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Could not start attendance: {exc}",
            ) from exc

        session_running = True

    return {
        "message": "Attendance session started",
        "websocket": "/ws/attendance",
    }


@app.get("/attendance")
def get_attendance():
    return {
        "participants": list(attendance.get_attendance().values()),
        "csv_path": attendance.csv_path,
    }


@app.post("/attendance/stop")
async def stop_attendance():
    global session_running

    async with camera_lock:
        if not session_running:
            return {"message": "No active attendance session"}

        session_running = False

        await asyncio.to_thread(camera.stop)
        records = attendance.finish()

    return {
        "message": "Attendance session stopped",
        "participants": list(records.values()),
        "csv_path": attendance.csv_path,
    }


@app.websocket("/ws/attendance")
async def attendance_websocket(websocket: WebSocket):
    await websocket.accept()

    # Only one WebSocket may process frames from this camera at a time.
    try:
        async with websocket_lock:
            while True:
                if not session_running:
                    await websocket.send_json({
                        "status": "stopped",
                        "message": "Start the session using POST /attendance/start",
                    })
                    await asyncio.sleep(1)
                    continue

                async with camera_lock:
                    if not session_running:
                        continue

                    frame = await asyncio.to_thread(camera.get_frame)

                if frame is None:
                    await websocket.send_json({
                        "status": "error",
                        "message": "Could not read a camera frame",
                    })
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
                records = attendance.update(
                    visible_ids, timestamp=now
                )

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

                # Metadata only; the video frame is not sent to the browser.
                await websocket.send_json({
                    "status": "running",
                    "timestamp": now,
                    "participants": list(records.values()),
                })

                await asyncio.sleep(0.03)

    except WebSocketDisconnect:
        pass


@app.on_event("shutdown")
def shutdown_event():
    global session_running

    camera.stop()

    if session_running:
        attendance.finish()

    session_running = False
