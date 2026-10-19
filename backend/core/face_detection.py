
import cv2


class FaceDetector:
    def __init__(
        self,
        scale_factor=1.1,
        min_neighbors=5,
        min_size=(30, 30),
    ):
        cascade_path = (
            cv2.data.haarcascades
            + "haarcascade_frontalface_default.xml"
        )
        self.face_cascade = cv2.CascadeClassifier(cascade_path)

        if self.face_cascade.empty():
            raise RuntimeError(
                "OpenCV could not load its Haar Cascade file."
            )

        self.scale_factor = scale_factor
        self.min_neighbors = min_neighbors
        self.min_size = min_size

    def process_frame(self, frame):
        """Return face detections from one OpenCV BGR frame."""
        if frame is None:
            return []

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=self.scale_factor,
            minNeighbors=self.min_neighbors,
            minSize=self.min_size,
        )

        return [
            {
                "bbox": (int(x), int(y), int(w), int(h)),
                "score": 1.0,
            }
            for x, y, w, h in faces
        ]
