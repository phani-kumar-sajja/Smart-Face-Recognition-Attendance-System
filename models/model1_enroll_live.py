import cv2
import os
import face_recognition
import sqlite3

def process_live_enrollment(student_info):
    save_dir = f'static/faces/{student_info["student_id"]}'
    os.makedirs(save_dir, exist_ok=True)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Camera not available")

    print("[INFO] Starting webcam for live enrollment...")
    saved_faces = 0
    frame_count = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        cv2.imshow("Live Enrollment - Press Q to Quit", frame)

        frame_count += 1
        if frame_count % 10 != 0:
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            continue

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        locations = face_recognition.face_locations(rgb)
        encodings = face_recognition.face_encodings(rgb, locations)

        for top, right, bottom, left in locations:
            face = frame[top:bottom, left:right]
            if face.size == 0:
                continue
            face_path = os.path.join(save_dir, f"{student_info['student_id']}_{saved_faces}.jpg")
            cv2.imwrite(face_path, face)
            print(f"[INFO] Saved: {face_path}")
            saved_faces += 1
            if saved_faces >= 20:
                break

        if saved_faces >= 20:
            break
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    # Save student info to DB
    conn = sqlite3.connect('database/users.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            class TEXT NOT NULL,
            branch TEXT NOT NULL
        )
    ''')
    c.execute("INSERT OR REPLACE INTO students (id, name, class, branch) VALUES (?, ?, ?, ?)",
              (student_info["student_id"], student_info["name"],
               student_info["student_class"], student_info["branch"]))
    conn.commit()
    conn.close()


    def save_enroll_snapshot(frame, student_info):
    from datetime import datetime
    model = YOLO("Yolo_model_1/my_model.pt")

    save_dir = f"static/faces/{student_info['student_id']}"
    os.makedirs(save_dir, exist_ok=True)

    results = model(frame)
    face_saved = False

    for r in results:
        for box in r.boxes:
            cls = int(box.cls[0])
            label = model.names[cls].lower()
            if 'face' in label or 'person' in label:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                face = frame[y1:y2, x1:x2]
                if face.size == 0:
                    continue

                count = len(os.listdir(save_dir))
                if count >= 10:
                    return "✔️ Already saved 10 faces."

                face_path = os.path.join(save_dir, f"{student_info['student_id']}_{count}.jpg")
                cv2.imwrite(face_path, face)
                face_saved = True
                break

    # Save student info once
    if face_saved and count == 0:
        conn = sqlite3.connect('database/users.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS students (
            id TEXT PRIMARY KEY,
            name TEXT,
            class TEXT,
            branch TEXT)''')
        c.execute("INSERT OR REPLACE INTO students (id, name, class, branch) VALUES (?, ?, ?, ?)",
                  (student_info['student_id'], student_info['name'], student_info['student_class'], student_info['branch']))
        conn.commit()
        conn.close()

    return "✅ Face captured" if face_saved else "❌ No face detected"

