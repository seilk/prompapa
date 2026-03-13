# tui-translator 안정성 분석 — Corner Cases & Known Issues

> 분석 기준: 실제 사용자가 `tui-translator`를 일상적으로 사용할 때 겪을 수 있는 모든 불편/오작동 시나리오.
> 대상 환경: claude CLI, opencode 등 prompt_toolkit 기반 앱을 PTY 프록시로 감싸는 구성.

---

## 🔴 CRITICAL — 지금 깨져 있는 것

### C-1. Ctrl+T T (전체 번역)가 대화 히스토리를 캡처함

**증상**: "테스트 테스트"만 입력 후 Ctrl+T T → 이전 대화 내용, 시스템 메시지, 이전 번역 결과가 합쳐져서 번역됨

**근본 원인**: `_capture_all_lines()`가 Up arrow(`\x1b[A`)를 보내서 "이전 줄"을 캡처하지만, prompt_toolkit 기반 앱(claude, opencode)에서 Up arrow는 **멀티라인 버퍼 내 이동**이 아니라 **명령 히스토리 탐색**임.

```python
# app.py:190-202 — Up arrow = 히스토리 탐색이므로 이전 대화 메시지를 캡처
for _ in range(MAX_LINES):
    os.write(master_fd, b"\x1b[A")  # 히스토리의 이전 항목으로 이동
    line = await _capture_current_line()  # 그 항목의 텍스트를 캡처
    lines.append(line)  # → 대화 히스토리가 쌓임
```

**영향**: Ctrl+T T는 prompt_toolkit 앱에서 사실상 **사용 불가**. 현재 입력만 번역하는 게 아니라 이전 대화 전체를 긁어와서 API에 전송.

**TODO.md에 이미 기록되어 있었으나 Ctrl+T chord 구현 시 선결 조건 미확인:**
> *"prompt_toolkit (claude/opencode) Up arrow behavior in multiline context needs verification before implementing"*

---

### C-2. 타이밍 의존적 캡처 — 환경에 따라 비결정적 결과

**증상**: 같은 입력인데 어떨 때는 제대로, 어떨 때는 빈 문자열 또는 깨진 텍스트가 캡처됨

**근본 원인**: 모든 캡처 단계가 하드코딩된 `asyncio.sleep()`과 `_read_with_timeout()`에 의존:

| 단계 | 대기 시간 | 위험 |
|---|---|---|
| 스테일 데이터 드레인 | 20ms timeout | 자식 앱이 아직 출력 중이면 누락 |
| Ctrl+E 응답 대기 | 30ms sleep + 50ms timeout | 느린 터미널에서 응답 미수신 |
| Ctrl+U 응답 대기 | 50ms sleep + 300ms timeout | 부하 높은 시스템에서 부족 |
| Ctrl+Y 응답 대기 | 50ms sleep + 300ms timeout | SSH 원격 세션에서 레이턴시 추가 |
| Up arrow 응답 대기 | 80ms sleep + 50ms timeout | prompt_toolkit 렌더링 지연 시 부족 |

**결과**: SSH 환경, 시스템 부하, 자식 앱의 렌더링 속도에 따라 캡처 성공률이 달라짐. 재현이 어려운 간헐적 실패를 유발.

---

### C-3. 캡처 중 자식 앱의 비동기 출력이 혼입됨

**증상**: 캡처된 텍스트에 프롬프트 문자열, 상태 표시줄 텍스트, 알림 메시지가 섞임

**근본 원인**: `_capture_current_line()`에서 Ctrl+Y 후 `_read_with_timeout()`은 **yank된 텍스트만** 읽어야 하지만, 같은 fd에서 자식 앱의 다른 출력(프롬프트 재그리기, 상태바 업데이트 등)도 함께 읽힘. `_strip_ansi()`는 ANSI 이스케이프만 제거하고 **내용은 구분 불가**.

```python
# 이 시점에서 raw에는 yank된 텍스트 + 자식 앱의 프롬프트 재렌더링이 섞일 수 있음
raw = _read_with_timeout(master_fd)
captured = _strip_ansi(raw)  # ANSI만 제거, 프롬프트 텍스트는 남음
```

---

## 🟠 HIGH — 사용 중 자주 겪을 문제

### H-1. 번역 결과 주입 시 자식 앱의 입력 처리가 간섭

**증상**: 번역된 영어 텍스트가 입력되면서 자동완성 팝업이 뜨거나, 괄호가 이중으로 입력되거나, 하이라이팅이 깜빡임

**원인**: `os.write(master_fd, result.encode("utf-8"))`는 자식 앱 입장에서 사용자가 매우 빠르게 타이핑하는 것과 동일. prompt_toolkit의 자동완성, 괄호 매칭, 구문 하이라이팅이 모두 반응함.

**특히 위험한 케이스**:
- 번역 결과에 `(`, `[`, `{` → 자동 닫기 괄호 추가
- 번역 결과에 `"`, `'` → 자동 페어링
- 번역 결과에 탭 문자 → 자동완성 트리거
- 번역 결과에 `\n` → **Enter로 해석되어 메시지가 전송될 수 있음**

### H-2. 번역 결과의 개행문자가 메시지 제출을 트리거

**증상**: 번역 결과가 여러 줄이면, `\n`이 Enter로 해석되어 번역 중간에 메시지가 전송됨

**원인**: `os.write(master_fd, result.encode())` 할 때 `\n`은 자식 앱 입장에서 Enter키. claude CLI는 Enter를 메시지 제출로 처리하므로 **번역 결과의 첫 줄만 제출되고 나머지는 유실**되거나, 여러 불완전한 메시지가 연속 전송됨.

### H-3. Undo가 멀티라인에서 작동하지 않음

**증상**: 번역 후 Ctrl+Z로 undo하면 현재 줄만 복원되고, 이전 줄들은 번역된 상태로 남음

**원인**: `do_undo()`는 Ctrl+E(줄 끝) + Ctrl+U(줄 삭제) + 복원 텍스트 입력만 수행. 이것은 **현재 줄 하나만** 삭제/복원하므로, 멀티라인 번역 결과의 이전 줄들은 건드리지 못함.

```python
def do_undo():
    os.write(master_fd, b"\x05")   # Ctrl+E — 현재 줄 끝으로
    os.write(master_fd, b"\x15")   # Ctrl+U — 현재 줄만 삭제
    os.write(master_fd, restored.encode("utf-8"))  # 복원 (하지만 이전 줄들은?)
```

### H-4. Ctrl+Z가 프로세스 일시정지(SIGTSTP)를 삼킴

**증상**: 터미널에서 Ctrl+Z로 프로세스를 백그라운드로 보낼 수 없음

**원인**: `handle_stdin()`에서 `b"\x1a"` (Ctrl+Z)를 무조건 가로채서 undo로 처리. SIGTSTP 시그널이 자식 프로세스에 절대 전달되지 않음.

```python
if b"\x1a" in data:
    if not translating:
        do_undo()
    return  # 자식에게 절대 전달 안 됨
```

### H-5. "translating..." 표시가 TUI 레이아웃을 파괴

**증상**: claude/opencode의 복잡한 TUI 화면에서 번역 중 표시가 화면을 깨뜨림

**원인**: `\r\x1b[2K`는 **현재 커서 줄을 완전히 지우고** 텍스트를 쓰는데, claude CLI의 TUI는 다중 패널 레이아웃이므로 상태바, 입력창, 출력창이 섞여 있음. 단순 줄 지우기가 TUI 렌더링을 손상시킴.

---

## 🟡 MEDIUM — 사용성 저하 & 엣지케이스

### M-1. Chord 모드에 피드백 없음

**증상**: Ctrl+T를 누르면 아무 반응 없이 T 또는 L을 기다림. 사용자는 Ctrl+T가 먹었는지 모름.

**개선**: Ctrl+T 입력 시 "T: full / L: line" 같은 힌트를 잠깐 표시해야 함.

### M-2. 잘못된 chord 키 → 무음 취소

**증상**: Ctrl+T 후 T/L이 아닌 키를 누르면 아무 일도 안 일어남. 키 입력도 삼켜짐.

```python
# app.py:292 — T/L 아닌 키는 그냥 버려짐
# anything else: discard (cancel chord)
return
```

**문제**: 사용자가 빠르게 타이핑하다가 실수로 Ctrl+T를 누르면, 다음 글자가 사라짐.

### M-3. 번역 취소 불가

**증상**: 번역 API 호출이 시작되면 응답이 올 때까지(최대 30초) 아무것도 할 수 없음.

**원인**: `rewrite_to_english()`가 완료될 때까지 `await`. 취소 메커니즘 없음.

### M-4. 빠른 타이핑 시 Ctrl+T가 데이터 중간에서 감지됨

**증상**: 빠르게 타이핑하다가 우연히 Ctrl+T(0x14)가 포함되면 chord 모드 진입

**원인**: `if b"\x14" in data` — 1024바이트 청크 어디에든 0x14가 있으면 **전체 청크가 삼켜짐** (자식에 전달 안 됨). 그 바이트 전후의 일반 키입력도 함께 사라짐.

```python
if b"\x14" in data:
    if not translating:
        waiting_chord = True
    return  # data 전체가 버려짐 — 0x14 이전/이후 바이트 포함
```

### M-5. 마스킹이 백틱만 커버

**증상**: 백틱 없이 쓴 파일 경로, URL, 셸 명령어가 번역됨

```
입력: "src/auth.ts 수정해줘"
기대: "Modify src/auth.ts"
실제: "Modify the source/authentication.ts" (경로가 번역됨)
```

### M-6. `os.waitpid(-1, ...)` 가 다른 자식 프로세스를 잡을 수 있음

**원인**: `-1`은 **모든** 자식 프로세스를 기다림. fork된 특정 PID가 아니라 아무 자식이 종료되면 루프 탈출.

```python
# app.py:323 — pid 대신 -1 사용
result = os.waitpid(-1, os.WNOHANG)
if result[0] != 0:
    break  # 다른 자식 프로세스 종료 시에도 여기서 탈출
```

### M-7. `_read_with_timeout` 기본값 0.3초가 인터랙티브 느낌을 해침

**증상**: 캡처 실패 시(타임아웃) 전체 번역 과정이 0.3s × 여러 단계 = 체감 1-2초 지연

**원인**: `_read_with_timeout(fd, timeout=0.3)` — 데이터가 없을 때 0.3초 대기. 캡처 단계별로 여러 번 호출되므로 누적.

---

## 🔵 LOW — 개선 권장

### L-1. `.env`가 `.gitignore`에 없음

**현황**: `.env`에 `GOOGLE_API_KEY` 포함. git에 아직 트래킹되진 않지만(untracked), `.gitignore`에 없어서 `git add .` 시 실수로 커밋될 위험.

### L-2. 캡처 텍스트 크기 제한 없음

**위험**: 대량의 텍스트가 캡처되면 그대로 번역 API로 전송 → 비용 증가, 타임아웃

### L-3. PROMPT_TOOLKIT_NO_CPR=1 이 자식 앱 UI를 깨뜨릴 수 있음

**원인**: CPR(Cursor Position Report) 비활성화는 prompt_toolkit의 정확한 커서 위치 감지를 막음. 자식 앱의 레이아웃이 어긋날 수 있음.

### L-4. 설정 핫리로드 미지원

변경 시 tui-translator 재시작 필요.

### L-5. Google Translate 는 코딩 맥락을 모름

"이 함수 리팩토링해줘" 같은 코딩 지시가 자연스러운 영어로 안 나올 수 있음. (LLM provider 사용 시에만 시스템 프롬프트가 적용됨)

---

## 구조적 분석 — 왜 이 문제들이 생기는가

### 핵심 딜레마: PTY 프록시의 근본 한계

이 도구는 **자식 프로세스의 입력 버퍼에 직접 접근할 방법이 없는** PTY 프록시입니다.

```
┌──────────────────────────────────────────────────────┐
│                   tui-translator (부모)                │
│                                                        │
│  stdin ──→ [핫키 가로채기] ──→ os.write(master_fd) ──→ │
│                                                    │   │
│  stdout ←── os.read(master_fd) ←── [캡처 로직] ←───┘   │
│                                                        │
│  문제: 자식의 "현재 입력 버퍼"를 직접 읽을 방법 없음      │
│  해결: readline kill-ring 트릭 (Ctrl+U/Y)              │
│  한계: 자식이 readline을 쓴다는 가정에 의존              │
└──────────────────────────────────────────────────────┘
         PTY (pseudo-terminal)
┌──────────────────────────────────────────────────────┐
│              자식 프로세스 (claude, opencode)           │
│                                                        │
│  prompt_toolkit 기반 → readline과 다른 동작 가능        │
│  - Ctrl+U: 줄 삭제는 되지만 kill-ring 동작이 다를 수 있음│
│  - Up arrow: 히스토리 탐색 (멀티라인 이동 아님)          │
│  - 자체 ANSI 렌더링 → 캡처 시 혼입                     │
└──────────────────────────────────────────────────────┘
```

### 현재 접근의 근본적 취약점 (Oracle 분석 통합)

> *"You are reading terminal repaint bytes and treating them as authoritative buffer contents. In rich TUIs, repaint may include prompts, history, completions, diffed screen regions, or whole-screen redraws."*

1. **카테고리 혼동(Category Confusion)**: 터미널 리페인트 바이트를 버퍼 내용으로 취급하지만, 리페인트에는 프롬프트, 히스토리, 자동완성, 화면 전체 재그리기가 포함될 수 있음
2. **파괴적 캡처(Destructive Capture)**: Ctrl+U는 실제로 자식 앱의 상태를 변경함 — kill 버퍼를 덮어쓰고, undo 히스토리를 오염시키며, 중간에 실패하면 사용자 텍스트를 잃음
3. **관측과 개입이 같은 채널**: 캡처도 master_fd로, 주입도 master_fd로 — 자기 출력이 자기 입력에 섞임
4. **타이밍 기반 동기화**: 자식 앱의 응답을 기다리는 유일한 방법이 `sleep()` — 리페인트 타이밍은 CPU 부하, 네트워크 출력, 터미널 크기에 따라 달라짐
5. **자식 앱 행동에 대한 가정**: readline Emacs 바인딩을 전제하지만, prompt_toolkit은 자체 버퍼 객체와 스크린 렌더러를 소유 — Ctrl+U/Y/E는 앱 레벨 바인딩이지 터미널 프리미티브가 아님

### prompt_toolkit이 readline과 다른 점 (Oracle 확인)

| 항목 | readline | prompt_toolkit |
|---|---|---|
| Ctrl+U | kill-ring에 저장 → Ctrl+Y로 복원 가능 | 앱 레벨 바인딩, 모드(emacs/vi)에 따라 동작 다름 |
| Ctrl+Y | kill-ring에서 yank → stdout에 출력됨 | 앱 내부 버퍼 조작, stdout 출력은 리페인트의 부산물 |
| Up arrow | 히스토리 탐색 | 히스토리 탐색 (멀티라인 내 이동 아님) |
| 화면 출력 | 줄 에코 | 전체 화면 diff 기반 리페인트 |

### 추가 PTY 엣지케이스 (Oracle)

- **UTF-8 멀티바이트 분할**: `_read_with_timeout`이 UTF-8 시퀀스 중간에서 잘릴 수 있음
- **소프트 랩 vs 실제 개행**: 화면에서 여러 줄로 보여도 논리적으로 한 줄일 수 있음
- **ANSI 이스케이프 단편화**: 불완전한 이스케이프 시퀀스를 strip하면 텍스트가 손상됨
- **대체 스크린 버퍼**: 자식 앱이 alternate screen 사용 시 캡처 자체가 무의미
- **termios 변경**: 자식 앱이 터미널 설정을 변경하면 제어 바이트 해석이 달라짐

---

## 아키텍처 개선 방향 (Oracle 권장)

### 올바른 접근: "추론"에서 "소유"로 전환

현재: 자식 앱의 화면 출력을 읽고 → 내용을 *추론*
개선: 사용자 키 입력을 가로채서 → 프록시 측에서 입력을 직접 *소유*

```
현재 (추론 기반):
  User → Proxy → Child → [화면 출력] → Proxy가 읽고 추론
                                         ↑ 불확실, 비결정적

개선 (소유 기반):
  User → Proxy [Shadow Buffer] → Child
           ↑ 사용자 입력을 직접 추적
           ↓ 번역 결과를 Bracketed Paste로 주입
```

### 구체적 개선안

1. **Shadow Buffer를 입력의 소스 오브 트루스(source of truth)로 사용**: 사용자 키스트로크를 프록시에서 추적해서 현재 입력을 항상 알고 있기 → Ctrl+U/Y 캡처 제거
2. **Bracketed Paste로 주입**: `os.write(master_fd, b"\x1b[200~" + result + b"\x1b[201~")` — 앱이 개별 키스트로크가 아닌 붙여넣기로 처리하므로 자동완성/괄호매칭이 트리거되지 않음
3. **모드 감지**: 자동완성/검색/히스토리/메뉴 모드가 활성화되면 번역을 거부
4. **멀티라인은 Shadow Buffer에서 해결**: Up arrow 탐색 대신 프록시가 가진 버퍼에서 전체 텍스트를 가져옴
5. **Undo를 프록시 로컬로 처리**: 자식 앱에 에디터 명령을 보내지 않고, 프록시 측에서 버퍼를 교체

---

## 권장 우선순위

### 즉시 수정 (안정화)

| 순위 | 이슈 | 조치 |
|---|---|---|
| 1 | C-1 Ctrl+T T 히스토리 캡처 | **Ctrl+T T 비활성화**. 현재 Ctrl+T L (싱글라인)만 작동하도록 제한. 멀티라인은 Shadow Buffer 재설계 후 재활성화 |
| 2 | H-2 개행 = Enter | 번역 결과 주입 시 **Bracketed Paste** 사용: `\x1b[200~` + result + `\x1b[201~` |
| 3 | H-4 Ctrl+Z 충돌 | chord 방식으로 변경 (Ctrl+T U = undo) 또는 별도 핫키 |
| 4 | M-4 데이터 삼킴 | Ctrl+T 바이트만 추출, 나머지 바이트는 자식에 전달 |
| 5 | L-1 .env gitignore | `.gitignore`에 `.env` 추가 |

### 중기 개선 (아키텍처)

| 순위 | 이슈 | 조치 |
|---|---|---|
| 6 | C-2, C-3 타이밍/혼입 | **Shadow Buffer를 source of truth로 전환** — Ctrl+U/Y 캡처 제거, 사용자 키스트로크 직접 추적 |
| 7 | H-1 자동완성 간섭 | Bracketed Paste 주입으로 일괄 해결 |
| 8 | H-3 멀티라인 undo | Undo를 프록시 로컬로 처리 (자식에 에디터 명령 보내지 않음) |
| 9 | H-5 TUI 레이아웃 파괴 | 표시 메커니즘을 터미널 타이틀 또는 별도 상태줄로 변경 |
| 10 | M-1, M-2 chord 피드백 | chord 모드 진입 시 시각적 힌트 표시 |

### 장기 고려 (근본적 전환)

Ctrl+U/Y 기반 캡처를 Shadow Buffer 기반으로 완전히 전환하면 C-2, C-3, H-1, H-3, H-5가 동시에 해결됨. 이것이 Oracle이 권장하는 **"추론에서 소유로"** 전환의 핵심.
