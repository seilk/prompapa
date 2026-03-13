<p align="center">
  <img src="assets/prompapa-banner.png" alt="prompapa" width="800" />
</p>

<p align="center">
  <em>母国語で入力して、<code>Ctrl+T</code>を押すだけ。<strong>Claude Code</strong>で完璧な英語に変わります。</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/install-uv-blueviolet" alt="uv" />
  <img src="https://img.shields.io/badge/translation-Google_Cloud-green" alt="Google Cloud Translation" />
</p>

<p align="center">
  <a href="README.md">English</a> · <a href="README.ko.md">한국어</a> · <a href="README.ja.md">日本語</a> · <a href="README.zh.md">中文</a> · <a href="README.fr.md">Français</a> · <a href="README.es.md">Español</a> · <a href="README.de.md">Deutsch</a> · <a href="README.ru.md">Русский</a>
</p>

## デモ

<table>
  <tr>
    <td align="center">
      <img src="assets/prompapa-demo-ko.gif" width="600" />
      <br/>🇰🇷 韓国語
    </td>
    <td align="center">
      <img src="assets/prompapa-demo-jp.gif" width="600" />
      <br/>🇯🇵 日本語
    </td>
    <td align="center">
      <img src="assets/prompapa-demo-cn.gif" width="600" />
      <br/>🇨🇳 中国語
    </td>
  </tr>
  <tr>
    <td align="center">
      <img src="assets/prompapa-demo-fr.gif" width="600" />
      <br/>🇫🇷 フランス語
    </td>
    <td align="center">
      <img src="assets/prompapa-demo-es.gif" width="600" />
      <br/>🇪🇸 スペイン語
    </td>
    <td align="center">
      <img src="assets/prompapa-demo-de.gif" width="600" />
      <br/>🇩🇪 ドイツ語
    </td>
  </tr>
</table>

<p align="center"><em><strong><em>あらゆる言語</em>で入力できます。<code>Ctrl+T</code>で英語に翻訳、<code>Ctrl+Y</code>で元に戻す。</strong></em></p>

## なぜ作ったのか

言語は思考を入れる中立な容器ではありません。最初に浮かぶ言葉、意味を理解する前に課す構造、言語化に先立つ本能。これらはすべて母国語に深く根ざしています。そのプロセスを第二言語に強制すると、単に遅くなるだけではありません。思考そのものが静かに変形されます。

AIコーディングアシスタントは反対の方向から類似した制約を持っています。研究によると、これらのモデルは構造的な英語バイアスを示し、非英語言語で表現された同じ意図は測定可能なほど弱い応答を生み出します [[1]](https://arxiv.org/abs/2504.11833)。このバイアスは表面的な語彙を超えて深く根付いています。大型推論モデルの表現分析では、訓練データだけでなく、アーキテクチャ的に内部推論経路が英語中心であることが示されています。プロンプトがどの言語で入力されても、モデルは推論を開始する前に英語中心の潜在空間に収束します [[2]](https://arxiv.org/abs/2601.02996)。言語表現と推論基盤を分離すると同じパターンが明らかになります — 提示された言語レイヤーが英語のとき、推論エンジンの性能が最も高くなります [[3]](https://arxiv.org/abs/2505.15257)。その結果は理論にとどまりません。11言語と4つのタスク領域にわたって、非英語プロンプトは性能と堅牢性の両方で一貫した低下を示します [[4]](https://arxiv.org/abs/2505.15935)。

目的がすれ違う二つの心。一方は母国語で考えるときが最も明確。もう一方は英語で推論するときが最も優れています。

Prompapaはその間に立っています。それだけです。

### 参考文献

1. Gao et al. (2025). *Could Thinking Multilingually Empower LLM Reasoning?* arXiv:2504.11833
2. Liu et al. (2026). *Large Reasoning Models Are (Not Yet) Multilingual Latent Reasoners.* arXiv:2601.02996
3. Zhao et al. (2025). *When Less Language is More: Language-Reasoning Disentanglement Makes LLMs Better Multilingual Reasoners.* NeurIPS 2025. arXiv:2505.15257
4. Hofman et al. (2025). *MAPS: A Multilingual Benchmark for Agent Performance and Security.* EACL 2026. arXiv:2505.15935

## インストール

[uv](https://docs.astral.sh/uv/)が必要です。一度インストールしたら:

```bash
uv tool install git+https://github.com/seilk/prompapa
```

## セットアップ

オンボーディングウィザードでAPIキーを設定します:

```bash
papa onboard
```

`~/.config/prompapa/config.toml`にGoogle Cloud Translation APIキーが保存されます。

キーをお持ちでない方も、ウィザードが取得方法を案内します。

## 使い方

```bash
papa claude
```

ツールは通常通りに起動します。新しいホットキーが2つ追加されます:

| ホットキー | 動作 |
|--------|--------|
| `Ctrl+T` | 現在の入力を英語に翻訳 |
| `Ctrl+Y` | 翻訳を取り消し、原文を復元 |

## 設定

`~/.config/prompapa/config.toml`:

```toml
provider = "google"
api_key = "your-gcp-translation-api-key"
target_cmd = ["claude"]
preserve_backticks = true
```

環境変数でキーを管理したい場合は`api_key_env`も使えます:

```toml
provider = "google"
api_key_env = "GOOGLE_API_KEY"
target_cmd = ["claude"]
```

### preserve_backticks

バッククォートで囲まれたトークンを翻訳せずに保持します:

```toml
preserve_backticks = true
```

`` `src/auth.ts` ``は翻訳後もそのまま維持されます。

## 仕組み

Prompapaは対象CLIを**PTY（疑似端末）**としてフォークし、キーボードとプロセスの間に透過的に位置します。すべてのキー入力は変更なく通過します。`Ctrl+T`を押すまでは。

その時点で:

1. `pyte`スクリーントラッカーで現在の入力を端末画面から読み取ります
2. Google Cloud Translation APIへの非同期呼び出しを実行します
3. 正確に計算されたバックスペースで原文を消去します（画面の再描画なし）
4. ブラケットペーストで英語の結果を注入します

子プロセスは一時停止しません。UIは再描画されません。テキストがただ... 変わります。

## 開発

```bash
git clone https://github.com/seilk/prompapa
cd prompapa
uv sync
uv run pytest -v
```

インストールなしでローカル実行:

```bash
uv run papa claude
```

## アップデート

```bash
papa update
```

GitHubから最新バージョンを取得して再インストールします。

## アンインストール

```bash
papa uninstall
```

`~/.config/prompapa/`の設定ファイルは保持されます。必要であれば手動で削除してください。

## TODO
- [ ] `opencode` サポート
- [ ] LLM API 翻訳サポート (OpenAI, Gemini, Claude, ...)
- [ ] 翻訳先言語の選択と多様化 (現在は英語固定)
