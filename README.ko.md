<p align="center">
  <img src="assets/prompapa-banner.png" alt="prompapa" width="800" />
</p>

<p align="center">
  <em>모국어로 입력하세요. <code>Ctrl+]</code>를 누르면 <strong>Claude Code / Codex / Opencode</strong>에서 완벽한 영어로 바뀝니다.</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/install-uv-blueviolet" alt="uv" />
  <img src="https://img.shields.io/badge/translation-Google_Cloud-green" alt="Google Cloud Translation" />
</p>

<p align="center">
  <a href="README.md">English</a> · <a href="README.ko.md">한국어</a> · <a href="README.ja.md">日本語</a> · <a href="README.zh.md">中文</a> · <a href="README.fr.md">Français</a> · <a href="README.es.md">Español</a> · <a href="README.de.md">Deutsch</a> · <a href="README.ru.md">Русский</a>
</p>

## 데모

<table>
  <tr>
    <td align="center">
      <img src="assets/prompapa-demo-ko.gif" width="600" />
      <br/>🇰🇷 한국어
    </td>
    <td align="center">
      <img src="assets/prompapa-demo-jp.gif" width="600" />
      <br/>🇯🇵 일본어
    </td>
    <td align="center">
      <img src="assets/prompapa-demo-cn.gif" width="600" />
      <br/>🇨🇳 중국어
    </td>
  </tr>
  <tr>
    <td align="center">
      <img src="assets/prompapa-demo-fr.gif" width="600" />
      <br/>🇫🇷 프랑스어
    </td>
    <td align="center">
      <img src="assets/prompapa-demo-es.gif" width="600" />
      <br/>🇪🇸 스페인어
    </td>
    <td align="center">
      <img src="assets/prompapa-demo-de.gif" width="600" />
      <br/>🇩🇪 독일어
    </td>
  </tr>
</table>

<p align="center"><em><strong><em>어떤 언어든</em> 입력하세요. <code>Ctrl+]</code>로 영어로 번역, <code>Ctrl+Q</code>로 되돌리기.</strong></em></p>

## 왜 만들었는가

언어는 사고를 담는 중립적인 그릇이 아닙니다. 우리가 가장 먼저 떠올리는 단어, 의미를 깨닫기도 전에 부과하는 구조, 언어화에 앞서는 본능. 이것들은 모두 모국어에 깊이 새겨져 있습니다. 그 과정을 제2외국어로 강제하면 단순히 느려지는 게 아닙니다. 사고 자체가 조용히 왜곡됩니다.

AI 코딩 어시스턴트는 반대 방향에서 유사한 제약을 지닙니다. 연구에 따르면 이 모델들은 구조적 영어 편향을 보이며, 비영어 언어로 표현된 동일한 의도는 측정 가능한 수준으로 더 약한 응답을 낳습니다 [[1]](https://arxiv.org/abs/2504.11833). 이 편향은 표면적인 어휘를 넘어 깊이 뿌리내려 있습니다. 대형 추론 모델에 대한 표현 분석은, 내부 추론 경로가 훈련 데이터만이 아니라 아키텍처적으로 영어 중심임을 보여줍니다. 프롬프트가 어떤 언어로 입력되든, 모델은 추론을 시작하기 전 영어 중심의 잠재 공간으로 수렴합니다 [[2]](https://arxiv.org/abs/2601.02996). 언어 표현과 추론 기반을 분리하면 동일한 패턴이 드러납니다 — 제시된 언어 레이어가 영어일 때 추론 엔진의 성능이 가장 높습니다 [[3]](https://arxiv.org/abs/2505.15257). 그 결과는 이론에 그치지 않습니다. 11개 언어와 4개 과제 영역에 걸쳐, 비영어 프롬프트는 성능과 견고성 모두에서 일관된 저하를 보입니다 [[4]](https://arxiv.org/abs/2505.15935).

서로 엇갈리는 두 개의 마음. 하나는 모국어로 생각할 때 가장 명확하고. 하나는 영어로 추론할 때 가장 뛰어납니다.

Prompapa는 그 사이에 있습니다. 그것뿐입니다.

### 참고문헌

1. Gao et al. (2025). *Could Thinking Multilingually Empower LLM Reasoning?* [arXiv:2504.11833](https://arxiv.org/abs/2504.11833)
2. Liu et al. (2026). *Large Reasoning Models Are (Not Yet) Multilingual Latent Reasoners.* [arXiv:2601.02996](https://arxiv.org/abs/2601.02996)
3. Zhao et al. (2025). *When Less Language is More: Language-Reasoning Disentanglement Makes LLMs Better Multilingual Reasoners.* NeurIPS 2025. [arXiv:2505.15257](https://arxiv.org/abs/2505.15257)
4. Hofman et al. (2025). *MAPS: A Multilingual Benchmark for Agent Performance and Security.* EACL 2026. [arXiv:2505.15935](https://arxiv.org/abs/2505.15935)

## 설치

[uv](https://docs.astral.sh/uv/)가 필요합니다. 없다면 먼저 설치하세요:

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

그 다음 prompapa를 설치합니다:

```bash
uv tool install git+https://github.com/seilk/prompapa
```

## 설정

온보딩 마법사로 API 키를 설정하세요:

```bash
papa onboard
```

`~/.config/prompapa/config.toml`에 Google Cloud Translation API 키가 저장됩니다.

### Google Cloud Translation API 키 발급

> **무료 한도:** Google Cloud Translation API(Basic)는 **매월 500,000자를 무료**로 제공합니다. 초과 시 100만 자당 $20입니다. 일반적인 AI 프롬프트가 100~300자 수준이므로, 무료 한도 안에서 하루 1,500~5,000건의 번역이 가능합니다.

1. [console.cloud.google.com](https://console.cloud.google.com)에 접속해 로그인합니다.
2. 새 프로젝트를 생성하거나 기존 프로젝트를 선택합니다.
3. **APIs & Services → Library**로 이동해 **Cloud Translation API**를 검색한 후 **사용 설정(Enable)**을 클릭합니다.
4. 결제 수단 등록을 요청합니다. 신용카드 정보가 필요하지만, **무료 한도 내에서는 실제 청구가 발생하지 않습니다.** ([요금 안내](https://cloud.google.com/translate/pricing))
5. **APIs & Services → 사용자 인증 정보(Credentials) → 사용자 인증 정보 만들기 → API 키**를 선택합니다.
6. 생성된 키를 복사해 `papa onboard` 실행 시 입력하면 됩니다.

## 사용법

```bash
papa claude
```

도구가 평소와 똑같이 실행됩니다. 새로운 단축키 두 가지:

| 단축키 | 동작 |
|--------|--------|
| `Ctrl+]` | 현재 입력을 영어로 번역 |
| `Ctrl+Q` | 번역 취소, 원문 복원 |

## 설정 파일

`~/.config/prompapa/config.toml`:

```toml
provider = "google"
api_key = "your-gcp-translation-api-key"
target_cmd = ["claude"]
preserve_backticks = true
```

환경 변수로 키를 관리하고 싶다면 `api_key_env`도 지원합니다:

```toml
provider = "google"
api_key_env = "GOOGLE_API_KEY"
target_cmd = ["claude"]
```

### preserve_backticks

백틱으로 감싼 토큰을 번역하지 않고 유지합니다:

```toml
preserve_backticks = true
```

`` `src/auth.ts` ``는 번역 후에도 그대로 유지됩니다.

## 작동 원리

Prompapa는 대상 CLI를 **PTY(가상 터미널)**로 포크하여, 키보드와 프로세스 사이에 투명하게 위치합니다. 모든 키 입력은 변경 없이 통과합니다. `Ctrl+]`를 누르기 전까지는.

그 시점에:

1. `pyte` 스크린 트래커를 통해 현재 입력을 터미널 화면에서 읽습니다
2. Google Cloud Translation API에 비동기 호출을 실행합니다
3. 정확히 계산된 백스페이스로 원문을 지웁니다 (화면 새로고침 없음)
4. 괄호형 붙여넣기로 영어 결과를 주입합니다

자식 프로세스는 멈추지 않습니다. UI는 다시 그려지지 않습니다. 텍스트가 그냥... 바뀝니다.

## 개발

```bash
git clone https://github.com/seilk/prompapa
cd prompapa
uv sync
uv run pytest -v
```

설치 없이 로컬 실행:

```bash
uv run papa claude
```

## 업데이트

```bash
papa update
```

GitHub에서 최신 버전을 받아 재설치합니다.

## 제거

```bash
papa uninstall
```

`~/.config/prompapa/`의 설정 파일은 보존됩니다. 필요하다면 직접 삭제하세요.

## TODO
- [x] `codex` 및 `opencode` 지원
- [ ] LLM API 번역 지원 (OpenAI, Gemini, Claude, ...)
- [ ] 번역 대상(목적지) 언어 선택 가능하게 다양화 (현재 영어 고정)
