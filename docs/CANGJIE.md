# Cangjie adapter plan

上游项目：https://github.com/kangarooking/cangjie-skill

Cangjie Skill v2.5 的主要能力包括全书结构分析、案例提取、三重验证、方法卡生成和压力测试。

当前版本尚未自动调用仓颉的 Skill runtime。未来适配时优先消费其稳定 JSON/YAML 案例卡，并映射到本项目的 story JSON：

- title、protagonist、setting、conflict、decision、outcome、insight；
- source.type、source.book_filename、source.chapter、source.chunk_id 和短证据锚点；
- source_checked 必须区别来源存在与历史事实真实性，不可仅凭原文锚点置为 true。

仓颉适合知识和方法论蒸馏，但不是专用小说 Scene/Beat 引擎。Novel Radar 已有的 novel_text_analyses 应直接保留并复用，不能重复采集或复制受版权保护的原始小说内容到公开仓库。
