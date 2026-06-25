# Trae SOLO 项目全量归档

> 生成时间：2026-06-22
> 工作目录：d:\TRAE SOLO CN\

---

## 一、项目概览

| 项目 | 路径 | 描述 |
|------|------|------|
| 投资指数资讯 | d:\TRAE SOLO CN\投资指数资讯 | 指数投资每日资讯生成 + 小程序 + Web 前端 |
| 各类测试 | d:\TRAE SOLO CN\各类测试 | 测试沙箱 + portfolio-analysis 持仓分析系统 |
| RAG Demo | d:\TRAE SOLO CN\RAG Demo | RAG 问答 Web 应用 |

---

## 二、Skill 总表

### 全局 Skill（内置目录）

| Skill | 路径 |
|-------|------|
| TRAE-product-knowledge | C:\Users\11328817\.trae-cn\builtin\code\default\skills\TRAE-product-knowledge\SKILL.md |
| web-dev | C:\Users\11328817\.trae-cn\builtin\code\default\skills\web-dev\SKILL.md |

### 项目级 Skill

#### 投资指数资讯（4 个）

```
d:\TRAE SOLO CN\投资指数资讯\.trae\skills\
├── a-stock-data/               SKILL.md + scripts/ + references/
├── full-coverage-test/          SKILL.md + references/
├── guizang-social-card-skill/   SKILL.md + agents/ + assets/ + references/
└── install-software/            SKILL.md
```

#### 各类测试（27 个）

```
d:\TRAE SOLO CN\各类测试\.trae\skills\
├── batch-import-skills/       ← 批量导入 Skill
├── brainstorming/             ← 创意 + 产品方向验证（含 Office Hours 6问）
├── code-review/               ← 代码审查
├── code-simplifier/           ← 代码简化优化
├── dispatching-parallel-agents/ ← 分发并行 Agent
├── docx/                     ← DOCX 处理
├── executing-plans/           ← 执行计划
├── finishing-a-development-branch/ ← 完成开发分支
├── frontend-design/          ← 前端设计
├── install-software/         ← 自动安装软件
├── karpathy-guidelines/      ← Karpathy 编码准则
├── mcp-builder/              ← MCP 服务器构建
├── pdf/                      ← PDF 处理
├── planning-with-files/      ← 文件规划
├── receiving-code-review/    ← 接收代码审查
├── requesting-code-review/   ← 请求代码审查
├── skill-creator/            ← 创建/更新 Skill（已融合 skill-from-masters）
├── subagent-driven-development/ ← 子 Agent 驱动开发
├── systematic-debugging/     ← 系统化调试
├── test-driven-development/  ← TDD 测试驱动开发
├── using-git-worktrees/      ← Git Worktree 使用
├── using-superpowers/        ← 超级能力使用
├── verification-before-completion/ ← 完成前验证
├── web-dev/                  ← Web 开发
├── webapp-testing/           ← Web 应用测试
├── writing-plans/            ← 编写计划
└── writing-skills/           ← 创建/编辑 Skill
```

#### RAG Demo（无独立 Skill）

无项目级 Skill，使用全局 Skill。

---

## 三、Skill 详细介绍

### a-stock-data — A股全栈数据工具包

| 属性 | 值 |
|------|-----|
| 位置 | 投资指数资讯 |
| 作者 | simonlin1212（Simon 林） |
| 版本 | V3.2.2 |
| 协议 | Apache-2.0 |
| Star | 3,296+ |
| 数据源 | 13 个 |
| 端点 | 27 个 |
| 架构 | 7 层 |

**七层架构**：行情层(mootdx+腾讯+百度K线)、研报层(东财+同花顺)、信号层(同花顺热点+北向+龙虎榜+解禁+行业)、资金面(融资融券+大宗交易+股东户数+分红)、新闻层(东财个股新闻+全球资讯)、基础数据(mootdx财务/F10+新浪三表)、公告层(巨潮)

**依赖**: mootdx 0.11.7, requests, pandas 3.0.3, stockstats 0.6.8

**内置 4 套调研流程**: 单票估值(30s)、批量对比(1min)、主题研报(2min)、新标的调研(1min)

**数据源优先级**: 通达信(mootdx)不封IP > 腾讯不封IP > 新浪/巨潮/同花顺 > 东财(仅独有数据,已内置em_get限流防封)

### full-coverage-test — 功能调整后全面测试

| 属性 | 值 |
|------|-----|
| 位置 | 投资指数资讯 |
| 触发词 | 测试/验证/E2E/回归测试/全面测试/截图验证/质量评分 |

**四阶段流程**：
1. 编码前：需求清单 → 验证点 → 验收标准 → 选策略
2. 编码中：TDD 红绿重构（RED写失败测试→Verify RED→GREEN最小实现→Verify GREEN→REFACTOR）
3. 编码后：E2E截图(Playwright模拟用户操作,每步截图,必须遍历所有按钮/链接/导航/表单/弹窗/侧边栏) + 四层测试体系(L1静态/L2服务端/L3事件/L4逻辑) + 功能覆盖矩阵 + 多轮去重归并 + 根因追溯链 + 内容准入+否决+质量评分 + LLM二次审核
4. 标准化测试报告：概览+覆盖矩阵+问题分级+根因链+未解决问题+验证命令

**用户交互铁律**: 涉及用户交互的变更，必须用 Playwright 模拟用户操作点击进行全面的端到端功能遍历测试（点击每个按钮/链接/导航/表单/弹窗/侧边栏），每步截图。没有截图 = 没测。

**参考文件**: e2e-screenshot.md / layered-testing.md / content-filter.md / report-template.md / test-strategies.md

### guizang-social-card-skill — 小红书图文/公众号封面对生成

| 属性 | 值 |
|------|-----|
| 位置 | 投资指数资讯 |
| 作者 | op7418（归藏/龟藏） |
| 协议 | AGPL-3.0 |
| 文件数 | 28 |

**双视觉系统**: 电子杂志风(Editorial, 16个版式M01-M16, 6套主题) + 瑞士国际主义风(Swiss, 12个版式S01-S12, 4套锚点色)

**3 个画板尺寸**: xhs 1080×1440(小红书3:4)、wide 2100×900(公众号21:9)、square 1080×1080(公众号1:1)

**姊妹产品**: guizang-ppt-skill（网页 PPT 生成），两者共享美学语言但独立维护

### batch-import-skills — 批量导入 Skill

| 属性 | 值 |
|------|-----|
| 位置 | 各类测试 |
| 功能 | 将本地文件夹中的技能导入到 SOLO，适用于批量安装 |

### brainstorming — 创意与产品方向验证

| 属性 | 值 |
|------|-----|
| 位置 | 各类测试 |
| 功能 | Office Hours 6 问：需求真相/现状壁垒/具体场景/最小切入/验证方法/未来适配 |

### code-review — 代码审查

审查代码、检查bug、提升代码质量、安全审查。

### code-simplifier — 代码简化优化

简化优化最近修改的代码、重构、提升可读性。

### dispatching-parallel-agents — 分发并行 Agent

分发并行 Agent 任务。

### docx — DOCX 处理

Word 文档处理能力。

### drawio-skill — 画图

画图：流程图、架构图、泳道图、网络拓扑图、ER图、UML图、思维导图等。

### frontend-design — 前端设计

前端 UI/UX 设计指导。

### guizang-ppt-skill — 网页 PPT 生成

网页 PPT 生成（单 HTML 横向翻页），电子杂志风/瑞士国际主义风。

### humanizer-zh — 中文去 AI 痕迹

中文去 AI 写作痕迹，识别 24 种 AI 模式，让文字更像人写的。

### install-software — 自动安装软件

自动安装各类软件、包、工具，带自动重试和验证。

### karpathy-guidelines — Karpathy 编码准则

写代码、审查代码、重构代码时减少常见LLM编码错误。4 条准则：编码前先思考 / 简洁优先 / 外科手术式修改 / 目标驱动执行。

### mcp-builder — MCP 服务器构建

构建MCP服务器、集成外部API。

### pdf — PDF 处理

PDF 文档处理能力。

### ppt-master — PPT 生成

AI 驱动 PPT 生成，通过 SVG 合成原生可编辑 .pptx 文件。

### skill-creator — 创建/更新 Skill

**已融合 skill-from-masters（研究领域最佳实践）**。

Step 1.5：研究领域最佳实践 — Learn from Masters（可选但推荐）。搜索策略：GitHub 高星项目 → 领域专家方法论 → 行业报告/文章。

Step 6：跨项目同步（强制检查点）。Step 7：自检确认（强制检查点）。

### subagent-driven-development — 子 Agent 驱动开发

使用子 Agent 加速多任务开发。

### systematic-debugging — 系统化调试

系统化调试方法论。

### test-driven-development — TDD

测试驱动开发，铁律：没有先写失败测试 = 不能写生产代码。

### verification-before-completion — 完成前验证

铁律：没有新鲜验证证据就不能声称完成。五步关闸函数：确认→运行→读取→验证→才能声称。

### web-dev — Web 开发

从零创建网站、网页、Web 应用（不适用于已有项目修改）。

### webapp-testing — Web 应用测试

测试本地Web应用、验证前端功能、调试UI。

### writing-plans — 编写计划

编写执行计划。

### writing-skills — 创建/编辑 Skill

创建或编辑 Skill 定义。

### TRAE-product-knowledge — TRAE 品牌知识

内置全局 Skill，用于 TRAE 品牌身份和产品知识问题。

---

## 四、project_rules.md 对照

### 共同规则（三个项目共享）

| 检查点 | 名称 | 描述 |
|--------|------|------|
| 🔴 检查点0 | 规则自检 | 每轮对话第一步输出确认 |
| 🔴 检查点1 | Skill 检查 | 扫描 available_skills 列表，逐个判断 |
| 🔴 检查点2 | 验证循环 | 改后必须验证，循环直到满足需求 |
| 🔴 检查点3 | 禁止猜测 | 不确定必须测，禁止"应该可以" |
| 🔴 检查点4 | 跨项目同步 | 新增/修改Skill后同步所有 project_rules.md |
| 🔴 检查点5+ | 安全扫描 | 密钥泄露检查（各项目编号不同） |
| 🔴 安全红线 | API Key 泄露 | 680+ 元损失的教训，最高警戒 |
| Skill优先 | 先用 Skill | 检查可用列表，能用必用 |
| Karpathy编码 | 4 条准则 | 编码前思考/简洁优先/外科手术/目标驱动 |
| 极致自动化 | 懒人模式 | 零人工介入，穷举所有自动化方案 |

### 强制检查点编号差异

| 编号 | 投资指数资讯 | 各类测试-持仓系统 | RAG Demo |
|------|------------|-----------------|---------|
| 0 | 规则自检 | 规则自检 + 项目专属 | 规则自检 |
| 1 | Skill 检查 | Skill 检查 | Skill 检查 |
| 2 | 验证循环 | 验证循环 + portfolio-analysis 验证 | 验证循环 |
| 3 | 禁止猜测 | 禁止猜测 | 禁止猜测 |
| 4 | **跨项目同步** | **安全扫描** | **安全扫描** |
| 5 | **Windows Task Scheduler** | **跨项目同步** | **代码安全扫描** |
| 6 | **代码安全扫描** | **密钥泄露检查** | **跨项目同步** |

### 各项目专属规则

#### 投资指数资讯

- **Windows Task Scheduler 推送**：`daily_report.py` → PushDeer
- **双触发机制**：`Trae每日指数投资资讯`(08:00) + `-开机补发`(开机1分钟后)
- **防重复**：`push_status.json` 自动检查当天是否已推送
- **静默执行模式**：修改时不要停下来问确认，直接做完

#### 各类测试-持仓系统

- **生产环境定义**：有且仅有一个 `https://portfolio-analysis.top`
- **铁律**：本地 localhost 验证不算验证，CF Tunnel 不算验证，只有生产域名上的验证才算验证
- **修改流程**：改代码 → `python deploy_v2.py` → 等 5-10s CDN → Playwright 访问 portfolio-analysis.top → 截图 → 确认
- **日志优先**：任何异常先查 `data/logs/daily/log_YYYY-MM-DD.jsonl`
- **Windows 定时任务**：`\估值日报推送` 每天 08:00 执行
- **CF Tunnel**：`node cf_tunnel.cjs` 启动云隧道

#### RAG Demo

- **后端验证优先**：验证手段优先级为 自动化测试 > 代码审查 > 手动检查
- **Python 异步优先**：FastAPI + SQLAlchemy + ChromaDB

### API 安全铁律（三个项目通用）

**⚠️ 真实教训（670+ 元损失）：**

| 时间 | 泄露内容 | 来源 | 损失 |
|------|---------|------|------|
| 2026-06-10 | 百炼 API Key `sk-xxx` | index.html 硬编码 + 公网 OSS | **70+ 元** |
| 2026-06-19~20 | DeepSeek API Key `sk-xxx` | daily_report.py 硬编码 + Public GitHub | **600+ 元** |

**安全铁律：**
1. API Key 永不出现在任何源代码/HTML/前端 JS/配置文件中
2. 唯一合法位置：操作系统环境变量 / `.env`（必须在 `.gitignore` 中）
3. 前端调第三方 API 必须走后端代理（`/api/proxy`），禁止直连
4. 每次修改后强制扫描：`sk-`/`AKID`/`ghp_`/`Bearer`/`password`

---

## 五、安装来源记录

| Skill | 来源 | 安装时间 |
|-------|------|---------|
| a-stock-data | github.com/simonlin1212/a-stock-data | 2026-06-04 |
| full-coverage-test | 自建（从投资指数资讯+各类测试历史对话提炼） | 2026-06-09 |
| guizang-social-card-skill | github.com/op7418/guizang-social-card-skill | 2026-06-02 |
| guizang-ppt-skill | github.com/op7418/guizang-ppt-skill | 较早 |
| humanizer-zh | github.com/op7418/Humanizer-zh | 较早 |
| ppt-master | github 第三方 | 较早 |
| skill-creator | anthropics/skills 官方 | 较早（已融合 skill-from-masters） |
| batch-import-skills | 自建 | 较早 |
| browser-guide | 自建（融合 epiral/bb-browser） | 较早 |
| brainstorming | 自建（融合 office-hours） | 较早 |

### 龟藏（op7418）Skill 家族

| Skill | 已安装 | 备注 |
|-------|:-----:|------|
| guizang-ppt-skill | ✅ | 网页 PPT 生成 |
| guizang-social-card-skill | ✅ | 小红书图文/公众号封面 |
| humanizer-zh | ✅ | 中文去 AI 痕迹 |
| skill-from-masters | 🔄 已融合 | 融合到 skill-creator Step 1.5 |
| Youtube-clipper-skill | ❌ 条件可用 | 需 yt-dlp + FFmpeg |
| ai-desk-card | ❌ 硬件依赖 | 需 M5Paper V1.1 |

---

## 六、工作目录

```
d:\TRAE SOLO CN\
├── 投资指数资讯\         ← 主力项目：每日指数投资资讯
│   ├── .trae/rules/     ← project_rules.md（本目录）
│   ├── .trae/skills/    ← a-stock-data + full-coverage-test + guizang-social-card-skill + install-software
│   ├── daily_report.py  ← 每日资讯生成推送主脚本
│   ├── push_status.json ← 推送状态
│   ├── miniprogram/     ← 微信小程序
│   ├── website/         ← Web 前端
│   └── reports/         ← 已生成的每日报告
│
├── 各类测试\             ← 测试沙箱 + 持仓分析
│   ├── .trae/rules/     ← project_rules.md
│   ├── .trae/skills/    ← 27 个 Skill
│   ├── portfolio-analysis/ ← 持仓分析 React 应用
│   │   ├── src/         ← React 源码
│   │   ├── screenshots/ ← E2E 截图（35+）
│   │   └── data/logs/   ← 测试报告
│   └── valuation/       ← 估值日报
│
└── RAG Demo\             ← RAG 问答应用
    ├── .trae/rules/     ← project_rules.md
    └── backend/         ← FastAPI 后端
```
