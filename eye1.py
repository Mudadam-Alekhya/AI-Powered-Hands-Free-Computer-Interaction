import cv2
import mediapipe as mp
from pynput.mouse import Controller, Button
import time

# Initialize webcam and Face Mesh
cam = cv2.VideoCapture(0)
face_mesh = mp.solutions.face_mesh.FaceMesh(refine_landmarks=True)

# Set screen size (adjust to your resolution)
screen_w, screen_h = 1920, 1080

# Initialize Mouse Controller
mouse = Controller()

# Track last cursor position
last_x, last_y = 0, 0

# Click prevention variables
last_left_click_time = 0
last_right_click_time = 0
click_cooldown = 0.7  # seconds

while cam.isOpened():
    success, frame = cam.read()
    if not success:
        break

    # Flip and convert frame to RGB
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    output = face_mesh.process(rgb_frame)
    frame_h, frame_w, _ = frame.shape

    if output.multi_face_landmarks:
        landmarks = output.multi_face_landmarks[0].landmark

        # Track the gaze points using landmarks 474 to 477
        for idx, landmark in enumerate(landmarks[474:478]):
            x = int(landmark.x * frame_w)
            y = int(landmark.y * frame_h)
            cv2.circle(frame, (x, y), 3, (0, 255, 0), -1)

            if idx == 1:
                # Compute the relative position (0 to 1)
                rel_x = x / frame_w
                rel_y = y / frame_h

                # Amplify the relative movement around the center (0.5)
                amp_factor = 1.8
                new_rel_x = (rel_x - 0.5) * amp_factor + 0.5
                new_rel_y = (rel_y - 0.5) * amp_factor + 0.5

                # Clamp between 0 and 1
                new_rel_x = min(max(new_rel_x, 0), 1)
                new_rel_y = min(max(new_rel_y, 0), 1)

                # Map to full screen coordinates
                screen_x = int(new_rel_x * screen_w)
                screen_y = int(new_rel_y * screen_h)

                # Only update if movement is significant to reduce jitter
                if abs(screen_x - last_x) > 5 or abs(screen_y - last_y) > 5:
                    last_x, last_y = screen_x, screen_y
                    mouse.position = (screen_x, screen_y)

        # Eye landmarks for blink detection
        left_eye = [landmarks[145], landmarks[159]]
        right_eye = [landmarks[374], landmarks[386]]

        # Draw circles on the eye landmarks
        for landmark in left_eye + right_eye:
            x = int(landmark.x * frame_w)
            y = int(landmark.y * frame_h)
            cv2.circle(frame, (x, y), 3, (0, 255, 255), -1)

        current_time = time.time()

        # Left eye → Single click
        if (left_eye[0].y - left_eye[1].y) < 0.015 and (current_time - last_left_click_time > click_cooldown):
            print("Left eye blink → Single Click")
            mouse.click(Button.left, 1)
            last_left_click_time = current_time

        # Right eye → Double click
        if (right_eye[0].y - right_eye[1].y) < 0.015 and (current_time - last_right_click_time > click_cooldown):
            print("Right eye blink → Double Click")
            mouse.click(Button.left, 2)
            last_right_click_time = current_time

    # Display the frame
    cv2.imshow("Eye Controlled Mouse", frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
cam.release()
cv2.destroyAllWindows()
