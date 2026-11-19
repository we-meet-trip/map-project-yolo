"""map-project-yolo 환경설정.

`VisionSettings(BaseSettings)` 는 환경 변수(또는 `.env`) 로부터 값을
읽어 들이는 설정 객체이고, `get_settings()` 는 프로세스 1회 캐시되는
싱글톤 접근자다.
"""
from __future__ import annotations

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class VisionSettings(BaseSettings):
    """map-project-yolo 의 모든 환경 변수 묶음.

    model_config:
      - env_file=".env": 작업 디렉토리의 .env 파일 자동 로드.
      - extra="ignore": 정의되지 않은 환경 변수는 무시.

    Gemini 관련:
      YOLO_GEMINI_API_KEY: Gemini Vision 호출용 API 키. 비밀값(SecretStr).
        비어 있으면 공용 MAP_PROJECT_GEMINI_API_KEY 를 읽는다.
      MAP_PROJECT_GEMINI_MODEL: 사용할 Gemini 모델명.
      YOLO_GEMINI_TIMEOUT_SECONDS: Gemini 호출 1건의 타임아웃(초).

    YOLO 관련:
      YOLO_MODEL_PATH: .pt 모델 파일 경로. 작업 디렉토리 기준 상대 경로.
      YOLO_CONFIDENCE: 탐지 신뢰도 임계값(0.0~1.0).

    서비스 관련:
      YOLO_JOB_TIMEOUT_SECONDS: 작업 1건(탐지·식별·검색) 전체 한도(초).
        식별 + 검색을 모두 담아야 하므로 YOLO_GEMINI_TIMEOUT_SECONDS 보다 커야 한다.
        작으면 식별을 마치고도 검색 도중 잘려 결과가 통째로 버려진다.
      YOLO_WS_MAX_JOBS: 연결 하나가 돌릴 수 있는 인식 횟수 상한.
        인식 1건마다 외부 모델을 부르므로, 상한이 없으면 연결 하나로 호출
        한도를 소진시켜 같은 키를 쓰는 다른 기능까지 멈춘다.

    검색(위키백과):
      YOLO_WIKIPEDIA_CONTACT: 위키백과 API 를 부를 때 User-Agent 에 넣는 운영자 연락처
        (URL 또는 이메일). Wikimedia User-Agent 정책은 요청을 보내는 쪽의 연락처를
        요구한다. 비어 있으면 위키백과를 부르지 않고 검색 결과를 빈 목록으로 둔다.

    관측(로깅):
      YOLO_LOG_LEVEL: 루트 로거 레벨. uvicorn 은 자기 로거만 구성하고 루트 로거에는
        핸들러를 붙이지 않는다. map_project_yolo/main.py 의 _configure_logging 이 부팅 시
        루트 핸들러가 비어 있을 때만 stdout 핸들러를 붙여 map_project_yolo.* 로그를 살린다.
    """

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    YOLO_GEMINI_API_KEY: SecretStr = SecretStr("")
    # 다른 서비스와 함께 쓰는 공용 키. 전용 키가 없거나 비어 있을 때만 쓴다.
    MAP_PROJECT_GEMINI_API_KEY: SecretStr = SecretStr("")
    MAP_PROJECT_GEMINI_MODEL: str = "gemini-3.8-flash"
    YOLO_GEMINI_TIMEOUT_SECONDS: float = 25.0
    MAP_PROJECT_KAKAO_REST_API_KEY: str = ""

    YOLO_MODEL_PATH: str = "models/yolo11n.pt"
    YOLO_CONFIDENCE: float = 0.5

    YOLO_JOB_TIMEOUT_SECONDS: float = 45.0
    YOLO_WS_MAX_JOBS: int = 60
    YOLO_USER_SERVICE_BASE_URL: str = "http://user:8080"
    MAP_PROJECT_VISION_INTERNAL_TOKEN: SecretStr = SecretStr("")
    YOLO_PERMIT_TIMEOUT_SECONDS: float = Field(default=5.0, gt=0, le=30)
    YOLO_MAX_CONCURRENT_JOBS: int = Field(default=2, ge=1, le=8)
    YOLO_WS_IDLE_TIMEOUT_SECONDS: float = Field(default=120.0, gt=0)
    YOLO_WS_MAX_MESSAGES_PER_CONNECTION: int = Field(default=240, ge=1)

    YOLO_WIKIPEDIA_CONTACT: str = Field(default="", max_length=256)

    YOLO_LOG_LEVEL: str = "INFO"

    @model_validator(mode="after")
    def _use_shared_gemini_key_when_service_key_is_empty(self) -> "VisionSettings":
        """전용 키가 빈 값으로 들어와도 공용 키로 넘어가게 한다.

        예시 설정처럼 `YOLO_GEMINI_API_KEY=` 줄이 빈 값으로 있으면, 이름 대체만으로는
        빈 값이 그대로 남아 공용 키가 있어도 부팅을 거절한다.
        """
        if not self.YOLO_GEMINI_API_KEY.get_secret_value():
            self.YOLO_GEMINI_API_KEY = self.MAP_PROJECT_GEMINI_API_KEY
        return self


_settings: VisionSettings | None = None


def get_settings() -> VisionSettings:
    """프로세스 단위 싱글톤 VisionSettings 접근자."""
    global _settings
    if _settings is None:
        _settings = VisionSettings()
    return _settings
