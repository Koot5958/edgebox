// =====================
// DOM
// =====================
const startBtn = document.getElementById("start-btn");
const stopBtn  = document.getElementById("stop-btn");

const bars = document.querySelectorAll(".voice-circle.google-voice .bar");

const panels = {
    left: {
        prev: document.getElementById("prev-subt-left"),
        curr: document.getElementById("curr-subt-left"),
        space: document.getElementById("space-line-left"),
    },
    right: {
        prev: document.getElementById("prev-subt-right"),
        curr: document.getElementById("curr-subt-right"),
        space: document.getElementById("space-line-right"),
    }
};

// =====================
// State
// =====================
let pc = null;
let channel = null;
let stream = null;

// =====================
// UI helpers
// =====================
function animateSpace(el, animation_duration) {
    if (!el) return;

    el.style.setProperty("--anim-duration", `${animation_duration}s`);
    el.classList.remove("animate");
    void el.offsetWidth;
    el.classList.add("animate");
}

function updateSubtitle(kind, newLine, prevText, currText, animation_duration) {
    const p = panels[kind];
    if (!p || !p.curr) return;

    p.prev.textContent = prevText;
    p.curr.textContent = currText;

    if (newLine) {
        animateSpace(p.space, animation_duration);
    }
}


// voice animations
function randomizeBars() {
    bars.forEach(bar => {
        const mult = (Math.random() * 0.6 + 0.15).toFixed(2);
        const transDelay = (Math.random() * 0.1).toFixed(2);

        bar.style.setProperty("--multiplier", mult);
        bar.style.setProperty("--trans-delay", transDelay + "s");
    });
}

randomizeBars();
setInterval(randomizeBars, 1000);

let voiceTick = 0;
function updateVoice(level) {
    voiceTick++;
    if (voiceTick % 3 !== 0) return;

    const containers = document.querySelectorAll(".voice-circle.google-voice");
    
    const normalizedLevel = level < 0.12 ? 0 : level;

    containers.forEach(vc => {
        vc.style.setProperty("--voice-level", normalizedLevel);
        
        if (normalizedLevel === 0) {
            vc.classList.add("is-silent");
        } else {
            vc.classList.remove("is-silent");
        }
    });
}

function handleSubtitleFromBackend(msg) {

    const panelKey = msg.speaker_slot === 0
        ? "left"
        : "right";

    updateSubtitle(
        panelKey,
        msg.new_line_transc,
        msg.prev_transc,
        msg.transc,
        msg.animation_duration,
    );
}

// =====================
// Display languages
// =====================
function setupCustomSelect(selectRootId, defaultValue) {
    const root = document.getElementById(selectRootId);
    const trigger = root.querySelector(".select-trigger");
    const menu = root.querySelector(".select-menu");

    fetch("/lang_list.json")
        .then(res => res.json())
        .then(languages => {
            menu.innerHTML = "";

            languages.forEach(lang => {
                const li = document.createElement("li");
                li.textContent = lang.label;
                li.dataset.value = lang.code;

                li.addEventListener("click", () => {
                    trigger.textContent = lang.label;
                    trigger.dataset.value = lang.code;
                    root.classList.remove("open");
                });

                menu.appendChild(li);

                if (lang.code === defaultValue) {
                    trigger.textContent = lang.label;
                    trigger.dataset.value = lang.code;
                }
            });
        });

    // ouvrir / fermer
    trigger.addEventListener("click", (e) => {
        e.stopPropagation();
        root.classList.toggle("open");
    });

    // fermer si clic ailleurs
    document.addEventListener("click", () => {
        root.classList.remove("open");
    });
}

// =====================
// START
// =====================
async function start() {
    stream = await navigator.mediaDevices.getUserMedia({ audio: true });

    startBtn.disabled = true;
    stopBtn.disabled = false;


    pc = new RTCPeerConnection({
        iceServers: [{ urls: "stun:stun.l.google.com:19302" }]
    });

    channel = pc.createDataChannel("data");

    channel.onmessage = (event) => {
        let msg;
        try {
            msg = JSON.parse(event.data);
        } catch {
            return;
        }

        if (msg.type === "subtitle") handleSubtitleFromBackend(msg);
        if (msg.type === "voice") updateVoice(msg.level);
    };

    stream.getTracks().forEach(track => pc.addTrack(track, stream));

    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);

    await new Promise(resolve => {
        if (pc.iceGatheringState === "complete") resolve();
        else {
            pc.addEventListener("icegatheringstatechange", () => {
                if (pc.iceGatheringState === "complete") resolve();
            });
        }
    });

    const res = await fetch("/api/offer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            sdp: pc.localDescription.sdp,
            type: pc.localDescription.type,
            room_code: currentRoomCode
        })
    });

    const answer = await res.json();
    await pc.setRemoteDescription(answer);
}

// =====================
// STOP
// =====================
function stop() {
    startBtn.disabled = false;
    stopBtn.disabled = true;

    if (channel) channel.close();
    if (stream) stream.getTracks().forEach(t => t.stop());
    if (pc) pc.close();

    channel = null;
    stream = null;
    pc = null;

    Object.values(panels).forEach(p => {
        if (p.prev) p.prev.textContent = "";
        if (p.curr) p.curr.textContent = "";
    });

    updateVoice(0);
}


// =====================
// Events
// =====================
startBtn.addEventListener("click", start);
stopBtn.addEventListener("click", stop);

document.addEventListener("DOMContentLoaded", () => {
    // récupérer room depuis URL
    const params = new URLSearchParams(window.location.search);
    const roomCode = params.get("room");

    if (roomCode) {
        document.getElementById("room-display").textContent = roomCode;
        window.currentRoomCode = roomCode; // utile pour l'envoyer au backend
    }
});

