# Implementation Plan: 실시간 현황 대시보드 자동 활성화 및 음성 안내

## Overview

개발자 대시보드(8503)에서 시나리오 실행 시 실시간 현황 대시보드(8505)가 DynamoDB 폴링을 통해 자동으로 워크플로우를 감지하고, Amazon Polly 기반 한국어 음성 안내를 제공하는 기능을 구현합니다.

## Tasks

- [-] 1. 서비스 모듈 구조 설정
  - [x] 1.1 dashboard/services/ 디렉토리 생성 및 __init__.py 작성
    - 서비스 모듈 패키지 초기화
    - _Requirements: 1.1, 1.2_
  
  - [x] 1.2 LogService 클래스 구현
    - KST 타임스탬프 포함 로그 추가 기능
    - 로그 레벨 (INFO, SUCCESS, WARNING, ERROR) 지원
    - 최대 30개 로그 유지
    - _Requirements: 7.1, 7.3, 7.4, 7.5_
  
  - [ ]* 1.3 LogService 속성 테스트 작성
    - **Property 8: 로그 형식 일관성**
    - **Validates: Requirements 7.1, 7.3, 7.4, 7.5**

- [-] 2. WorkflowTriggerService 구현
  - [x] 2.1 WorkflowTriggerService 클래스 구현
    - create_trigger: 새 워크플로우 트리거 생성
    - get_pending_trigger: pending 상태 트리거 조회
    - update_status: 상태 업데이트 (pending → running → completed)
    - _Requirements: 1.3, 1.4, 1.5, 3.2, 3.3_
  
  - [ ]* 2.2 트리거 상태 전이 속성 테스트 작성
    - **Property 1: 트리거 상태 전이 일관성**
    - **Validates: Requirements 1.4, 1.5**
  
  - [ ]* 2.3 트리거 데이터 음성 포함 속성 테스트 작성
    - **Property 5: 트리거 데이터 음성 포함**
    - **Validates: Requirements 3.2, 3.3**

- [-] 3. VoiceService 구현
  - [x] 3.1 VoiceService 클래스 구현
    - synthesize: Polly 음성 합성 및 파일 저장
    - get_step_message: 단계별 음성 메시지 반환
    - voice_outputs 디렉토리 자동 생성
    - 파일명 패턴: auto_demo_HHMMSS.mp3
    - _Requirements: 2.1, 2.2, 2.4, 2.5, 3.4, 3.5, 6.1, 6.2, 6.3, 6.4, 6.5_
  
  - [ ]* 3.2 음성 파일 저장 규칙 속성 테스트 작성
    - **Property 7: 음성 파일 저장 규칙**
    - **Validates: Requirements 6.1, 6.2, 6.5**
  
  - [ ]* 3.3 음성 선택 일관성 속성 테스트 작성
    - **Property 3: 음성 선택 일관성**
    - **Validates: Requirements 2.2, 3.4**

- [-] 4. NotificationService 구현
  - [x] 4.1 NotificationService 클래스 구현
    - format_phone_number: 010-XXXX-XXXX → +8210XXXXXXXX 변환
    - send_sms: AWS SNS SMS 발송
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_
  
  - [ ]* 4.2 전화번호 포맷 변환 속성 테스트 작성
    - **Property 10: 전화번호 포맷 변환**
    - **Validates: Requirements 9.2**
  
  - [ ]* 4.3 SMS 메시지 응급 정보 포함 속성 테스트 작성
    - **Property 11: SMS 메시지 응급 정보 포함**
    - **Validates: Requirements 9.3, 9.4**

- [ ] 5. Checkpoint - 서비스 모듈 검증
  - Ensure all tests pass, ask the user if questions arise.

- [-] 6. WorkflowEngine 구현
  - [x] 6.1 WorkflowEngine 클래스 구현
    - 5단계 워크플로우 정의 (STEPS 상수)
    - execute: 전체 워크플로우 실행
    - execute_step: 개별 단계 실행
    - 콜백 기반 UI 업데이트 지원
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_
  
  - [ ]* 6.2 낙상 감지 단계 스타일링 속성 테스트 작성
    - **Property 6: 낙상 감지 단계 스타일링**
    - **Validates: Requirements 5.5**
  
  - [ ]* 6.3 5단계 음성 생성 속성 테스트 작성
    - **Property 4: 5단계 음성 생성**
    - **Validates: Requirements 2.4**

- [-] 7. app_v3.py 리팩토링 - 서비스 통합
  - [x] 7.1 서비스 모듈 import 및 초기화
    - LogService, WorkflowTriggerService, VoiceService, NotificationService, WorkflowEngine 통합
    - _Requirements: 1.1, 1.2_
  
  - [-] 7.2 DynamoDB 폴링 기반 자동 감지 구현
    - 3초 간격 폴링
    - pending 트리거 감지 시 자동 워크플로우 시작
    - _Requirements: 1.2, 1.3_
  
  - [ ]* 7.3 Pending 트리거 자동 시작 속성 테스트 작성
    - **Property 2: Pending 트리거 자동 시작**
    - **Validates: Requirements 1.3**

- [ ] 8. 보호자 정보 로드 및 상태 복구 구현
  - [x] 8.1 보호자 정보 로드 기능 구현
    - UserSettings 테이블에서 보호자 정보 로드
    - 정보 없을 시 기본값 사용 및 경고 표시
    - INFO 레벨 로깅
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_
  
  - [ ]* 8.2 보호자 정보 로드 및 표시 속성 테스트 작성
    - **Property 9: 보호자 정보 로드 및 표시**
    - **Validates: Requirements 8.1, 8.2, 8.4**
  
  - [x] 8.3 워크플로우 완료 후 상태 복구 구현
    - emergency → active 상태 변경
    - UserSettings 테이블 업데이트
    - SUCCESS 레벨 로깅
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_
  
  - [ ]* 8.4 워크플로우 완료 후 상태 복구 속성 테스트 작성
    - **Property 12: 워크플로우 완료 후 상태 복구**
    - **Validates: Requirements 10.1, 10.2, 10.3**

- [ ] 9. Checkpoint - 통합 검증
  - Ensure all tests pass, ask the user if questions arise.

- [-] 10. app.py 업데이트 - 응급상황 경고 표시
  - [x] 10.1 응급상황 시각적 경고 구현
    - User_Settings_Table status 'emergency' 감지
    - "⚠️ 응급상황 발생! 즉시 확인 필요" 메시지 표시
    - 빨간색 에러 스타일링 적용
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 11. Final Checkpoint - 전체 시스템 검증
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- 기존 dashboard/app_v3.py 코드를 서비스 모듈로 리팩토링하여 테스트 가능성 향상
- Python + Hypothesis 라이브러리로 속성 기반 테스트 구현
- 모든 음성 합성은 Amazon Polly 한국어 음성 (Seoyeon/Jihye) 사용
