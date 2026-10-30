# Architecture

~~~text
合法持有的书籍正文
 -> prepare-book -> 本地私有索引（原文分块、章节、位置、hash）
 -> extract-stories -> 源证据锚点 + 故事候选卡（可选模型）
 -> 人工审核证据及历史真实性
 -> make-episode -> 6镜头脚本、SRT、提示词、旁白
 -> 外部生图/录音（当前为人工接入）
 -> render -> FFmpeg MP4
~~~

- Novel Radar 继续负责番茄/长读合法采集、正文完整性判定、Story Engine 和 Pattern Library。
- Cangjie Skill 负责可验证的知识蒸馏，上游工具不复制进本仓库。
- Book Story Factory 负责视频化，不建第二套爬虫或生产 Supabase。
- 仅在书籍实际包含相关证据时才输出故事候选；短来源锚点不等于历史事实已验证。
- 调用模型时，选定书籍分块会传给配置的第三方 API 服务商，需评估版权与数据处理许可。
- 当前 make-episode 为初稿模板，字幕按镜头定时，不是逐词精准对齐；发布前需要润色、校验与试听。
