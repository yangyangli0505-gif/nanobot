# 这个 fork 到底改了什么（中文说明）

这份文档是给 **直接看我这个 fork 的人** 准备的。

因为原版 nanobot 的 README 很长，而且主要是英文介绍上游项目。  
如果只看首页，很容易看不出来：**这个 fork 到底改了什么、是不是只是改了几个配置、和上游 nanobot 到底是什么关系。**

所以这里用最直白的话讲清楚。

---

# 一句话先说清楚

**上游 nanobot 是一个通用的 agent runtime。**  
**我这个 fork 在它上面接入了一个 AI Tech Intelligence 应用层。**

也就是说：

- 上游 nanobot 提供：agent loop、tools、commands、cron、channels、gateway
- 我这个 fork 新增：AI 科技情报抓取、分类、排序、日报/午报生成、定时推送

所以这次二开不是：

- 重写 nanobot
- 另起炉灶重新造一个 agent 框架
- 改 provider / channel / memory 的全部底层

而是：

> **利用 nanobot 已有的大框架，把一个外部 AI 资讯/情报 pipeline 接成了 nanobot 内建能力。**

---

# 为什么一开始会让人觉得“没改到 nanobot”

一开始确实有这个问题。

最早的 AI intelligence 项目，更像是：

- 一个独立 Python pipeline
- 在外面跑 ingestion / dedup / ranking / report generation
- 再借助 runtime 去定时和推送

这种状态下，你完全可以说：

> “这和 nanobot 的关系太弱，nanobot 的大框架根本没真正用上。”

这个质疑是对的。

后面这次真正做的事情，就是把这层关系补实。

---

# 这次二开，代码层面到底加了什么

## 1. 新增一个内建模块：`nanobot/ai_intel/`

这是这次二开的核心。

新增了一个 AI intelligence 模块，里面包括：

- `models.py`
- `source_registry.py`
- `adapters_base.py`
- `rss_adapter.py`
- `dedup.py`
- `topic_classifier.py`
- `signal_ranker.py`
- `change_detection.py`
- `report_generator.py`
- `llm_enricher.py`
- `ingest.py`
- `sources.json`

它负责的事情包括：

- 抓取 AI 信息源
- 去重
- 主题分类
- 信号排序
- 快照变化检测
- 生成日报 / 午报
- 可选 LLM enrich

也就是说，**AI intelligence 的业务逻辑现在已经不是 nanobot 外面的独立脚本，而是 nanobot repo 内的正式模块。**

---

## 2. 新增一个内建 tool：`ai_intel`

新增了：

- `nanobot/agent/tools/ai_intel.py`

并且把它注册进了 nanobot 的 tool registry。

这个 tool 现在支持：

- `daily_brief`
- `midday_recap`
- `refresh`

这一步很关键，因为它意味着：

> **AI intelligence 能力已经变成 nanobot agent 可以直接调用的内部工具。**

而不是单纯外部脚本。

---

## 3. 新增命令入口

现在这个 fork 里已经有：

- `/intel-daily`
- `/intel-recap`
- `/intel-refresh`
- `/intel-schedule-daily`
- `/intel-schedule-midday`

这意味着两种使用方式都成立：

### 手动模式
你可以在 CLI 或聊天里手动调用：
- `/intel-daily`
- `/intel-recap`
- `/intel-refresh`

### 定时模式
你也可以让 nanobot 自动创建：
- 日报任务
- 午报任务

---

## 4. 新增配置块：`tools.aiIntel.*`

我还把它接进了 nanobot 的配置系统。

现在配置里可以写：

- `tools.aiIntel.enabled`
- `tools.aiIntel.stateDir`
- `tools.aiIntel.sourcesPath`
- `tools.aiIntel.channel`
- `tools.aiIntel.chatId`
- `tools.aiIntel.daily.enabled`
- `tools.aiIntel.daily.cron`
- `tools.aiIntel.midday.enabled`
- `tools.aiIntel.midday.cron`

这一步的意义是：

> **这已经不是“仓库里塞了点代码”，而是 nanobot 里一个正式可配置能力。**

---

## 5. 接入 nanobot runtime state

这次还做了状态层的接入：

- AI intel snapshot 不再放在源码旁边
- 改成走 nanobot runtime state 目录

这说明它已经开始遵守 nanobot 的运行时结构，而不是自己乱落文件。

---

## 6. 接入 cron

这一步是把关系真正补实的关键。

现在有两层 cron 集成：

### 第一层：手动命令创建 cron
- `/intel-schedule-daily`
- `/intel-schedule-midday`

### 第二层：gateway 启动自动注册
只要配置里开了：
- `tools.aiIntel.daily.enabled = true`
- `tools.aiIntel.midday.enabled = true`

并给出投递目标：
- `channel`
- `chatId`

那么 `nanobot gateway` 启动时就会自动注册：

- `ai-intel-daily`
- `ai-intel-midday`

这时候它就已经不是“手动脚本”，而是：

> **nanobot 内部长期运行、自动定时、自动推送的能力。**

---

## 7. 接入 channel 投递

如果配置了像 Telegram 这样的 channel，  
这个 fork 现在已经可以：

- 到点跑 intelligence pipeline
- 生成日报 / 午报
- 通过 nanobot channel 发到目标 chat_id

这点非常重要，因为这说明：

> 它不是只会在终端里打印，而是真正进入了 nanobot 的 delivery 链路。

---

# 所以这次二开到底算什么？

我建议最准确的说法是：

> **这不是改 nanobot 内核的“重度框架改造”，而是把一个 AI Tech Intelligence 应用真正接成了 nanobot 内建能力。**

换句话说：

## 上游 nanobot
更像：
- 通用 runtime
- agent 平台
- 基础设施

## 这个 fork
更像：
- 基于 runtime 接入了一个 AI intelligence app
- 让 nanobot 多了一个可调用、可配置、可定时、可推送的垂直能力

---

# 它和“只是外部脚本”有什么区别？

区别就在于现在已经真的用上了这些 nanobot 骨架：

- tool registry
- agent loop
- command router
- config schema
- runtime state dir
- cron system jobs
- gateway startup lifecycle
- channel delivery
- focused tests

所以现在已经不应该再说它只是：
- “外面单独跑个脚本”
- “和 nanobot 没关系”

因为这几个核心入口都接上了。

---

# 现在这个 fork 应该怎么用？

## 1. 手动调试 / CLI 使用

启动：

```bash
nanobot agent
```

然后在会话里用：

- `/intel-daily`
- `/intel-recap`
- `/intel-refresh`

适合：
- 调试
- 看报告效果
- 验证排序和输出质量

---

## 2. 长期运行 / 自动推送

启动：

```bash
nanobot gateway
```

如果你已经在配置里填好：

- Telegram bot token
- `tools.aiIntel.channel`
- `tools.aiIntel.chatId`
- `daily.cron`
- `midday.cron`

那么 gateway 启动时会自动注册：

- `ai-intel-daily`
- `ai-intel-midday`

然后到时间自动给你发。

---

# 现在这个 fork 的成熟度怎么判断？

## 已经做成的
- 代码模块并入 nanobot
- tool 接入
- command 接入
- config 接入
- cron 接入
- 自动注册接入
- channel 投递链路接入
- focused tests 验证

## 还可以继续优化的
- 更细的 watchlist 配置
- 更丰富的 topic/company tracking
- 更完整的 cron 生命周期管理
- 报告展示和交付格式继续抛光

所以它现在不是“玩具”，但也还不是最终产品终态。

---

# 一句话总结

**上游 nanobot 提供的是通用 agent runtime；我这个 fork 的二次开发，做的是把一个 AI Tech Intelligence pipeline 真正接成 nanobot 内建的、可调用、可配置、可定时、可推送的垂直能力。**
