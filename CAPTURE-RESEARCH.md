# Text Box 캡처 전략 조사 결과

> 목표: 싱글라인이든 멀티라인이든, 직접 타이핑이든 히스토리에서 로드한 것이든,
> text box에 있는 텍스트를 **안정적으로 캡처하고 번역**하는 방법 찾기.

---

## 1. 대상 앱 입력 스택 조사 결과

### Claude Code

| 항목 | 값 |
|---|---|
| **TUI 프레임워크** | Ink (React for CLI) + Node `readline` + 커스텀 raw TTY |
| **prompt_toolkit?** | ❌ 아님 |
| **제출** | `Enter` |
| **줄바꿈** | `\` + Enter, Option+Enter, Shift+Enter, Ctrl+J |
| **Up/Down** | 히스토리 탐색 (vim모드: 버퍼 내 이동 후 경계에서 히스토리) |
| **Ctrl+U** | 전체 줄 삭제 |
| **Ctrl+K** | 커서부터 줄 끝까지 삭제 |
| **Ctrl+Y** | 삭제된 텍스트 붙여넣기 |
| **외부 에디터** | **Ctrl+G** → $VISUAL/$EDITOR 로 열기 |
| **Select All** | 없음 (문서화된 바인딩 없음) |

> 소스: npm 패키지 번들 분석 + 공식 docs (`interactive-mode`, `keybindings`)

### OpenCode (현재 버전)

| 항목 | 값 |
|---|---|
| **TUI 프레임워크** | @opentui/core + @opentui/solid (TypeScript) |
| **Go/BubbleTea?** | ❌ 현재 버전은 TypeScript (과거 Go였으나 리라이트) |
| **제출** | `Enter` |
| **줄바꿈** | Shift+Enter, Ctrl+Enter, Alt+Enter, Ctrl+J |
| **Up/Down** | 멀티라인 내 커서 이동, 경계(맨 위/아래)에서 히스토리 전환 |
| **Ctrl+U** | 커서부터 줄 시작까지 삭제 |
| **Ctrl+K** | 커서부터 줄 끝까지 삭제 |
| **Home/End** | 버퍼 시작/끝 이동 |
| **Shift+Home/End** | 버퍼 시작/끝까지 선택 |
| **Ctrl+Shift+D** | 줄 삭제 |
| **외부 에디터** | **`<leader>e`** (기본 leader=Ctrl+X) 또는 `/editor` 명령어 |
| **Select All** | 없음 (전용 바인딩 없음, 단 Shift+Home/End로 선택 가능) |

> 소스: GitHub `anomalyco/opencode` 소스코드 직접 분석

### prompt_toolkit (참고용 — Python readline 앱)

| 항목 | 값 |
|---|---|
| **Ctrl+Home** | `beginning-of-buffer` (버퍼 맨 처음으로) |
| **Ctrl+End** | `end-of-buffer` (버퍼 맨 끝으로) |
| **Ctrl+Space** | 선택 시작 (mark 설정) |
| **Ctrl+W** (선택 중) | 선택 영역 잘라내기 |
| **Ctrl+Y** | 붙여넣기 (yank) |
| **Escape+<** | 히스토리 처음으로 (버퍼 시작 아님!) |
| **Ctrl+U** | 커서부터 **현재 줄** 시작까지만 삭제 (전체 버퍼 아님) |

> 소스: prompt_toolkit `named_commands.py` + `emacs.py` 직접 분석

---

## 2. 현재 접근 (Ctrl+U/Y)의 정확한 한계

### 싱글라인 캡처: 동작함 (두 앱 모두)

```
Ctrl+E → Ctrl+U → Ctrl+Y → read PTY output
```

- Claude Code: Ctrl+U가 전체 줄을 삭제 → kill buffer에 저장 → Ctrl+Y로 복원 ✓
- OpenCode: Ctrl+E + Ctrl+U가 줄 전체를 삭제 → 동일 패턴 ✓
- 히스토리에서 로드한 싱글라인 텍스트도 캡처됨 ✓

### 멀티라인 캡처: **동작하지 않음**

현재 방식(`_capture_all_lines`의 Up arrow 접근):
- Claude Code: Up arrow = **히스토리 탐색** → 이전 대화를 캡처 ✗
- OpenCode: Up arrow = 멀티라인 커서 이동 → **경계에서 히스토리로 전환** → 불확실 ✗

**Ctrl+U는 두 앱 모두 현재 줄만 삭제하므로, 멀티라인 전체를 한 번에 캡처할 방법이 Ctrl+U/Y로는 없음.**

---

## 3. 발견된 해결 경로 3가지

### 경로 A: 외부 에디터 인터셉션 (가장 안정적)

**핵심 발견: Claude Code와 OpenCode 모두 "외부 에디터로 열기" 기능을 지원**

| 앱 | 외부 에디터 트리거 | 동작 |
|---|---|---|
| Claude Code | `Ctrl+G` | $VISUAL/$EDITOR로 버퍼 내용을 temp 파일에 쓰고 열기 |
| OpenCode | `Ctrl+X e` (leader+e) | 동일하게 temp 파일 → $VISUAL/$EDITOR |

**작동 원리:**

```
사용자 입력: Ctrl+T (번역 핫키)
                ↓
프록시: EDITOR를 우리 번역 스크립트로 설정
                ↓
프록시: 앱에 Ctrl+G (Claude) 또는 Ctrl+X e (OpenCode) 전송
                ↓
앱: 버퍼 내용을 /tmp/xxx.txt에 쓰고, 우리 "에디터" 실행
                ↓
우리 스크립트: 파일 읽기 → 번역 API 호출 → 결과를 파일에 쓰기 → 종료
                ↓
앱: 수정된 파일 읽기 → 버퍼를 번역된 텍스트로 교체
```

**장점:**
- ✅ 싱글/멀티라인 구분 없이 **전체 버퍼를 완전히 캡처**
- ✅ 히스토리에서 로드한 텍스트도 캡처됨
- ✅ 타이밍 문제 없음 (파일 I/O 기반)
- ✅ ANSI 스트리핑 불필요 (plain text 파일)
- ✅ 앱의 공식 기능을 사용하므로 호환성 보장
- ✅ 번역 결과 주입도 앱이 직접 처리 (Enter/자동완성 간섭 없음)

**단점:**
- ⚠️ 앱마다 다른 외부 에디터 트리거 키 → target_cmd 기반으로 구분 필요
- ⚠️ 사용자가 직접 외부 에디터를 열고 싶을 때 충돌 → 모드 전환 필요
- ⚠️ 화면 깜빡임 (에디터 open/close 사이클) → 스크립트가 빠르면 최소화 가능
- ⚠️ 번역 API 지연 시 에디터가 "멈춘" 것처럼 보임

**구현 설계:**
```python
# 프록시 시작 시
os.environ["TUI_TRANSLATOR_REAL_EDITOR"] = os.environ.get("EDITOR", "vi")
os.environ["EDITOR"] = "tui-translator-edit"  # 우리 래퍼 스크립트
os.environ["VISUAL"] = "tui-translator-edit"

# tui-translator-edit 스크립트:
#   if TUI_TRANSLATOR_MODE == "translate":
#     1. 파일 읽기
#     2. 번역 API 호출
#     3. 결과 쓰기
#     4. 종료
#   else:
#     exec $TUI_TRANSLATOR_REAL_EDITOR "$@"

# Ctrl+T 처리:
#   1. os.environ["TUI_TRANSLATOR_MODE"] = "translate" 설정
#   2. target에 따라 Ctrl+G 또는 Ctrl+X e 전송
#   3. 앱이 에디터를 열고 닫으면 버퍼가 번역됨
#   4. os.environ["TUI_TRANSLATOR_MODE"] = "" 리셋
```

---

### 경로 B: 향상된 싱글라인 Ctrl+U/Y + Ctrl+K 반복 킬 (중간 안정성)

**아이디어**: readline에서 연속된 Ctrl+K는 kill ring에 누적됨. 이를 이용해 멀티라인 캡처:

```
1. Ctrl+E              → 현재 줄 끝
2. Ctrl+K              → 줄 끝까지 삭제 (newline이면 다음 줄과 합침)
3. Ctrl+K 반복         → 계속 삭제하면서 kill ring에 누적
4. (모든 텍스트 삭제될 때까지 반복)
5. Ctrl+Y              → kill ring 전체를 yank → PTY에서 읽기
```

**문제점:**
- Claude Code가 readline의 kill concatenation을 지원하는지 불확실
- OpenCode가 이 패턴을 지원하는지 불확실
- 여전히 타이밍 의존적
- 반복 횟수를 알 수 없음 (언제 모든 텍스트가 삭제됐는지 감지 어려움)

**판정: 앱별 동작이 불확실해서 보편적 해결책이 못 됨.**

---

### 경로 C: Shadow Buffer + 히스토리 감지 하이브리드 (보완용)

**아이디어**: 사용자 키스트로크를 프록시에서 추적하면서, 히스토리 로드 시 캡처로 폴백

```
1. 모든 키스트로크를 Shadow Buffer에 기록 (현재 buffer.py가 이미 존재)
2. 직접 타이핑한 텍스트: Shadow Buffer에서 직접 가져옴 (빠르고 확실)
3. Up arrow 감지 → Shadow Buffer를 "stale" 마킹
4. Stale 상태에서 번역 요청 → Ctrl+U/Y 싱글라인 캡처로 폴백
5. 또는 Stale 상태에서 → 외부 에디터 경로(A)로 폴백
```

**장점:**
- 직접 타이핑의 경우 즉시 캡처 (API 호출 전 대기 없음)
- 캡처 실패 확률 크게 감소

**단점:**
- Shadow Buffer가 커서 이동을 완벽하게 추적하지 못함 (현재 구현은 append-only)
- 히스토리 로드 시 여전히 폴백 필요

---

## 4. 권장 전략: A + C 하이브리드

```
Ctrl+T 눌림
    ↓
Shadow Buffer가 유효한가?  ──Yes──→ Shadow Buffer에서 텍스트 가져옴
    ↓ No (Up arrow 등으로 stale)       ↓
    ↓                               텍스트가 싱글라인인가?
    ↓                                 ↓ Yes         ↓ No
    ↓                           Ctrl+E/U/Y 캡처    외부 에디터 경로
    ↓
외부 에디터 경로 (경로 A)
    ↓
번역 API 호출
    ↓
결과 주입:
  - 외부 에디터 경로: 앱이 자체 처리
  - Ctrl+U/Y 경로: Bracketed Paste로 주입
```

### 주입 개선: Bracketed Paste

번역 결과를 자식 앱에 주입할 때:
```python
# 현재 (위험):
os.write(master_fd, result.encode("utf-8"))

# 개선 (안전):
os.write(master_fd, b"\x1b[200~" + result.encode("utf-8") + b"\x1b[201~")
```

Bracketed Paste가 해결하는 것:
- ✅ `\n`이 Enter로 해석되지 않음 (제출 트리거 방지)
- ✅ 자동완성 트리거 안 됨
- ✅ 괄호 자동 매칭 안 됨
- ✅ 구문 하이라이팅 깜빡임 최소화

---

## 5. 구현 우선순위

| 순서 | 작업 | 영향 | 난이도 |
|---|---|---|---|
| 1 | Ctrl+T T (Up arrow 멀티라인) 비활성화 | C-1 버그 제거 | 쉬움 |
| 2 | Bracketed Paste로 결과 주입 변경 | H-1, H-2 해결 | 쉬움 |
| 3 | 외부 에디터 인터셉션 구현 (경로 A) | **멀티라인 + 히스토리 완전 해결** | 중간 |
| 4 | target_cmd 기반 에디터 트리거 키 매핑 | claude=Ctrl+G, opencode=Ctrl+X e | 쉬움 |
| 5 | Ctrl+T를 단일 동작으로 (chord 제거) | UX 단순화, 싱글라인 빠른 번역 | 쉬움 |
| 6 | Shadow Buffer 개선 (커서 추적) | 직접 타이핑 시 즉시 캡처 | 중간 |
| 7 | Undo를 프록시 로컬로 재구현 | H-3 해결 | 중간 |

---

## 6. 앱별 키 시퀀스 매트릭스

번역 프록시가 알아야 하는 핵심 키 시퀀스:

| 동작 | Claude Code | OpenCode | bash/readline |
|---|---|---|---|
| 줄 끝 이동 | Ctrl+E | Ctrl+E / End | Ctrl+E |
| 줄 삭제 | Ctrl+U | Ctrl+E + Ctrl+U | Ctrl+U |
| 삭제 텍스트 붙여넣기 | Ctrl+Y | Ctrl+Y | Ctrl+Y |
| 제출 | Enter | Enter | Enter |
| 줄바꿈 | Ctrl+J / Shift+Enter | Ctrl+J / Shift+Enter | 해당없음 |
| 히스토리 이전 | Up | Up (경계에서만) | Up |
| 외부 에디터 | **Ctrl+G** | **Ctrl+X e** | Ctrl+X Ctrl+E |
| 버퍼 시작 | 미확인 | Home | Ctrl+A |
| 버퍼 끝 | 미확인 | End | Ctrl+E |
