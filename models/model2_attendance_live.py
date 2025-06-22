import cv2
import face_recognition
import os
import datetime
import csv
import time
import simpleaudio as sa


os.environ["QT_QPA_PLATFORM"] = "xcb"

# keep track of timestamps for each seen student
seen = set()
recent_feedback = {}  # track when we showed them last


import pygame

def play_notification():
    try:
        pygame.mixer.init()
        pygame.mixer.music.load("static/notify.mp3")
        pygame.mixer.music.play()
    except Exception as e:
        print(f"[SOUND ERROR] {e}")



def load_known_faces(face_dir='static/faces'):
    known_encodings = []
    known_ids = []

    for student_id in os.listdir(face_dir):
        student_path = os.path.join(face_dir, student_id)
        for img_name in os.listdir(student_path):
            img_path = os.path.join(student_path, img_name)
            image = face_recognition.load_image_file(img_path)
            encodings = face_recognition.face_encodings(image)
            if encodings:
                known_encodings.append(encodings[0])
                known_ids.append(student_id)

    return known_encodings, known_ids


def mark_attendance_live(subject, output_csv='attendance_logs.csv'):
    import traceback

    try:
        print("[DEBUG] Loading known face encodings...")
        known_encodings, known_ids = load_known_faces()
        seen = set()

        print("[DEBUG] Opening webcam...")
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            raise RuntimeError("Camera not accessible")

        print("[INFO] Scanning faces — click the ❌ icon to stop")
        clicked_close = False

        def on_mouse(event, x, y, flags, param):
            nonlocal clicked_close
            if event == cv2.EVENT_LBUTTONDOWN:
                if 580 <= x <= 620 and 10 <= y <= 40:
                    clicked_close = True

        cv2.namedWindow("Live Attendance")
        cv2.setMouseCallback("Live Attendance", on_mouse)

        while not clicked_close:
            ret, frame = cap.read()
            if not ret:
                print("[ERROR] Failed to read frame.")
                break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb)
            face_encodings = face_recognition.face_encodings(rgb, face_locations)

            current_time = time.time()

            for encoding in face_encodings:
                distances = face_recognition.face_distance(known_encodings, encoding)
                if len(distances) == 0:
                    continue

                best_index = distances.argmin()
                if distances[best_index] < 0.6:
                    student_id = known_ids[best_index]

                    if student_id not in seen:
                        print(f"[MATCHED] New student detected: {student_id}")
                        seen.add(student_id)
                        recent_feedback[student_id] = current_time

                        try:
                            print("[DEBUG] Playing notification sound...")
                            play_notification()
                        except Exception as sound_err:
                            print(f"[ERROR] Sound playback failed: {sound_err}")

                    elif current_time - recent_feedback.get(student_id, 0) < 2:
                        recent_feedback[student_id] = current_time

            # UI drawing
            y_pos = 50
            for sid in seen:
                label = sid
                if current_time - recent_feedback.get(sid, 0) < 2:
                    label += " ✔"
                cv2.putText(frame, label, (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                y_pos += 25

            cv2.rectangle(frame, (580, 10), (620, 40), (0, 0, 255), -1)
            cv2.putText(frame, "X", (590, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

            try:
                cv2.imshow("Live Attendance", frame)
            except Exception as im_err:
                print(f"[ERROR] imshow failed: {im_err}")

            if cv2.waitKey(1) & 0xFF == 27:
                print("[INFO] Escape key pressed.")
                break

        cap.release()
        cv2.destroyAllWindows()
        print("[INFO] Webcam and windows closed.")

        # Save attendance
        print("[DEBUG] Writing attendance log...")
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        existing_records = {}

        if os.path.exists(output_csv):
            with open(output_csv, 'r') as f:
                for row in csv.reader(f):
                    if len(row) >= 3:
                        sid, sub, ts = row[0], row[1], row[2]
                        key = (sid, sub)
                        existing_time = datetime.datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
                        if key not in existing_records or existing_time > existing_records[key]:
                            existing_records[key] = existing_time

        current_time = datetime.datetime.now()

        with open(output_csv, 'a', newline='') as f:
            writer = csv.writer(f)
            for sid in seen:
                key = (sid, subject)
                if key not in existing_records:
                    writer.writerow([sid, subject, current_time.strftime("%Y-%m-%d %H:%M:%S")])
                    print(f"[LOGGED] {sid} at {subject}")
                else:
                    time_diff = current_time - existing_records[key]
                    if time_diff.total_seconds() >= 3600:
                        writer.writerow([sid, subject, current_time.strftime("%Y-%m-%d %H:%M:%S")])
                        print(f"[LOGGED] {sid} again at {subject}")

        return seen

    except Exception as e:
        print("[FATAL ERROR] mark_attendance_live crashed:")
        traceback.print_exc()
        raise


import face_recognition
from datetime import datetime
import os
import csv

def mark_attendance_browser(frame, subject, log_csv='attendance_logs.csv'):
    known_encodings, known_ids = load_known_faces()
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    encodings = face_recognition.face_encodings(rgb)

    for encoding in encodings:
        matches = face_recognition.compare_faces(known_encodings, encoding)
        if True in matches:
            index = matches.index(True)
            sid = known_ids[index]

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            key = (sid, subject)

            existing = {}
            if os.path.exists(log_csv):
                with open(log_csv, 'r') as f:
                    for row in csv.reader(f):
                        if len(row) >= 3:
                            existing[(row[0], row[1])] = row[2]

            # Avoid duplicate logging within 1 hour
            now = datetime.now()
            if key not in existing or (now - datetime.strptime(existing[key], "%Y-%m-%d %H:%M:%S")).total_seconds() > 3600:
                with open(log_csv, 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([sid, subject, timestamp])
            return sid

    return None

