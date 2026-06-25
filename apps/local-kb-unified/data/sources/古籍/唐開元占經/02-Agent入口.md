# Agent 入口

> 这是《唐開元占經》知识库的 Agent 使用导航页。

## 一、目标
这套 Agent 不是泛泛谈玄，而是：
- 优先依据《唐開元占經》原文回答
- 在必要时给出现代中文解释
- 能指出对应分卷、术语卡、主题索引
- 不把后世流行说法强行说成书中原意

## 二、推荐工作流

### 1. 问答模式
适合：
- 问术语
- 问卷目
- 问专题
- 问原文大意

入口：
- [[agent/prompts/qa-prompt]]
- [[agent/prompts/mansion_qa_prompt]]
- [[agent/prompts/xingguan_qa_prompt]]

辅助资料：
- `术语卡片/`
- `主题索引/`
- `逐宿卡/`
- `星官卡/`
- `分卷/`

### 2. 抽取模式
适合：
- 从原文片段抽术语
- 抽概念关系
- 抽专题知识卡

入口：
- [[agent/prompts/extraction-prompt]]
- `agent/extract/prompts/extract_to_card`
- `agent/extract/prompts/merge_cards`
- `agent/schema.yaml`
- `agent/extract/schema/knowledge_card.schema.yaml`

输出位置建议：
- `知识抽取卡/`

### 3. 专题总结模式
适合：
- 对某一主题做现代中文综述
- 汇总多个分卷的信息
- 形成可读的专题总结

入口：
- [[agent/prompts/thematic-summary-prompt]]

输入来源建议：
- `主题索引/`
- `章节摘要卡/`
- `知识抽取卡/`

## 三、推荐路由规则

### 问“概念是什么”
优先路由到：
1. `术语卡片/`
2. `知识抽取卡/`
3. `分卷/`

### 问“某主题在哪些卷”
优先路由到：
1. `主题索引/`
2. `导航/主题总览`
3. `章节摘要卡/`
4. `分卷/`

### 问“某宿/某星官”
优先路由到：
1. `逐宿卡/` 或 `星官卡/`
2. 专门 prompt
3. `分卷/`

### 问“请引用原文”
优先路由到：
1. `分卷/`
2. `唐開元占經-全文合併版.md`

## 四、建议的回答格式

### 标准问答格式
1. 结论
2. 原文依据
3. 白话解释
4. 相关术语 / 相关主题
5. 对应文件位置

### 专题总结格式
1. 主题概述
2. 涉及分卷
3. 核心术语
4. 关键摘录
5. 白话总结
6. 待考问题

## 五、先用这批题做测试
- 什么是渾天？
- 黄道与赤道有何关系？
- 卷一主要讲什么？
- 二十八宿内容集中在哪几卷？
- 客星、彗星、妖星有何不同？
- 紫微、太微、天市在这套库里去哪里看？

相关文件：
- `问答样例库/基础天文与术语问答`
- `问答样例库/星变与占象问答`
- `问答样例库/卷目结构与导航问答`
- `问答样例库/主题路由测试集`

## 六、评测入口
- `agent/eval/qa_eval_dataset.jsonl`
- `agent/eval/router_eval_dataset.yaml`

建议：
- 每次补完一批新卡片，就跑一次路由测试。
- 每次调整 prompt，就至少用 10 个固定问题回归测试。

## 七、当前推荐默认配置

### 默认问答 prompt
- [[agent/prompts/qa-prompt]]

### 宿类专门问答
- [[agent/prompts/mansion_qa_prompt]]

### 星官专门问答
- [[agent/prompts/xingguan_qa_prompt]]

### 抽取 prompt
- [[agent/prompts/extraction-prompt]]

### 专题总结 prompt
- [[agent/prompts/thematic-summary-prompt]]

## 八、后续可继续扩展
- 加一个“引用原文优先”的严格模式 prompt
- 加一个“只做结构定位，不做解释”的路由模式 prompt
- 加一个“现代中文导读”模式 prompt
