<p align="center">
  <img src="assets/prompapa-banner.png" alt="prompapa" width="800" />
</p>

<p align="center">
  <em>用你的母语输入，在 <strong>Claude Code</strong> 中按下 <code>Ctrl+T</code>，看它变成完美的英语。</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/install-uv-blueviolet" alt="uv" />
  <img src="https://img.shields.io/badge/translation-Google_Cloud-green" alt="Google Cloud Translation" />
</p>

<p align="center">
  <a href="README.md">English</a> · <a href="README.ko.md">한국어</a> · <a href="README.ja.md">日本語</a> · <a href="README.zh.md">中文</a> · <a href="README.fr.md">Français</a> · <a href="README.es.md">Español</a> · <a href="README.de.md">Deutsch</a> · <a href="README.ru.md">Русский</a>
</p>

## 演示

<table>
  <tr>
    <td align="center">
      <img src="assets/prompapa-demo-ko.gif" width="600" />
      <br/>🇰🇷 韩语
    </td>
    <td align="center">
      <img src="assets/prompapa-demo-jp.gif" width="600" />
      <br/>🇯🇵 日语
    </td>
    <td align="center">
      <img src="assets/prompapa-demo-cn.gif" width="600" />
      <br/>🇨🇳 中文
    </td>
  </tr>
  <tr>
    <td align="center">
      <img src="assets/prompapa-demo-fr.gif" width="600" />
      <br/>🇫🇷 法语
    </td>
    <td align="center">
      <img src="assets/prompapa-demo-es.gif" width="600" />
      <br/>🇪🇸 西班牙语
    </td>
    <td align="center">
      <img src="assets/prompapa-demo-de.gif" width="600" />
      <br/>🇩🇪 德语
    </td>
  </tr>
</table>

<p align="center"><em><strong>支持<em>任意语言</em>。按 <code>Ctrl+T</code> 翻译成英语，按 <code>Ctrl+Y</code> 撤销。</strong></em></p>

## 为什么要做这个

语言不是容纳思想的中性容器。我们最先想到的词语、在理解意思之前就施加的结构、先于语言化的本能，这些都深深扎根于母语之中。强迫这个过程经由第二语言，不仅仅是让它变慢。它会悄然地重塑思维本身。

AI 编程助手从相反的方向承受着类似的约束。研究证实了许多人的直觉：这些模型表现出结构性的英语偏差，用非英语语言表达相同意图会产生明显更弱的响应 [[1]](https://arxiv.org/abs/2504.11833)。这种偏差深入到表面词汇之下。对大型推论模型的表征分析表明，其内部推理路径在架构上以英语为中心，而不仅仅是训练数据的问题。无论提示以何种语言输入，模型都会在开始推理之前收敛到以英语为形态的潜在空间 [[2]](https://arxiv.org/abs/2601.02996)。将语言表征与推理基底分离揭示了同样的规律：当呈现给推理引擎的语言层是英语时，性能最佳 [[3]](https://arxiv.org/abs/2505.15257)。这一结果并非理论层面。在十一种语言和四个任务领域中，非英语提示在性能和鲁棒性上都表现出一致的下降 [[4]](https://arxiv.org/abs/2505.15935)。

两种心智，目的相悖。一个在母语中思考时最为清晰。一个在英语中推理时最为出色。

Prompapa 站在它们之间。仅此而已。

### 参考文献

1. Gao et al. (2025). *Could Thinking Multilingually Empower LLM Reasoning?* arXiv:2504.11833
2. Liu et al. (2026). *Large Reasoning Models Are (Not Yet) Multilingual Latent Reasoners.* arXiv:2601.02996
3. Zhao et al. (2025). *When Less Language is More: Language-Reasoning Disentanglement Makes LLMs Better Multilingual Reasoners.* NeurIPS 2025. arXiv:2505.15257
4. Hofman et al. (2025). *MAPS: A Multilingual Benchmark for Agent Performance and Security.* EACL 2026. arXiv:2505.15935

## 安装

需要 [uv](https://docs.astral.sh/uv/)。安装一次后：

```bash
uv tool install git+https://github.com/seilk/prompapa
```

## 设置

运行引导向导配置 API 密钥：

```bash
papa onboard
```

这会将你的 Google Cloud Translation API 密钥保存到 `~/.config/prompapa/config.toml`。

还没有密钥？向导会引导你完成获取流程。

## 使用方法

```bash
papa claude
```

工具完全按照正常方式启动。新增两个快捷键：

| 快捷键 | 操作 |
|--------|--------|
| `Ctrl+T` | 将当前输入翻译成英语 |
| `Ctrl+Y` | 撤销翻译，恢复原文 |

## 配置

`~/.config/prompapa/config.toml`：

```toml
provider = "google"
api_key = "your-gcp-translation-api-key"
target_cmd = ["claude"]
preserve_backticks = true
```

如果你更喜欢通过环境变量管理密钥，也支持 `api_key_env`：

```toml
provider = "google"
api_key_env = "GOOGLE_API_KEY"
target_cmd = ["claude"]
```

### preserve_backticks

保持反引号包裹的标记不被翻译：

```toml
preserve_backticks = true
```

`` `src/auth.ts` `` 在翻译后保持原样。

## 工作原理

Prompapa 将目标 CLI 以 **PTY（伪终端）** 方式分叉，透明地坐落在你的键盘和进程之间。每个按键都原样传递，直到你按下 `Ctrl+T`。

此时：

1. 通过 `pyte` 屏幕追踪器从终端屏幕读取当前输入
2. 向 Google Cloud Translation API 发起异步调用
3. 用精确计算的退格键擦除原文（无屏幕刷新）
4. 通过括号粘贴注入英语结果

子进程从不暂停。UI 从不重绘。文字就这样……变了。

## 开发

```bash
git clone https://github.com/seilk/prompapa
cd prompapa
uv sync
uv run pytest -v
```

不安装直接本地运行：

```bash
uv run papa claude
```

## 更新

```bash
papa update
```

从 GitHub 拉取并重新安装最新版本。

## 卸载

```bash
papa uninstall
```

`~/.config/prompapa/` 中的配置文件会被保留。如有需要，请手动删除。

## TODO
- [ ] `opencode` 支持
- [ ] LLM API 翻译支持 (OpenAI, Gemini, Claude, ...)
- [ ] 可配置的目标（目的地）语言，不局限于英语
