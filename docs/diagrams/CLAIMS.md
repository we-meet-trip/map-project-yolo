# 다이어그램 근거표

그림마다 노드와 엣지 하나에 한 줄씩, 그 주장이 어느 코드에 근거하는지 적는다. 줄 번호는 이 저장소의 현재 코드 기준이다. 다른 저장소의 위치는 저장소 이름과 경로로 적는다.

## vision-pipeline (`src/vision-pipeline.seq.json`)

사진 경로(`voice_triggered=true`)의 순서다. 텍스트 경로는 탐지·식별·위키백과 대신 Kakao 장소 검색이나 Gemini 텍스트 답변을 쓴다([architecture.md](../architecture.md) "처리 순서" 5번).

| 그림 | 요소(노드/엣지) | 주장 | 근거 file:line | 확인 방법 |
|---|---|---|---|---|
| vision-pipeline | 노드 앱 | 앱이 하위 프로토콜 `map.vision.v1` 로 연결한다 | map-project-client `lib/features/vision/services/vision_ws_service.dart:107` | 코드 대조 |
| vision-pipeline | 노드 비전 서비스 | `/ws/vision` 경로를 이 서비스가 연다 | `map_project_yolo/main.py:122` | 코드 대조, `tests/test_vision_security.py` 의 `test_real_asgi_websocket_negotiates_protocol_and_echoes_request_id` |
| vision-pipeline | 노드 User BFF | 허가 API 를 User BFF 가 정의한다 | map-project-user `src/main/java/map/project/user/vision/VisionPermitController.java:22` | 코드 대조 |
| vision-pipeline | 노드 Gemini API | 식별에 Gemini 를 부른다 | `map_project_yolo/nodes/identify_node.py:97` | 코드 대조 |
| vision-pipeline | 노드 Kakao Local (키가 있을 때) | 역지오코딩은 Kakao 키가 있을 때만 한다 | `map_project_yolo/nodes/identify_node.py:57-58`, `map_project_yolo/nodes/kakao_local.py:9,23` | 코드 대조 |
| vision-pipeline | 노드 위키백과 API (연락처 설정 때) | 위키백과는 `YOLO_WIKIPEDIA_CONTACT` 가 있을 때만 부른다 | `map_project_yolo/nodes/search_node.py:39-42` | `tests/test_nodes.py` 의 `test_search_makes_no_call_without_operator_contact` |
| vision-pipeline | 띠 ① 연결 | 수락 전에 권한을 확인한다 | `map_project_yolo/api/ws.py:122-128` | `test_policy_denied_handshake_never_accepts_or_reads_a_frame` |
| vision-pipeline | 엣지 앱→비전 서비스 WebSocket 연결 | `map.vision.v1` 과 `bearer.<JWT>` 정확히 하나가 있어야 한다 | `map_project_yolo/api/ws.py:25-31` | `test_unauthenticated_connections_never_accept_or_call_model` |
| vision-pipeline | 엣지 비전 서비스→User BFF `consume:false` | 연결 때 한도를 쓰지 않고 확인만 한다 | `map_project_yolo/api/ws.py:122`, `map_project_yolo/api/permit.py:33-41` | `test_account_quota_survives_reconnection`(호출 순서 `[False, True, False, …]`) |
| vision-pipeline | 엣지 User BFF→비전 서비스 200 | 응답에 `user_id`·`consent_revision`·`include_location` 이 있어야 한다 | `map_project_yolo/api/permit.py:15-20` | `test_legacy_or_malformed_permission_contract_fails_closed` |
| vision-pipeline | 엣지 비전 서비스→앱 연결 수락 | 협상 응답에 `map.vision.v1` 만 싣는다 | `map_project_yolo/api/ws.py:21,128` | `test_real_asgi_websocket_negotiates_protocol_and_echoes_request_id` |
| vision-pipeline | 띠 ② 요청마다 | 검사 → 한도 사용 → 탐지·식별·검색 순서다 | `map_project_yolo/api/ws.py:141-183` | 코드 대조 |
| vision-pipeline | 엣지 앱→비전 서비스 VisionRequest | 요청 JSON 필드 | `map_project_yolo/schemas/vision_schemas.py:39-65` | `test_invalid_request_never_spends_account_quota` |
| vision-pipeline | 자기 호출 입력 검사·연결 상한·자원 예약 | 외부 호출 전에 크기·형식·상한을 본다 | `map_project_yolo/api/ws.py:141,147,156,164`, `map_project_yolo/vision/frame.py:11-21` | `test_pixel_bomb_is_rejected_before_inference`, `test_busy_inference_does_not_spend_quota` |
| vision-pipeline | 엣지 비전 서비스→User BFF `consume:true` | 처리 직전에 한도 1을 쓰고 개정 번호를 보낸다 | `map_project_yolo/api/ws.py:174-178` | `test_server_location_opt_in_controls_structured_location_before_provider`(`expected_revision` `[None, 1, 1]`) |
| vision-pipeline | 엣지 User BFF→비전 서비스 200(한도 사용) | 위치 동의가 없으면 위치를 지운다 | `map_project_yolo/api/ws.py:179-180` | 같은 시험 |
| vision-pipeline | 자기 호출 YOLO 탐지 | 전용 실행기 하나에서 추론한다 | `map_project_yolo/api/ws.py:97`, `map_project_yolo/vision/runtime.py:14,32-41` | `test_native_inference_timeout_does_not_allow_overlapping_model_calls` |
| vision-pipeline | 엣지 비전 서비스→Kakao 좌표→주소 | 위치가 있고 키가 있을 때만 부른다 | `map_project_yolo/nodes/identify_node.py:55-60` | 코드 대조 |
| vision-pipeline | 엣지 Kakao→비전 서비스 주소 | 도로명 주소 우선, 없으면 지번 | `map_project_yolo/nodes/kakao_local.py:27-35` | 코드 대조 |
| vision-pipeline | 엣지 비전 서비스→Gemini | 사진·질문·탐지 힌트·주소 또는 소수 셋째 자리 좌표를 보낸다 | `map_project_yolo/nodes/identify_node.py:61-99` | `tests/test_nodes.py` 의 식별 시험(모델 대역) |
| vision-pipeline | 엣지 Gemini→비전 서비스 | `name`·`category`·`description`·`search_query` JSON 을 받는다 | `map_project_yolo/nodes/identify_node.py:103-110`, `map_project_yolo/schemas/vision_schemas.py:68-79` | `test_identify_parses_with_and_without_code_fence` |
| vision-pipeline | 엣지 비전 서비스→위키백과 | 검색 쿼리로 검색하고, User-Agent 에 운영자 연락처를 넣는다 | `map_project_yolo/nodes/search_node.py:39-59`, `map_project_yolo/graph/vision_graph.py:26-28` | `test_search_user_agent_carries_operator_contact` |
| vision-pipeline | 엣지 위키백과→비전 서비스 | 제목·요약(태그 제거)·원문 링크 | `map_project_yolo/nodes/search_node.py:64-78` | `test_search_strips_html_and_builds_url` |
| vision-pipeline | 띠 ③ 전송 직전 | 결과를 보내기 전에 권한을 다시 확인한다 | `map_project_yolo/api/ws.py:185-191` | `test_policy_change_while_inference_is_pending_withholds_result` |
| vision-pipeline | 엣지 비전 서비스→User BFF `consume:false` 재확인 | 한도를 다시 쓰지 않는다 | `map_project_yolo/api/ws.py:187` | `test_post_result_permit_uses_real_client_consume_false_wire_contract`(실제 클라이언트, 호출 순서 `[False, True, False]`) |
| vision-pipeline | 엣지 User BFF→비전 서비스(거절이면 닫음) | 거절되면 결과를 버리고 실패 응답 뒤 닫는다 | `map_project_yolo/api/ws.py:192-208` | 같은 시험 |
| vision-pipeline | 엣지 비전 서비스→앱 VisionResponse | 응답 형식과 상태 값 | `map_project_yolo/schemas/vision_schemas.py:96-113`, `map_project_yolo/api/ws.py:205` | `test_timeout_and_detector_exception_return_correlated_failure` |
