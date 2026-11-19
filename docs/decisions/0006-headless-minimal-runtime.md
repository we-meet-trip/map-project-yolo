# 0006. 실행 이미지는 headless·CPU 전용·최소 권한으로 만들고, 빌드 때 검사한다

- 상태: 채택

## 맥락
서버에는 화면이 없고 GPU 도 쓰지 않는다. 기본 ultralytics 배포판은 GUI 판 OpenCV 를 끌고 와서 GUI 계열 시스템 라이브러리가 필요하다. PyPI 의 torch 는 CUDA 를 함께 담아 이미지가 커진다.

## 선택지
1. 기본 배포판과 시스템 라이브러리를 그대로 쓴다.
2. headless 배포판, CPU 인덱스 torch, 필요 없는 실행 파일 제거, 비루트 실행으로 줄이고, 줄인 결과를 빌드 단계에서 검사한다.

## 결정
2번. `ultralytics-opencv-headless` 와 `opencv-python-headless` 를 쓰고, torch 는 CPU 인덱스에서 먼저 골라 제약으로 고정한다. 비루트 사용자(uid 10001)로 실행하고, perl 을 지우고 setuid·setgid 비트를 없앤다. 빌드 마지막에 네트워크를 끈 채 `scripts/verify-headless-runtime.py` 로 설치 패키지, GUI 라이브러리 부재, CUDA 부재, 합성 JPEG 추론을 확인한다.

## 결과
- 이미지가 작고, 실행 중 쓸 수 있는 도구가 적다.
- 줄인 것이 다음 업그레이드에서 다시 들어오면 빌드가 실패해서 알아챈다. 이미지 감사 워크플로가 같은 점검과 취약점 검사를 PR·수동 실행으로 돌린다.
