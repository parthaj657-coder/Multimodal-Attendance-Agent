
import cv2

camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("ERROR: Could not open webcam.")
else:
    print("Webcam opened successfully.")
    print("A preview window should appear. Press Q to close it.")

    try:
        while True:
            success, frame = camera.read()

            if not success:
                print("ERROR: Could not read webcam frame.")
                break

            cv2.imshow("Webcam Test - Press Q to Close", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        camera.release()
        cv2.destroyAllWindows()

print("Webcam test finished.")
