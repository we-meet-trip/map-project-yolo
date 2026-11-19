# 계약

이 서비스가 정의하는 계약(WebSocket `/ws/vision`, `GET /health`, `GET /metrics`)과, 이 서비스가 호출하는 계약(User BFF 의 Vision 허가 API)을 정리한다. 값과 한도는 코드 기준이다(`map_project_yolo/api/ws.py`, `map_project_yolo/api/permit.py`, `map_project_yolo/schemas/vision_schemas.py`, `map_project_yolo/settings.py`).

## 소유 관계

| 계약 | 정의 | 사용 |
|---|---|---|
| WebSocket `/ws/vision`, 하위 프로토콜 `map.vision.v1` | 이 저장소 | [map-project-client](https://github.com/we-meet-trip/map-project-client)(앱), [map-project-infra](https://github.com/we-meet-trip/map-project-infra)(관문 경로) |
| `GET /health`, `GET /metrics` | 이 저장소 | map-project-infra(compose 상태 확인, 지표 수집) |
| `POST /api/v1/vision/permit` | [map-project-user](https://github.com/we-meet-trip/map-project-user) | 이 저장소 |

## WebSocket `/ws/vision`

### 연결(핸드셰이크)

- 클라이언트는 하위 프로토콜 두 개를 함께 보낸다: `map.vision.v1`, `bearer.<사용자 JWT>`.
  - `bearer.` 값은 정확히 하나여야 하고, JWT 는 점으로 나뉜 base64url 세 조각, 8,192자 이하다.
  - 조건이 맞지 않으면 연결을 **수락하지 않고** close `4401` 로 닫는다.
- 서버는 수락 전에 User BFF 허가 API 를 `consume=false` 로 부른다(아래 "허가 API"). 거절되면 수락하지 않고 닫는다: 401→`4401`, 403→`4403`, 429→`4429`, 그 밖(허가 서비스 장애 포함)→`1013`.
  - 수락하지 않은 연결은 브라우저에서 HTTP 본문이 보이지 않는다. 앱은 연결이 거절되면 동의 상태를 다시 확인한다.
- 수락할 때 서버는 협상 응답에 `map.vision.v1` 만 싣는다. 토큰을 되돌려 보내지 않는다.
- 연결 시점의 사용자 ID 와 AI 동의 개정 번호(`consent_revision`)를 소켓에 고정한다. 이후 작업마다 같은 값인지 확인한다.

### 메시지

텍스트 프레임 하나에 JSON 객체 하나(`VisionRequest`)를 보낸다. 바이너리 프레임은 받지 않는다(close `1003`).

| 필드 | 형식 | 제약 |
|---|---|---|
| `session_id` | 문자열, 필수 | 1~128자, `[A-Za-z0-9_-]`. 응답에 그대로 돌려준다(상관 ID) |
| `request_id` | 문자열, 선택 | 1~128자, `[A-Za-z0-9_-]`. 응답에 그대로 돌려준다 |
| `voice_triggered` | 불리언, 기본 `false` | `true` 면 사진 경로, `false` 면 텍스트 경로 |
| `frame_b64` | 문자열, 기본 `""` | 사진 경로에서 필수. base64 JPEG, 문자열 2,796,204자 이하, 디코딩 2 MiB 이하, JPEG 끝 표식(FFD9)으로 끝남, 가로×세로 4,194,304 픽셀(2048×2048) 이하 |
| `voice_text` | 문자열, 선택 | 2,000자 이하. 텍스트 경로에서는 질문, 사진 경로에서는 사진에 대한 질문 |
| `location` | 객체, 선택 | `lat` 33~43, `lng` 124~132(대한민국 범위), `accuracy_meters` 0~100,000(선택). 유한한 숫자만 |
| `prior_context` | 문자열, 선택 | 2,000자 이하 |
| `conversation_history` | 배열, 기본 `[]` | 8개 이하. 원소는 정확히 `{"role": "user"\|"assistant", "content": 문자열(2,000자 이하)}` |

- 메시지 하나는 4 MiB(4,194,304바이트) 이하다. uvicorn 도 같은 크기 상한(`--ws-max-size 4194304`)과 전송 대기열 4개(`--ws-max-queue 4`)로 띄운다.
- `voice_triggered=false` 이고 `voice_text` 가 비어 있는 메시지는 응답 없이 넘긴다. 연결당 처리 상한도 쓰지 않는다.
- 형식이 틀린 메시지에는 `session_id="unknown"`, `status="failed"`, `error="parse error: 요청 형식을 확인해주세요."` 를 보내고 연결은 유지한다. 입력 값이나 검증 오류 본문은 돌려주지 않는다.

### 처리 순서(메시지 하나)

1. 연결당 메시지 수와 크기를 확인한다(넘으면 close `1009`).
2. 스키마와 사진(사진 경로일 때)을 검사한다.
3. 연결당 처리 횟수를 확인한다(넘으면 실패 응답 뒤 close `1008`).
4. 프로세스 자원을 예약한다. 가득 찼으면 `"다른 인식 요청을 처리 중이에요. 잠시 후 다시 시도해주세요."` 실패 응답을 보내고 연결은 유지한다. 계정 한도는 쓰지 않는다.
5. 허가 API 를 `consume=true`, `expected_revision=<연결 때 개정 번호>` 로 부른다. 계정 한도 1을 쓴다. 사용자 ID 나 개정 번호가 연결 때와 다르면 거절한다.
6. 허가 응답의 `include_location` 이 `false` 면 위치를 지우고 진행한다.
7. 사진 경로: YOLO 탐지 → Gemini 식별 → 위키백과 검색. 텍스트 경로: 장소 질문이면 Kakao 장소 검색, 아니면 Gemini 답변.
8. 결과를 보내기 직전에 허가 API 를 `consume=false`, `expected_revision` 으로 **한 번 더** 부른다. 거절되면 결과를 버리고 실패 응답을 보낸 뒤 닫는다. 이때 계정 한도를 다시 쓰지 않는다.
9. 전체 작업은 `YOLO_JOB_TIMEOUT_SECONDS` 안에 끝나야 한다(넘으면 `"인식 시간이 초과됐어요. 다시 시도해주세요."`).

### 응답(`VisionResponse`)

| 필드 | 형식 | 설명 |
|---|---|---|
| `session_id` | 문자열 | 요청 값 그대로(형식 오류면 `"unknown"`) |
| `request_id` | 문자열 또는 `null` | 요청 값 그대로 |
| `detected_object` | 객체 또는 `null` | YOLO 가 찾은 신뢰도 최고 객체 `{label, confidence(0~1), bbox[x1,y1,x2,y2]}` |
| `identify_result` | 객체 또는 `null` | `{name, category, description, search_query}`. `category` 는 `landmark`·`food`·`product`·`animal`·`plant`·`other` 중 하나. 텍스트 경로에서는 `name="AI 답변"`, `category="other"`, `description=<답변>`, `search_query=<질문>` |
| `search_results` | 배열 | `{title, summary, source, url}`. `source` 는 `"wikipedia"`. 검색을 끄거나 실패하면 빈 배열 |
| `status` | `"done"` 또는 `"failed"` | 사진 경로는 식별 결과가 있어야 `done` |
| `code` | 문자열 또는 `null` | 허가 거절 사유. 아래 다섯 값만 전달한다 |
| `error` | 문자열 또는 `null` | 사용자에게 보여 줄 한국어 문구. 내부 예외나 상위 서비스 본문은 담지 않는다 |

`code` 값: `AGE_INFORMATION_REQUIRED`, `AGE_RESTRICTED`, `SERVICE_POLICY_REQUIRED`, `AI_CONSENT_REQUIRED`, `AI_CONSENT_CHANGED`.

### close 코드

| 코드 | 언제 |
|---|---|
| `1000` | 유휴 시간(`YOLO_WS_IDLE_TIMEOUT_SECONDS`) 동안 메시지가 없음 |
| `1003` | 바이너리 프레임 등 텍스트 계약을 따르지 않는 프레임 |
| `1008` | 연결당 처리 횟수(`YOLO_WS_MAX_JOBS`)를 다 씀(실패 응답 뒤) |
| `1009` | 메시지가 4 MiB 를 넘거나 연결당 메시지 수(`YOLO_WS_MAX_MESSAGES_PER_CONNECTION`)를 넘음 |
| `1013` | 허가 서비스를 쓸 수 없음, 또는 서비스가 아직 준비되지 않음 |
| `4401` | 인증 실패(토큰 없음·형식 오류·만료·탈퇴, 사용자 ID 불일치) |
| `4403` | 정책·연령·AI 동의 거절, 동의 개정 번호 변경 |
| `4429` | 계정 일일 한도 초과 |

## 허가 API (User BFF 소유, 이 서비스가 호출)

- `POST {YOLO_USER_SERVICE_BASE_URL}/api/v1/vision/permit`
- 헤더: `Authorization: Bearer <사용자 JWT>`, `X-Internal-Token: <MAP_PROJECT_VISION_INTERNAL_TOKEN>`
- 본문: `{"consume": true|false}`, 연결 뒤 호출에는 `"expected_revision": <정수>` 를 더한다.
- 200 응답 본문: `user_id`(문자열 또는 정수, 비어 있으면 안 됨), `remaining`(0 이상 정수), `reset_at`(시간대가 있는 시각), `consent_revision`(1 이상 정수, 엄격), `include_location`(불리언, 엄격). 형식이 틀리면 허가 서비스 장애(503)로 본다.
- 200 이 아니면: 401·403·429 는 그대로, 그 밖은 503 으로 다룬다. 403 본문의 `code` 는 위 다섯 값일 때만 받아들이고, `message` 등 다른 본문은 버린다.
- 리다이렉트를 따라가지 않는다. 제한시간은 `YOLO_PERMIT_TIMEOUT_SECONDS`(0 초과 30 이하, 기본 5).
- 작업 하나에 세 번 부른다: 연결 때 `consume=false`, 처리 직전 `consume=true`, 전송 직전 `consume=false`.
- `MAP_PROJECT_VISION_INTERNAL_TOKEN` 이 비어 있으면 서비스가 부팅하지 않는다. User 서비스와 같은 값을 넣는다.

## HTTP

| 경로 | 응답 | 비고 |
|---|---|---|
| `GET /health` | `200 {"status": "ok", "service": "yolo"}` | 프로세스가 떠 있는지만 본다. Gemini·허가 서비스 도달성은 보지 않는다 |
| `GET /metrics` | Prometheus 텍스트 형식 | `prometheus-fastapi-instrumentator`. 인증이 없으므로 외부에 열지 않는다 |
