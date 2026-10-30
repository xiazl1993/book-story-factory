# book-story-factory

书籍蒸馏 + 历史故事插画短视频工具（MVP v0.1）。

目前支持：TXT/MD/EPUB/文字型 PDF 生成可追溯文本索引；利用 OpenAI-compatible API 按分块提取有证据的故事候选；由故事 JSON 生成六镜头旁白、插画提示词和字幕；用本地插画和可选配音通过 FFmpeg 合成竖屏视频。

当前不自动生成插画或语音；Cangjie Skill 的全自动接入尚未完成，优先保留稳定的上游 JSON/YAML 适配边界。不声称已经读取《胜天半子》正文。

## 快速使用

前置：Python 3.11+，合成阶段需要 FFmpeg。

~~~bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
book-story prepare-book books/raw/my-book.txt --out outputs/my-book/index.json
book-story make-episode examples/story.demo.json --out outputs/demo
python -m unittest discover -s tests -v
~~~

需要解析文字型 PDF 时安装可选依赖：

~~~bash
pip install -e '.[pdf]'
~~~

自动提取故事候选需要配置你自己的兼容 API，默认仅运行前三个分块，避免模型费用失控：

~~~bash
export OPENAI_COMPAT_API_KEY='YOUR_KEY'
export OPENAI_COMPAT_MODEL='YOUR_MODEL'
export OPENAI_COMPAT_BASE_URL='https://your-provider.example/v1'
book-story extract-stories outputs/my-book/index.json --out outputs/my-book/stories.json --max-chunks 3
book-story pick-story outputs/my-book/stories.json --number 1 --out outputs/my-book/story-001.json
book-story make-episode outputs/my-book/story-001.json --out outputs/episode-001
~~~

准备好 outputs/demo/images/01.png ~ 06.png（或 JPG / WEBP）之后：

~~~bash
book-story render outputs/demo --out outputs/demo/final.mp4
book-story render outputs/demo --audio outputs/demo/audio/voiceover.mp3 --out outputs/demo/final.mp4
~~~

SRT 字幕可直接导入剪映；当前视频默认不烧录字幕。这里的 demo 是原创虚构故事，不是《胜天半子》的内容。

## 安全边界

- 当前仓库是 Public。版权书籍正文和抽取结果只能保存在被忽略的 books/raw、outputs 等私有目录；不得提交 API Key。
- 只处理公开或获授权的文本，不绕过任何付费、DRM、登录或签名保护。
- 文本的出处可核验不等于历史事实已经核验。公开发布之前需要审核历史事实、文案原创性与版权。
- Novel Radar 负责小说采集和 Story Engine，本项目负责内容视频化，不建立第二套采集器或生产数据库。

参见 docs/ARCHITECTURE.md 和 docs/CANGJIE.md。
