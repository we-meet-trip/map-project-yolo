"""환경 변수 이름 계약 테스트.

배포 구성(compose)은 공용 값에 MAP_PROJECT_, 이 서비스 전용 값에 YOLO_ 접두를 붙인
이름으로 값을 넘긴다. 코드가 다른 이름을 읽으면 값이 조용히 기본값으로 돌아가므로,
읽는 이름을 여기서 고정한다.
"""
from __future__ import annotations

import pytest


def _fresh():
    from map_project_yolo.settings import VisionSettings

    return VisionSettings(_env_file=None)


def test_service_key_wins_over_shared_key(monkeypatch):
    monkeypatch.setenv("YOLO_GEMINI_API_KEY", "service-key")
    monkeypatch.setenv("MAP_PROJECT_GEMINI_API_KEY", "shared-key")

    assert _fresh().YOLO_GEMINI_API_KEY.get_secret_value() == "service-key"


def test_shared_key_is_used_when_service_key_is_absent(monkeypatch):
    monkeypatch.delenv("YOLO_GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("MAP_PROJECT_GEMINI_API_KEY", "shared-key")

    assert _fresh().YOLO_GEMINI_API_KEY.get_secret_value() == "shared-key"


def test_shared_key_is_used_when_service_key_is_empty(monkeypatch):
    """예시 설정처럼 전용 키가 빈 값으로 있어도 공용 키로 넘어간다."""
    monkeypatch.setenv("YOLO_GEMINI_API_KEY", "")
    monkeypatch.setenv("MAP_PROJECT_GEMINI_API_KEY", "shared-key")

    assert _fresh().YOLO_GEMINI_API_KEY.get_secret_value() == "shared-key"


def test_shared_key_fallback_also_works_from_env_file(monkeypatch, tmp_path):
    """.env 파일에 두 줄이 있고 전용 키가 빈 값일 때도 같다."""
    from map_project_yolo.settings import VisionSettings

    monkeypatch.delenv("YOLO_GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("MAP_PROJECT_GEMINI_API_KEY", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("YOLO_GEMINI_API_KEY=\nMAP_PROJECT_GEMINI_API_KEY=file-shared-key\n", encoding="utf-8")

    assert VisionSettings(_env_file=env_file).YOLO_GEMINI_API_KEY.get_secret_value() == "file-shared-key"


@pytest.mark.parametrize("name,value,field", [
    ("YOLO_WS_MAX_JOBS", "7", "YOLO_WS_MAX_JOBS"),
    ("YOLO_JOB_TIMEOUT_SECONDS", "40.0", "YOLO_JOB_TIMEOUT_SECONDS"),
    ("YOLO_USER_SERVICE_BASE_URL", "http://user.invalid:8080", "YOLO_USER_SERVICE_BASE_URL"),
    ("MAP_PROJECT_GEMINI_MODEL", "synthetic-model", "MAP_PROJECT_GEMINI_MODEL"),
    ("MAP_PROJECT_KAKAO_REST_API_KEY", "synthetic-kakao", "MAP_PROJECT_KAKAO_REST_API_KEY"),
    ("YOLO_WIKIPEDIA_CONTACT", "https://example.com/contact", "YOLO_WIKIPEDIA_CONTACT"),
])
def test_prefixed_names_are_read(monkeypatch, name, value, field):
    monkeypatch.setenv(name, value)

    assert str(getattr(_fresh(), field)) == value


@pytest.mark.parametrize("old_name,field", [
    ("WS_MAX_JOBS_PER_CONNECTION", "YOLO_WS_MAX_JOBS"),
    ("USER_SERVICE_BASE_URL", "YOLO_USER_SERVICE_BASE_URL"),
    ("GEMINI_MODEL", "MAP_PROJECT_GEMINI_MODEL"),
])
def test_unprefixed_names_are_not_read(monkeypatch, old_name, field):
    default = getattr(_fresh(), field)
    monkeypatch.setenv(old_name, "ignored-value" if isinstance(default, str) else "999")

    assert getattr(_fresh(), field) == default
