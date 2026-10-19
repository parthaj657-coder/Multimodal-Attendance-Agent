
import cv2


class CameraService:
    def __init__(self, camera_id=0):
        self.camera_id = camera_id
        self.cap = None
        self.is_running = False

    def start(self):
        if self.is_running:
            return

        cap = cv2.VideoCapture(self.camera_id)

        if not cap.isOpened():
            cap.release()
            raise RuntimeError(
                f"Could not open camera {self.camera_id}. "
                "Check that the webcam is connected and not in use."
            )

        self.cap = cap
        self.is_running = True

    def get_frame(self):
        if not self.is_running or self.cap is None:
            return None

        success, frame = self.cap.read()

        if not success:
            return None

        return frame

    def stop(self):
        if self.cap is not None:
            self.cap.release()

        self.cap = None
        self.is_running = False
