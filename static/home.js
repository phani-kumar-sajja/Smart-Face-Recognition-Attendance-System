const container = document.querySelector('.container');
const registerBtn = document.querySelector('.register-btn');
const loginBtn = document.querySelector('.login-btn');

registerBtn.addEventListener('click', () => {
    container.classList.add('active');
})

loginBtn.addEventListener('click', () => {
    container.classList.remove('active');
})

document.addEventListener("DOMContentLoaded", () => {
  const userIcon = document.getElementById("user-icon");
  const dropdownMenu = document.getElementById("dropdown-menu");

  userIcon.addEventListener("click", () => {
    dropdownMenu.style.display = dropdownMenu.style.display === "block" ? "none" : "block";
  });

  // Optional: Hide menu if clicked outside
  document.addEventListener("click", (e) => {
    if (!e.target.closest(".user-dropdown")) {
      dropdownMenu.style.display = "none";
    }
  });
});



const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const statusDiv = document.getElementById('status');
let stream, intervalId;

async function startWebcam() {
    stream = await navigator.mediaDevices.getUserMedia({ video: true });
    video.srcObject = stream;

    intervalId = setInterval(() => {
        canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
        let dataURL = canvas.toDataURL('image/jpeg');
        const subject = document.getElementById('subject').value;

        fetch('/upload_frame', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ image: dataURL, subject: subject })
        })
        .then(res => res.json())
        .then(data => {
            statusDiv.innerText = data.message;
        });
    }, 2000); // send frame every 2 sec
}

function stopWebcam() {
    clearInterval(intervalId);
    stream.getTracks().forEach(track => track.stop());
    statusDiv.innerText = "🛑 Attendance stopped.";
}

startBtn.onclick = () => {
    if (!document.getElementById('subject').value.trim()) {
        alert("Enter subject first!");
        return;
    }
    startWebcam();
    startBtn.disabled = true;
    stopBtn.disabled = false;
};
stopBtn.onclick = () => {
    stopWebcam();
    startBtn.disabled = false;
    stopBtn.disabled = true;
};


const enrollVideo = document.getElementById('enrollVideo');
const enrollCanvas = document.getElementById('enrollCanvas');
const startEnrollBtn = document.getElementById('startEnrollBtn');
const enrollStatus = document.getElementById('enrollStatus');

startEnrollBtn.onclick = async () => {
    const id = document.getElementById('enroll_id').value.trim();
    const name = document.getElementById('enroll_name').value.trim();
    const student_class = document.getElementById('enroll_class').value.trim();
    const branch = document.getElementById('enroll_branch').value.trim();

    if (!id || !name || !student_class || !branch) {
        alert("Please fill all fields before enrolling!");
        return;
    }

    // Start webcam
    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
    enrollVideo.srcObject = stream;

    let count = 0;
    const intervalId = setInterval(() => {
        const ctx = enrollCanvas.getContext('2d');
        ctx.drawImage(enrollVideo, 0, 0, enrollCanvas.width, enrollCanvas.height);
        const dataURL = enrollCanvas.toDataURL('image/jpeg');

        fetch('/upload_enroll_frame', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                image: dataURL,
                student_id: id,
                name: name,
                student_class: student_class,
                branch: branch
            })
        }).then(res => res.json()).then(data => {
            enrollStatus.innerText = data.message;
        });

        count++;
        if (count >= 10) {
            clearInterval(intervalId);
            stream.getTracks().forEach(track => track.stop());
            enrollStatus.innerText += "\n✅ Enrollment complete.";
        }
    }, 1000); // send 1 frame every second
};
