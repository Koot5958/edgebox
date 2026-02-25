// popup

function openModal() {
    document.getElementById("room-modal").style.display = "flex";
}

function closeModal() {
    document.getElementById("room-modal").style.display = "none";
}

function generateRoom() {
    const code = Math.random()
        .toString(36)
        .substring(2, 8)
        .toUpperCase();

    document.getElementById("generated-code").textContent =
        "Room code: " + code;
}

function joinRoom() {
    const code = document.getElementById("room-code").value.trim();

    if (!code) {
        alert("Please enter a room code");
        return;
    }

    window.location.href = `demo.html?room=${encodeURIComponent(code)}`;
}