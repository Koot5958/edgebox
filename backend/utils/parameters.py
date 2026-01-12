# App parameters
MAX_LEN = 10
STABILITY_MARGIN = 3  # Number of words displayed that can be modified (previous ones are frozen)
REFRESH_RATE_FAST = 0.1
REFRESH_RATE_SLOW = 0.3
REFRESH_TRANSLATE_RATE = 0.1

# Default languages
DEFAULT_AUDIO_LANG = "French (France)"
DEFAULT_TRANS_LANG = "English (United States)"

# Thread names
THREAD_NAMES = ["speech_to_text", "translate"]

# Display
LOG_TITLE = "[Logs]"

# Audio stream
SR = 16000
CHUNK = int(SR / 10)
TIME_BETWEEN_SENTENCES = 4
STREAMING_LIMIT = 296

# Display messages
SHUTDOWN_MSG = """
    **Session Closed**

    This session has been closed successfully.  
    Please refresh the page to start a new session.

    ---

    **세션 종료**

    현재 세션이 정상적으로 종료되었습니다.  
    새 세션을 시작하려면 페이지를 새로 고침해 주세요.
"""

INFO_MSG = """
    **Development Notice**

    This application is currently under active development.  
    While it aims to provide real-time speech transcription and translation, some results may be inaccurate, incomplete, or not fully representative of the original speech.

    Performance and accuracy may vary depending on the language.  
    At this stage, English and French generally provide the most reliable results.

    ---

    **개발 중 안내**

    본 애플리케이션은 현재 개발 중인 서비스입니다.  
    실시간 음성 인식 및 번역을 제공하지만, 일부 결과는 부정확하거나 불완전할 수 있습니다.

    언어, 발화 환경 및 오디오 품질에 따라 정확도가 달라질 수 있으며,  
    현재 영어와 프랑스어가 가장 안정적인 결과를 제공합니다.
"""