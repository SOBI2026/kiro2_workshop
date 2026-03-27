# Requirements Document

## Introduction

이 문서는 실시간 현황 대시보드(포트 8505)의 자동 활성화 및 음성 안내 기능에 대한 요구사항을 정의합니다. 개발자 대시보드(포트 8503)에서 시나리오를 실행하면, 실시간 현황 대시보드가 자동으로 워크플로우를 감지하고 시작하며, 각 단계마다 Amazon Polly를 사용한 음성 안내를 제공합니다.

## Glossary

- **Developer_Dashboard**: 개발자 모니터링 대시보드 (포트 8503), 시나리오 실행 및 시스템 관리 기능 제공
- **Realtime_Dashboard**: 실시간 현황 대시보드 (포트 8505), 워크플로우 진행 상황 시각화 및 음성 안내 제공
- **Workflow_Trigger_Table**: DynamoDB 테이블 (SeniorCare-WorkflowTrigger), 워크플로우 실행 트리거 정보 저장
- **Polly_Service**: Amazon Polly 음성 합성 서비스, 한국어 음성 생성
- **User_Settings_Table**: DynamoDB 테이블 (SeniorCare-UserSettings), 사용자 설정 및 상태 정보 저장
- **Workflow_Step**: 워크플로우의 개별 단계 (센서 데이터 수집, 낙상 감지, 음성 확인, 알림 발송, 완료)
- **Emergency_Status**: 사용자 상태가 'emergency'인 경우, 낙상 또는 응급상황 발생을 의미

## Requirements

### Requirement 1: 워크플로우 트리거 자동 감지

**User Story:** 개발자로서, 실시간 현황 대시보드가 자동으로 워크플로우 시작을 감지하기를 원합니다. 그래야 수동으로 새로고침하거나 버튼을 클릭할 필요가 없습니다.

#### Acceptance Criteria

1. WHEN THE Developer_Dashboard creates a workflow trigger, THE Realtime_Dashboard SHALL detect the trigger within 5 seconds
2. THE Realtime_Dashboard SHALL poll THE Workflow_Trigger_Table every 3 seconds
3. WHEN a new trigger with status 'pending' is detected, THE Realtime_Dashboard SHALL automatically start the workflow execution
4. WHEN the workflow starts, THE Realtime_Dashboard SHALL update the trigger status to 'running' in THE Workflow_Trigger_Table
5. WHEN the workflow completes, THE Realtime_Dashboard SHALL update the trigger status to 'completed' in THE Workflow_Trigger_Table

### Requirement 2: 워크플로우 단계별 음성 안내

**User Story:** 사용자로서, 각 워크플로우 단계마다 음성 안내를 듣기를 원합니다. 그래야 시스템이 무엇을 하고 있는지 청각적으로 확인할 수 있습니다.

#### Acceptance Criteria

1. WHEN a workflow step begins, THE Realtime_Dashboard SHALL generate voice guidance using THE Polly_Service
2. THE Realtime_Dashboard SHALL use Korean language voice (Seoyeon or Jihye) for voice synthesis
3. WHEN voice synthesis completes, THE Realtime_Dashboard SHALL automatically play the audio in the browser
4. THE Realtime_Dashboard SHALL generate voice for each of the 5 workflow steps
5. WHEN voice generation fails, THE Realtime_Dashboard SHALL log the error and continue to the next step

### Requirement 3: 음성 옵션 선택

**User Story:** 개발자로서, 음성 옵션을 선택할 수 있기를 원합니다. 그래야 선호하는 음성 스타일로 안내를 들을 수 있습니다.

#### Acceptance Criteria

1. THE Developer_Dashboard SHALL provide a voice selection dropdown with options 'Seoyeon' and 'Jihye'
2. WHEN THE Developer_Dashboard triggers a workflow, THE Developer_Dashboard SHALL include the selected voice in the trigger data
3. THE Realtime_Dashboard SHALL read the voice selection from THE Workflow_Trigger_Table
4. THE Realtime_Dashboard SHALL use the selected voice for all voice synthesis in that workflow execution
5. WHERE no voice is specified, THE Realtime_Dashboard SHALL default to 'Seoyeon'

### Requirement 4: 응급상황 시각적 경고

**User Story:** 개발자로서, 사용자 상태가 'emergency'로 변경되면 즉시 알림을 받기를 원합니다. 그래야 긴급 상황에 신속하게 대응할 수 있습니다.

#### Acceptance Criteria

1. WHEN THE User_Settings_Table status changes to 'emergency', THE Developer_Dashboard SHALL display a visual alert
2. THE Developer_Dashboard SHALL show the message "⚠️ 응급상황 발생! 즉시 확인 필요"
3. THE Developer_Dashboard SHALL use red color (error styling) for the emergency alert
4. THE Developer_Dashboard SHALL poll THE User_Settings_Table every 5 seconds to check for status changes
5. WHEN the status changes from 'emergency' to 'active', THE Developer_Dashboard SHALL remove the alert

### Requirement 5: 워크플로우 진행 상황 시각화

**User Story:** 사용자로서, 워크플로우의 현재 진행 상황을 시각적으로 확인하기를 원합니다. 그래야 어느 단계가 실행 중인지 알 수 있습니다.

#### Acceptance Criteria

1. THE Realtime_Dashboard SHALL display all 5 workflow steps with distinct visual states
2. WHEN a step is not yet started, THE Realtime_Dashboard SHALL display it with inactive styling (gray background)
3. WHILE a step is executing, THE Realtime_Dashboard SHALL display it with active styling (orange background with pulse animation)
4. WHEN a step completes successfully, THE Realtime_Dashboard SHALL display it with success styling (green background)
5. IF a step is the fall detection step, THEN THE Realtime_Dashboard SHALL display it with warning styling (red background)

### Requirement 6: 음성 파일 생성 및 저장

**User Story:** 개발자로서, 생성된 음성 파일이 저장되기를 원합니다. 그래야 나중에 재생하거나 디버깅할 수 있습니다.

#### Acceptance Criteria

1. WHEN THE Polly_Service generates voice audio, THE Realtime_Dashboard SHALL save it to the 'voice_outputs' directory
2. THE Realtime_Dashboard SHALL name the file with pattern 'auto_demo_HHMMSS.mp3' where HHMMSS is the current time
3. THE Realtime_Dashboard SHALL create the 'voice_outputs' directory if it does not exist
4. WHEN saving fails, THE Realtime_Dashboard SHALL log the error and continue execution
5. THE Realtime_Dashboard SHALL use MP3 format for all voice files

### Requirement 7: 워크플로우 로그 기록

**User Story:** 개발자로서, 워크플로우 실행 중 모든 이벤트가 로그로 기록되기를 원합니다. 그래야 문제 발생 시 디버깅할 수 있습니다.

#### Acceptance Criteria

1. THE Realtime_Dashboard SHALL log each workflow step with timestamp in KST timezone
2. THE Realtime_Dashboard SHALL display logs in a scrollable console-style container
3. THE Realtime_Dashboard SHALL include log level (INFO, SUCCESS, WARNING, ERROR) for each log entry
4. THE Realtime_Dashboard SHALL limit the displayed logs to the most recent 30 entries
5. WHEN a workflow completes, THE Realtime_Dashboard SHALL log the completion message with SUCCESS level

### Requirement 8: 보호자 정보 로드 및 표시

**User Story:** 개발자로서, 워크플로우 실행 시 보호자 정보가 자동으로 로드되기를 원합니다. 그래야 누구에게 알림이 발송되는지 확인할 수 있습니다.

#### Acceptance Criteria

1. WHEN a workflow starts, THE Realtime_Dashboard SHALL load guardian information from THE User_Settings_Table
2. THE Realtime_Dashboard SHALL display guardian name, phone number, email, and relation
3. WHEN guardian information is not found, THE Realtime_Dashboard SHALL use default values and display a warning
4. THE Realtime_Dashboard SHALL log the loaded guardian information with INFO level
5. THE Realtime_Dashboard SHALL display the information in an info box during workflow execution

### Requirement 9: SMS 알림 실제 발송

**User Story:** 개발자로서, 워크플로우 실행 시 실제 SMS가 발송되기를 원합니다. 그래야 전체 시스템이 제대로 작동하는지 확인할 수 있습니다.

#### Acceptance Criteria

1. WHEN the workflow reaches the notification step, THE Realtime_Dashboard SHALL send an actual SMS using AWS SNS
2. THE Realtime_Dashboard SHALL format the phone number from '010-XXXX-XXXX' to '+8210XXXXXXXX'
3. THE Realtime_Dashboard SHALL include emergency information in the SMS message
4. WHEN SMS sending succeeds, THE Realtime_Dashboard SHALL log the MessageId with SUCCESS level
5. IF SMS sending fails, THEN THE Realtime_Dashboard SHALL log the error with ERROR level and continue execution

### Requirement 10: 워크플로우 완료 후 상태 복구

**User Story:** 개발자로서, 워크플로우 완료 후 사용자 상태가 자동으로 복구되기를 원합니다. 그래야 다음 테스트를 위해 수동으로 상태를 변경할 필요가 없습니다.

#### Acceptance Criteria

1. WHEN the workflow completes all steps, THE Realtime_Dashboard SHALL update the user status from 'emergency' to 'active'
2. THE Realtime_Dashboard SHALL update the status in THE User_Settings_Table
3. WHEN status update succeeds, THE Realtime_Dashboard SHALL log the change with SUCCESS level
4. IF status update fails, THEN THE Realtime_Dashboard SHALL log the error with ERROR level
5. THE Realtime_Dashboard SHALL display a completion message with balloons animation
