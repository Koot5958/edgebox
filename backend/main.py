from itertools import count
import json
import asyncio
from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCConfiguration, RTCIceServer
from pathlib import Path

from processor import AudioProcessor
from thread_manager import ThreadManager, stop_all_threads
from utils.display import format_subt, join_text
from utils.parameters import REFRESH_RATE_FAST, REFRESH_RATE_SLOW, DEFAULT_AUDIO_LANG, DEFAULT_TRANS_LANG
from utils.lang_list import LANGUAGE_CODES
from utils.logs import print_logs_threads


count_pc = 0


async def subtitle_loop(pc):
    while pc.running:
        new_line_transc, pc.prev_transc, transc = format_subt(
            pc.thread_manager.output_stt,
            pc.prev_transc
        )

        new_line_transl, pc.prev_transl, transl = format_subt(
            pc.thread_manager.output_transl,
            pc.prev_transl
        )

        if pc.data_channel and pc.data_channel.readyState == "open":
            pc.data_channel.send(
                json.dumps(
                    {
                        "type": "subtitle",
                        "new_line_transc": new_line_transc,
                        "prev_transc": join_text(pc.prev_transc, LANGUAGE_CODES[DEFAULT_AUDIO_LANG]),
                        "transc": join_text(transc, LANGUAGE_CODES[DEFAULT_AUDIO_LANG]),
                        "new_line_transl": new_line_transl,
                        "prev_transl": join_text(pc.prev_transl, LANGUAGE_CODES[DEFAULT_TRANS_LANG]),
                        "transl": join_text(transl, LANGUAGE_CODES[DEFAULT_TRANS_LANG]),
                        "animation_duration": REFRESH_RATE_SLOW,
                    }
                )
            )

        waiting_time = (
            REFRESH_RATE_SLOW
            if (new_line_transc or new_line_transl)
            else REFRESH_RATE_FAST
        )

        await asyncio.sleep(waiting_time)


async def volume_animation_loop(pc):
    while pc.running:
        if pc.data_channel and pc.data_channel.readyState == "open":
            pc.data_channel.send(
                json.dumps({
                    "type": "voice",
                    "level": float(pc.processor.volume),
                })
            )
        await asyncio.sleep(0.1)


# -------------------------
# WebRTC offer handler
# -------------------------
async def offer(request):
    params = await request.json()
    audio_lang = params.get("audio_lang", DEFAULT_AUDIO_LANG)
    transl_lang = params.get("transl_lang", DEFAULT_TRANS_LANG)

    pc = RTCPeerConnection(
        RTCConfiguration(
            iceServers=[
                RTCIceServer(urls="stun:stun.l.google.com:19302")
            ]
        )
    )
    global count_pc
    count_pc += 1
    pc_id = count_pc

    print_logs_threads("Threads before initialization", pc_id=f"pc-{pc_id}")
    pc.processor = AudioProcessor()
    pc.thread_manager = ThreadManager(audio_lang, transl_lang, pc)
    print_logs_threads("Threads after initialization", pc_id=f"pc-{pc_id}")

    pc.thread_manager.start()
    pc.prev_transc, pc.prev_transl = [], []
    pc.data_channel = None
    pc.running = True

    # tasks that send subtitle and audio volume
    @pc.on("datachannel")
    def on_datachannel(channel):
        pc.data_channel = channel

        if not hasattr(pc, "subtitle_task") or pc.subtitle_task is None:
            pc.subtitle_task = asyncio.create_task(subtitle_loop(pc))
        if not hasattr(pc, "volume_task") or pc.volume_task is None:
            pc.volume_task = asyncio.create_task(volume_animation_loop(pc))

    # task that receives audio chunks from js
    @pc.on("track")
    def on_track(track):
        if track.kind == "audio":
            pc.audio_task = asyncio.create_task(
                pc.processor.process_track(track)
            )

    # changes in the connection between the peers
    @pc.on("connectionstatechange")
    async def on_state_change():
        if pc.connectionState in ("failed", "closed", "disconnected"):
            pc.processor.running = False
            pc.audio_task.cancel()
            pc.running = False

            pc.subtitle_task.cancel()
            pc.thread_manager.stop()

            stop_all_threads()

    await pc.setRemoteDescription(
        RTCSessionDescription(params["sdp"], params["type"])
    )

    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return web.json_response({
        "sdp": pc.localDescription.sdp,
        "type": pc.localDescription.type
    })


# -------------------------
# App aiohttp
# -------------------------
print_logs_threads("Threads before launching app", pc_id="glob")
app = web.Application()

# API
app.router.add_post("/api/offer", offer)

# Frontend
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_PUBLIC = BASE_DIR / "frontend" / "public"
FRONTEND_SRC = BASE_DIR / "frontend" / "src"

async def index(request):
    return web.FileResponse(FRONTEND_PUBLIC / "index.html")

app.router.add_get("/", index)
app.router.add_static("/", FRONTEND_PUBLIC)
app.router.add_static("/css", FRONTEND_PUBLIC / "css")
app.router.add_static("/images", FRONTEND_PUBLIC / "images")
app.router.add_static("/src", FRONTEND_SRC)

web.run_app(app, port=8080)
