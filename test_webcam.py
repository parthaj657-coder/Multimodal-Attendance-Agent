
import cv2
import time

def open_webcam():
    # Try different Windows camera backends and camera indexes
    camera_options = [
        (0, cv2.CAP_DSHOW, "DirectShow"),
        (0, cv2.CAP_MSMF, "Media Foundation"),
        (1, cv2.CAP_DSHOW, "DirectShow - Camera 1"),
        (1, cv2.CAP_MSMF, "Media Foundation - Camera 1"),
    ]

    camera = None

    for index, backend, name in camera_options:
        print(f"Trying camera {index} using {name}...")

        cap = cv2.VideoCapture(index, backend)

        if cap.isOpened():
            # Give the camera time to initialize
            time.sleep(1)

            success, frame = cap.read()

            if success and frame is not None:
                print(f"SUCCESS: Webcam opened using {name}.")
                camera = cap
                break

        cap.release()

    return camera


def main():
    camera = open_webcam()

    if camera is None:
        print("\nERROR: Could not open or read from any tested camera.")
        print("Check Windows camera permissions and close other camera apps.")
        return

    print("\nLive webcam preview started.")
    print("Press Q in the preview window to close it.")

    try:
        while True:
            success, frame = camera.read()

            if not success or frame is None:
                print("ERROR: Could not read a webcam frame.")
                break

            cv2.imshow("Webcam Test - Press Q to Close", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    except KeyboardInterrupt:
        print("\nWebcam test interrupted.")

    finally:
        camera.release()
        cv2.destroyAllWindows()
        print("Webcam test finished.")


if __name__ == "__main__":
    main()
