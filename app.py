import time

import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode

from utils.parameters import DEFAULT_AUDIO_LANG, DEFAULT_TRANS_LANG, REFRESH_RATE_FAST, REFRESH_RATE_SLOW
from utils.lang_list import LANGUAGE_CODES
from web.display import get_html_subt, format_subt, join_text
from utils.streamlit_utils import shutdown_app
from utils.logs import print_logs_threads
from thread_manager import ThreadManager, stop_all_threads
from microphone_stream import AudioProcessor


def load_css(path: str):
    with open(path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
load_css("web/theme.css")


if st.session_state.get("shutdown", False):
    print_logs_threads("Threads after executing stop_all_threads (close app)")
    st.write("App closed. Press Ctrl+C in the terminal.")
    st.stop()

st.set_page_config(layout="wide")
st.title("EdgeBox-Nova LLM")


#------- Rerun and stop buttons -------#
col_close, col_rerun, _ = st.columns([1, 1, 8])
with col_close:
    if st.button("Close App"):
        print_logs_threads("Threads before executing stop_all_threads (close app)")
        shutdown_app()
with col_rerun:
    if st.button("Rerun App"):
        print_logs_threads("Threads before executing stop_all_threads (rerun)")
        stop_all_threads()
        print_logs_threads("Threads after executing stop_all_threads (rerun)")
        st.rerun()


#------- audio capture -------#
ctx = webrtc_streamer(
    key="audio",
    mode=WebRtcMode.SENDONLY,
    audio_processor_factory=AudioProcessor,
    media_stream_constraints={"audio": True, "video": False},
    async_processing=True,
    audio_receiver_size=128,
)


#------- languages choice -------#
lang_keys = list(LANGUAGE_CODES.keys())
if "lang_audio" not in st.session_state:
    st.session_state["lang_audio"] = DEFAULT_AUDIO_LANG
if "lang_transl" not in st.session_state:
    st.session_state["lang_transl"] = DEFAULT_TRANS_LANG

col_transc, col_transl = st.columns(2, gap="large")
with col_transc:
    lang_audio_ui = st.selectbox("Audio language", lang_keys, key="lang_audio_ui", index=lang_keys.index(st.session_state.lang_audio))
with col_transl:
    lang_transl_ui = st.selectbox("Translation language", lang_keys, key="lang_transl_ui", index=lang_keys.index(st.session_state.lang_transl))

st.session_state.lang_audio = lang_audio_ui
st.session_state.lang_transl = lang_transl_ui

LANG_AUDIO = LANGUAGE_CODES[lang_audio_ui]
LANG_TRANSL = LANGUAGE_CODES[lang_transl_ui]


#------- transcription and translation display initialization -------#
transc, transl, prev_transc, prev_transl = [], [], [], []
with col_transc:
    transc_box = st.empty()
with col_transl:
    transl_box = st.empty()
transc_box.markdown(get_html_subt("", "", False, "transc", "Transcription"), unsafe_allow_html=True)
transl_box.markdown(get_html_subt("", "", False, "transl", "Translation"), unsafe_allow_html=True)


#------- stopping STT and translation threads -------#
print_logs_threads("Threads before stop_all_threads (before running while)")
stop_all_threads()
print_logs_threads("Threads after stop_all_threads (before running while)")


if ctx and ctx.audio_processor:

    #------- start STT and translation threads -------#
    st.session_state.threads = ThreadManager(LANG_AUDIO, LANG_TRANSL, ctx.audio_processor)
    print_logs_threads("Threads after creating threads (before running while)")

    threads = st.session_state.threads
    threads.start()


    #----- real-time update of transcription and translation -----#
    while threads.running:

        volume = ctx.audio_processor.volume if ctx.audio_processor else 0.0

        new_line_transc, prev_transc, transc = format_subt(threads.output_stt, prev_transc)
        new_line_transl, prev_transl, transl = format_subt(threads.output_transl, prev_transl)

        # transcription
        html_transc = get_html_subt(
            join_text(prev_transc, LANG_AUDIO), 
            join_text(transc, LANG_AUDIO), 
            new_line_transc, 
            "transc", 
            "Transcription",
            voice_level=volume,
        )
        transc_box.markdown(html_transc, unsafe_allow_html=True)

        # translation
        html_transl = get_html_subt(
            join_text(prev_transl, LANG_TRANSL), 
            join_text(transl, LANG_TRANSL), 
            new_line_transl, 
            "transl",
            "Translation",
            voice_level=volume,
        )
        transl_box.markdown(html_transl, unsafe_allow_html=True)

        # waiting time
        waiting_time = REFRESH_RATE_SLOW if (new_line_transc or new_line_transl) else REFRESH_RATE_FAST
        time.sleep(waiting_time)
