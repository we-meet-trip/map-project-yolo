# 기여 안내

MAP 는 교육·학습용으로 공개한 프로젝트다. 운영 중인 서비스가 아니며 지원이나 응답 기한을 약속하지 않는다. 그래도 오류 제보와 개선 제안은 환영한다.

## 어디서 시작하나
- 전체 구조와 한 번에 실행하는 방법은 [map-project-infra](https://github.com/we-meet-trip/map-project-infra) 에서 시작한다.
- 저장소마다 README 의 "빠른 시작" 과 "테스트" 절을 먼저 따라 해 본다.

## 이슈
- 오류 제보: 재현 단계, 기대한 동작, 실제 동작, 환경(OS·런타임 버전)을 적는다.
- 질문·제안: 무엇을 하려는지와 지금 막힌 곳을 적는다.
- 보안 문제는 공개 이슈로 올리지 말고 [SECURITY.md](SECURITY.md) 의 비공개 신고를 쓴다.

## Pull Request
1. 저장소를 fork 하고 `main` 에서 작업 브랜치를 만든다.
2. 변경과 함께 테스트를 추가하거나 고치고, README 의 테스트 명령이 통과하는지 확인한다.
3. PR 템플릿의 확인 항목을 채운다. 한 PR 에는 한 가지 목적만 담는다.

## 커밋 메시지
- 형식: `type: 한국어 명사구` — 예) `fix: 빈 일정 응답의 날짜 누락 처리`, `docs: 데이터 안내 문서의 받는 법 보완`.
- type: `feat` `fix` `docs` `refactor` `test` `chore` `ci` `build` 중 하나.
- 본문에는 왜 바꿨는지를 쓴다.

## 데이터와 비밀값
- 실제 데이터, 외부 서비스에서 받은 응답·이미지·본문, API 키·토큰·인증서·`.env` 를 커밋하지 않는다.
- 테스트에는 작은 합성 데이터만 쓴다. 외부 데이터는 [docs/data.md](docs/data.md) 의 받는 법을 따른다.

## 문서 언어
- README·docs·이슈·PR 은 한국어로 쓴다.
- 코드 식별자, 환경변수, API 필드, 오류 코드는 영어로 둔다.

## 서비스 간 계약을 바꿀 때
- 그 저장소의 `docs/contracts.md` 를 함께 고친다.
- 그 계약을 쓰는 다른 저장소와 [map-project-infra](https://github.com/we-meet-trip/map-project-infra) 의 compose·`.env.example` 도 같이 고쳐야 하는지 확인하고 PR 본문에 적는다.

## 라이선스
기여한 내용은 이 저장소와 같은 [MIT 라이선스](LICENSE)로 배포된다는 데 동의한 것으로 본다.
행동 강령은 [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) 를 따른다.
