# 데이터 안내

## 저장소에 들어 있는 데이터

없다. 시험에는 코드가 실행 중에 만드는 합성 값만 쓴다. 예를 들어 단색 JPEG, 합성 토큰 `test.jwt.signature`, 합성 응답 본문, 공개된 지명 같은 예시 문자열이다. 실제 사용자 사진·위치·대화나 외부 서비스에서 받은 응답은 들어 있지 않다.

## 모델 가중치

| 항목 | 내용 |
|---|---|
| 파일 | `yolo11n.pt`(Ultralytics YOLO11n, 객체 탐지) |
| 출처 | Ultralytics assets 저장소의 공개 릴리스 <https://github.com/ultralytics/assets/releases> |
| 라이선스 | Ultralytics 는 YOLO11 모델을 AGPL-3.0 과 별도 상용 라이선스로 제공한다(<https://www.ultralytics.com/license>). 자세한 고지는 [NOTICE](../NOTICE) |
| 저장소 포함 여부 | 넣지 않는다(재배포 조건이 이 저장소의 MIT 와 다르다). `.gitignore` 가 `models/*.pt` 를 막는다 |
| 받는 법 | `docker build` 가 고정한 릴리스 주소에서 받고, `ADD --checksum` 으로 sha256 을 확인한 뒤 이미지 `/app/models/yolo11n.pt` 에 넣는다(Dockerfile 의 가중치 단계) |
| 다른 가중치 | 파일을 컨테이너에 마운트하고 `YOLO_MODEL_PATH` 를 그 경로로 바꾼다 |

## 실행 중 외부로 보내는 것

이 서비스는 받은 사진·질문을 저장하지 않고 학습용으로 모으지도 않는다. 대신 처리하는 동안 아래 외부 서비스로 일부 내용을 보낸다. 모든 호출은 운영자가 직접 넣은 키·설정으로만 일어난다.

| 받는 곳 | 보내는 것 | 언제 | 근거 |
|---|---|---|---|
| Google Gemini API | 사진(JPEG), 사용자 질문, YOLO 탐지 이름·신뢰도, 위치(아래 조건) | 사진 경로의 식별마다 | `map_project_yolo/nodes/identify_node.py` |
| Google Gemini API | 질문, 이전 맥락(`prior_context`), 대화 기록(최대 8개) | 텍스트 경로의 일반 질문마다 | `map_project_yolo/api/ws.py` 의 텍스트 답변 |
| Kakao Local API | 위도·경도 | 사진 경로에서 위치가 있고 Kakao 키가 있을 때(주소로 바꾸기 위해) | `map_project_yolo/nodes/kakao_local.py` |
| Kakao Local API | 장소 검색어와 위도·경도(있을 때) | 텍스트 경로의 장소 질문마다 | 같은 파일 |
| 위키백과 API(`ko.wikipedia.org`) | Gemini 가 만든 검색어, 운영자 연락처가 든 User-Agent | 식별에 성공했고 `YOLO_WIKIPEDIA_CONTACT` 가 있을 때 | `map_project_yolo/nodes/search_node.py` |
| User BFF(같은 배포 안) | 사용자 JWT, 내부 토큰, 한도 사용 여부, 동의 개정 번호 | 연결 때, 처리 직전, 전송 직전 | `map_project_yolo/api/permit.py` |

위치 조건:
- User BFF 가 그 사용자의 위치 공유 동의(`include_location`)를 참으로 돌려줄 때만 위치를 쓴다. 거짓이면 외부 호출 전에 위치를 지운다.
- Gemini 에는 Kakao 로 바꾼 주소를 보내고, 주소를 못 얻으면 소수 셋째 자리(약 100m)로 줄인 좌표를 보낸다.
- 로그에 남는 좌표 값은 가린다([architecture.md](architecture.md) "로그와 개인 정보").

외부 서비스가 받은 내용을 어떻게 다루는지는 각 서비스의 약관·개인정보 처리 방침을 따른다. 특히 Gemini API 는 요금 등급에 따라 데이터 처리 조건이 다를 수 있으니, 실제 사용자 데이터를 보내기 전에 쓰는 등급의 조건을 직접 확인한다. 이 서비스를 사용자에게 제공하는 사람은 위 표의 전송을 사용자에게 알리고 동의를 받아야 한다.

## 위키백과 검색 결과

- 응답의 `search_results` 에는 위키백과 문서의 제목, 검색 요약 조각(HTML 태그 제거), 원문 링크가 들어간다.
- 위키백과 본문은 CC BY-SA 4.0(대부분 GFDL 과 함께)으로 배포된다(<https://en.wikipedia.org/wiki/Wikipedia:Copyrights>). 화면에 보여 줄 때는 출처(원문 링크)와 라이선스를 함께 표시해야 한다.
- 이 저장소에는 위키백과 본문이 들어 있지 않다. 검색 결과는 요청 처리 중에만 지나간다.
- `YOLO_WIKIPEDIA_CONTACT` 가 비어 있으면 위키백과를 부르지 않는다. Wikimedia User-Agent 정책은 요청을 보내는 쪽의 연락처를 요구하므로, 이 코드를 돌리는 사람이 자기 연락처(URL 또는 이메일)를 넣는다.

## 외부 서비스 키

| 설정 | 발급처 | 없을 때 |
|---|---|---|
| `YOLO_GEMINI_API_KEY` 또는 `MAP_PROJECT_GEMINI_API_KEY` | Google AI Studio 등 Gemini API 발급처 | 서비스가 부팅하지 않는다 |
| `MAP_PROJECT_KAKAO_REST_API_KEY` | Kakao Developers 의 REST API 키 | 장소 질문은 실패, 위치는 주소 대신 줄인 좌표 |

키는 각자 발급해 `.env` 에 넣는다. 저장소에는 어떤 키도 들어 있지 않다. 외부 API 호출 비용과 한도는 키를 발급받은 사람의 계정에 걸린다.

## 비공개 개발본과의 관계

- 공개본의 서비스·패키지·환경 변수 이름은 비공개 개발본과 다르다. 비공개 운영 설정이나 이미지와 바꿔 쓸 수 없다.
- 공개본에는 비공개 개발 기간의 운영 자료(로그, 사용자 데이터, 운영 설정)가 들어 있지 않고, 다시 만들 수도 없다.
