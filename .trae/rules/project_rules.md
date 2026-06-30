# 项目规则

## ⚡ 每轮对话强制执行流程（最高优先级，违反即失败）

**每轮对话必须严格按以下顺序执行，不得跳过任何步骤：**

### 🔴 强制检查点0：规则自检（每轮第一步）
- **每轮对话开始时，必须先输出以下确认：**
  ```
  ✅ 规则自检：
  - Skill检查：[列出相关Skill及是否已加载]
  - 工作流检查：[GH Actions最新运行状态]
  - 验证计划：[说明如何验证结果]
  - 安全扫描：[确认修改不涉及密钥/密码/Token硬编码]
  - 禁猜确认：[确认不猜测，不确定就问]
  ```
- 未输出此确认 = 违规
- **规则自检后立即执行检查点7（工作流失败自动检测）**

### 🔴 强制检查点1：Skill检查（不可跳过）
- 收到任务后第一件事：扫描 `<available_skills>` 列表
- **逐个判断每个Skill是否相关，输出判断结果**
- 相关的Skill **必须调用 `Skill` 工具加载**，之后再执行任务
- 即使任务看起来很直接，也必须先过 Skill 检查流程并输出判断

### 🔴 强制检查点2：验证循环（目标驱动）
- 完成任务后，**不能假设成功**，必须验证
- 每次修改后自我验证 → 发现问题 → 修复 → 再验证
- 循环直到确认满足需求，不允许"改完就等用户反馈"的弱循环
- 验证手段优先级：自动化截图 > 自动化测试 > 代码审查
- **必须输出验证结果，不能省略**

### 🔴 强制检查点3：禁止猜测
- 不确定效果时必须先测试验证，不能凭经验猜测
- 明显困惑时必须停下来，列出困惑点，使用 AskUserQuestion
- **禁止说"应该可以"、"大概没问题"等模糊表述，必须验证后给出确定结论**

### 🔴 强制检查点4：跨项目同步（新建/修改 Skill 后强制执行）
**每当你新增或修改了一个 Skill（包括创建 SKILL.md、修改描述、安装第三方 Skill），必须同步所有项目的 project_rules.md，不允许只更新当前项目。**
- 搜索 `d:\` 下所有 `project_rules.md` 文件
- 逐个检查：新/修改的 Skill 是否已在表格中列出
- 如未列出 → 添加；如描述过时 → 更新
- **输出同步结果表格**：[路径] → [已更新/无需更新]
- 未执行此步 = 违规

### 🔴 强制检查点5：云端 GitHub Actions 统一推送（本项目唯一推送方式）
**所有推送由云端 GitHub Actions 管理，推送内容是 daily_pipeline.py 生成、部署到 OSS 的 AI算力产业链新闻摘要。不依赖本地电脑开关机。**

**推送链路：**
| 调度方式 | 运行位置 | 生成方式 | 核心文件 |
|---------|---------|---------|---------|
| GitHub Actions cron + 跨仓库调度器 `daily-news-scheduler` | 云端 Ubuntu | daily_pipeline.py 采集RSS→DeepSeek分析→生成news JSON→push_news_digest.py 读取JSON按影响级别分组推送 | `push_news_digest.py` + `.github/workflows/daily_news.yml` |

**单 Job 架构（daily-news job 内顺序执行）：**
| 步骤 | 用途 | 推送标题 |
|------|------|---------|
| 运行数据流水线 | daily_pipeline.py 采集RSS+DeepSeek分析→生成 news_site/public/data/{today}.json | - |
| 构建前端+部署OSS | 部署到 portfolio-analysis.top/news/index.html | - |
| 推送今日资讯摘要 | push_news_digest.py 读取今日JSON，按影响大/中分组推送 | "AI算力产业链每日资讯" |
| 汇总报告并发送通知 | workflow_logger.py 推送工作流执行状态 | "AI算力每日资讯 工作流报告" |

**跨仓库调度器（解决 GitHub Actions schedule 对删除重建 workflow 不重新注册的问题）：**
- 私有仓库 `daily-news-scheduler` 的 `scheduler.yml` 在北京 08:05 调用 workflow_dispatch API
- PAT_TOKEN 作为 encrypted secret 注入

**防重复机制（云端版）：**
- 防重由 GitHub Actions 调度天然保证（每天固定时间触发一次）
- `news_history.json` 跨日去重由 daily_pipeline.py 内部 load_recent_seen() 处理（从 OSS 读取最近7天数据）
- 周末 cron 仍触发，但新闻数据可能为空，push_news_digest.py 检测到 count==0 自动跳过推送

**相关文件（云端，已纳入 git）：**
- `push_news_digest.py` — 读取今日 news JSON，按影响级别分组推送到 PushDeer
- `daily_pipeline.py` — RSS采集+DeepSeek分析，生成 news JSON
- `.github/workflows/daily_news.yml` — workflow 定义（daily-news job 含采集→部署→推送摘要→汇总报告）
- `workflow_logger.py` — 工作流日志+状态推送

**已废弃文件（2026-06-30 彻底推倒重做时删除/弃用）：**
- ~~`run_daily_report.bat`~~ — 已删除
- ~~`setup_admin.bat`~~ — 已删除
- ~~`task_daily_report.xml`~~ — 已删除
- ~~`push_status.json`~~ — 云端不再使用
- ~~`logs/task_runner.log`~~ — 云端不再使用
- `daily_report.py` — 旧的投资日报脚本（新浪财经+28条宽基行业），**已不再被 workflow 调用**，仅保留本地调试用

**手动触发命令（调试用）：**
```powershell
# 通过 GitHub API 触发 workflow_dispatch（需 GITHUB_TOKEN 环境变量）
python -c "import json, urllib.request, os; token=os.environ.get('GITHUB_TOKEN',''); data=json.dumps({'ref':'main','inputs':{'skip_pipeline':False,'skip_push_digest':False,'force_refresh':False}}).encode(); req=urllib.request.Request('https://api.github.com/repos/zhenggongze/daily-index-news/actions/workflows/daily_news.yml/dispatches', data=data, headers={'Accept':'application/vnd.github+json','Authorization':f'Bearer {token}','User-Agent':'python'}, method='POST'); urllib.request.urlopen(req, timeout=15); print('✅ triggered')"

# 查看最近运行状态
python _check_actions_v2.py
```

**本地运行 push_news_digest.py（调试用，需设 PUSHDEER_KEY 才真推送）：**
```powershell
# 仅生成 today_digest.md 不推送（不设 PUSHDEER_KEY）
$env:PUSHDEER_KEY=""; python push_news_digest.py --date 2026-06-24

# 真推送（设 PUSHDEER_KEY）
python push_news_digest.py
```

### 🔴 强制检查点7：工作流失败自动检测（本轮新增，每轮对话开始时强制执行）
**我负责发现并自动修复工作流失败，用户不需要看任何报错。**

**每轮对话开始时（规则自检之后）必须执行：**
1. 运行 `python _check_actions_v2.py` 检查 GH Actions 最新 3 次运行状态
2. 如果有新失败（比上次检查更晚且 `conclusion=failure`）：
   - 分析失败原因（调用 GH API 获取失败步骤的日志）
   - 修复代码
   - `git add/commit/push`
   - 在回复中告知用户"X步骤失败，已自动修复，原因：Y"
3. 如果全部成功 → 正常回复，不提及

**核心原则：用户永远不需要看工作流失败信息。**

### 🔴 强制检查点6：代码安全扫描（所有项目通用，最高优先级）
**每次改完代码后，必须遍历所有修改过的文件 + 新增文件，逐行扫描以下内容是否存在：**

**扫描清单（零容忍）：**
1. `sk-` 开头的字符串 → API Key 泄露
2. `ghp_` / `gho_` / `ghu_` / `ghs_` 开头的字符串 → GitHub Token 泄露
3. `AKID` / `SecretKey` / `access_key` / `secret_key` → 云服务密钥
4. 硬编码的密码、Token、认证凭据
5. 数据库连接字符串含密码（如 `mysql://user:password@host`）

**扫描范围：**
- 本次修改/新增的每一个文件
- 特别是 HTML、JS、JSON、配置文件（`.env`、`.json`、`config*`）
- 前端文件（HTML/JS）中绝对禁止出现 API Key — 所有对公网可见
- 如果涉及**其他项目**的修改（非当前工作目录），必须有额外的警惕意识

**违规处理：**
- 扫到疑似泄露 → 立即修复（换环境变量/配置分离）
- 通知用户去云平台控制台吊销泄露的 Key
- 记录到项目规则中，防止重复犯错

---

## Skill优先原则

**每次执行任务前，必须先检查可用的Skill列表，能用则用。**

具体要求：
1. 收到用户任务后，第一步是审视 `<available_skills>` 列表
2. 逐一判断每个Skill是否与当前任务相关
3. 相关的Skill必须调用加载后再执行任务，不要跳过Skill直接手工实现
4. 如果多个Skill都相关，按优先级依次调用

### 当前可用Skill及适用场景

| Skill | 适用场景 |
|-------|---------|
| a-stock-data | A股全栈数据工具包 — 七层架构27端点（行情/研报/信号/资金面/新闻/财报/公告），适用于个股估值、研报检索、龙虎榜跟踪、北向资金等投研场景 |
| batch-import-skills | 批量将本地文件夹中的技能导入到 SOLO 中，适用于安装多个技能或从本地文件夹复制技能 |
| brainstorming | 任何创意性工作前、产品方向验证（Office Hours 6问：需求/壁垒/场景/切入/验证/未来） |
| browser-guide | 浏览器访问特定互联网平台（知乎/GitHub/百度等），配合 integrated_browser MCP |
| code-review | 审查代码、检查bug、提升代码质量、安全审查（含密钥泄露检查） |
| code-simplifier | 简化优化最近修改的代码、重构、提升可读性（修改后需安全扫描） |
| drawio-skill | 画图：流程图、架构图、泳道图、网络拓扑图、ER图、UML图、思维导图等 |
| full-coverage-test | 功能调整后全面测试 Skill — 编码前需求清单 + 编码中TDD红绿重构 + 编码后E2E截图/四层测试/功能覆盖矩阵/根因追溯 + 内容准入否决质量评分（改代码后需安全扫描） |
| guizang-ppt-skill | 网页 PPT 生成（单 HTML 横向翻页），电子杂志风/瑞士国际主义风 |
| guizang-social-card-skill | 小红书图文/公众号封面对生成（杂志风/瑞士风双视觉系统），姊妹产品与 guizang-ppt-skill 互补 |
| humanizer-zh | 中文去 AI 写作痕迹，识别 24 种 AI 模式，让文字更像人写的 |
| karpathy-guidelines | 写代码、审查代码、重构代码时减少常见LLM编码错误（含密钥硬编码检查规则） |
| mcp-builder | 构建MCP服务器、集成外部API（密钥必须用环境变量，禁止硬编码） |
| ppt-master | AI 驱动 PPT 生成，通过 SVG 合成原生可编辑 .pptx 文件 |
| skill-creator | 创建新Skill或更新现有Skill（创建后需检查不包含敏感信息） |
| web-dev | 从零创建网站、网页、Web应用（创建后必须安全扫描，前端禁止硬编码API Key） |
| webapp-testing | 测试本地Web应用、验证前端功能、调试UI |
| writing-skills | 创建/编辑/验证Skill |

## Karpathy编码准则

源自Andrej Karpathy对LLM编码常见错误的观察，偏向谨慎而非速度。

### 1. 编码前先思考
**不要假设，不要隐藏困惑，暴露权衡。**
- 明确陈述假设，不确定就问
- 存在多种理解时全部列出，不要静默选择
- 如果有更简单的方案，说出来，必要时反驳
- 不清楚就停下来，指出困惑点，提问

### 2. 简洁优先
**用最少的代码解决问题，不做任何推测性设计。**
- 不添加未被要求的功能
- 不为单次使用的代码创建抽象
- 不添加未被要求的"灵活性"或"可配置性"
- 不为不可能发生的场景写错误处理
- 如果200行代码可以50行解决，重写
- 自问："资深工程师会觉得这过度复杂吗？"如果是，简化

### 3. 外科手术式修改
**只改必须改的，只清理自己制造的混乱。**
- 不要"改进"相邻代码、注释或格式
- 不要重构没坏的东西
- 匹配现有风格，即使你会有不同做法
- 发现无关死代码时提一下，不要删除
- 自己的修改产生了孤立代码时，删除自己造成的无用import/变量/函数
- 不要删除已有的死代码，除非被要求
- **检验标准：每一行改动都应该能追溯到用户的需求**

### 4. 目标驱动执行
**定义成功标准，循环直到验证通过。**
- 将任务转化为可验证的目标：
  - "添加验证" → "为无效输入写测试，然后让测试通过"
  - "修复bug" → "写一个能复现的测试，然后让测试通过"
  - "重构X" → "确保重构前后测试都通过"
- 多步骤任务时，先陈述简要计划：
  ```
  1. [步骤] → 验证: [检查方式]
  2. [步骤] → 验证: [检查方式]
  3. [步骤] → 验证: [检查方式]
  ```
- 强成功标准让你能独立循环，弱成功标准（"让它能用"）需要不断确认

### 5. 安全扫描（公网部署强制）
**所有项目最终要部署到公网！每次改完代码必须逐行扫描所有修改/新增文件：**

**强制扫描清单（每一项都是红色警报）：**
1. `sk-` / `ghp_` / `gho_` / `ghu_` / `ghs_` / `AKID` / `SecretKey` / `access_key` / `secret_key` 开头的字符串
2. 硬编码的密码、Token、认证凭据
3. 数据库连接字符串（`mysql://user:password` / `postgres://user:password` / `redis://:password`）
4. 前端文件中的任何API Key — 浏览器查看源码就可见
5. 配置文件（`.env` / `.json` / `config*` / `*.yml` / `*.yaml`）中的敏感凭据

**修复原则：**
- 发现疑似泄露 → 立即换成环境变量加载 + 通知用户去云平台吊销旧Key
- 前端发请求必须走自己的后端代理，不能直接带Key调第三方API
- 记入project_rules防重复犯错

## 其他规则

- 代码注释使用中文
- 不主动创建文档文件（*.md/README），除非用户明确要求

## 🔇 静默执行模式（本项目强制）

**修改和执行任务时，不要停下来让我确认或做决策。直接做完。**

## 🔴 API密钥安全铁律（硬规则，违反即事故 — 已酿成600+元损失）

### 惨痛教训
| 日期 | 泄露Key | 位置 | 损失 |
|------|--------|------|------|
| 2026-06-17 | 阿里云百炼 `sk-xxx...` | `index.html` / `server.cjs` 硬编码 | 70+ 元 |
| 2026-06-19~20 | DeepSeek `sk-xxx...` | `daily_report.py` 硬编码 + **Public GitHub 仓库** | **600+ 元** |

**根因：仓库 public + 代码中硬编码 API Key → GitHub Code Search 被爬取 → 被盗用。**

### API Key安全规则（零容忍，违反即事故）
1. **禁止** 在任何源代码文件（`.py/.js/.html/.json/.yml/.md`）中硬编码 API Key/Token/密码
2. **唯一合法存放位置**: 操作系统环境变量 / `.env` 文件（`.env` 必须在 `.gitignore` 中）
3. **代码中读取方式**: `os.environ.get("KEY", "")` 或 `process.env.KEY`
4. **`.env` 文件** 必须加入 `.gitignore`，且**绝不提交到 Git**
5. **Public GitHub 仓库** + API Key = **必然泄露**，没有例外
6. **每次 commit 前** 强制执行安全扫描（检查点6），扫 `sk-/ghp_/AKID/Secret` 等模式
7. 泄露的 Key **立即吊销**，重新生成
8. 属于外部项目（非当前工作目录）的修改，同样必须安全扫描

### 强制执行：.gitignore 必须包含
```
.env
*.env
```

### 🔴 每轮对话结束时必须输出安全确认
```
🔒 安全扫描确认：
- 涉及修改文件数：[N]
- 是否有Key泄露：[是/否]
- .env 是否在 .gitignore 中：[是/否]
```

- 不要问"要不要改"、"方案行不行"、"可以开始吗"——直接执行
- 修改后直接验证、修复、再验证，直到完成为止
- 只在最终完成后用一两句话告知结果即可
- 我如果给反馈，你继续修正，不要停下来确认
- 这条规则的优先级别最高，覆盖所有其他规则中的"需要确认"的描述

## 🤖 极致自动化原则（极其懒人模式）

**用户是极其懒的人，目标是零人工介入。**

### 自动化优先级（从高到低穷举）
1. **全自动完成** — 代码/脚本/配置一步到位，无需用户参与
2. **绕过限制** — 遇到权限/安全策略时，换工具/换方法/换路径绕过去（如Node.js绕过文件写入限制）
3. **静默处理** — 非致命错误自动fallback，不停下来问用户
4. **最后才通知用户** — 只有穷举所有自动化方案都失败后，才告诉用户需要手动操作

### 遇到"需要用户手动操作"时的强制流程
```
发现"需要用户操作"的步骤
    ↓
暂停，全面思考：这一步能不能自动化？
    ↓
┌→ 能自动化 → 立刻做，不通知用户
├→ 换工具能做 → 换工具做
├→ 换路径能做 → 换路径做
├→ 分步能做 → 拆解后逐步自动化
└→ 实在不能 → 通知用户（同时给出最简单的操作步骤）
```

### 典型场景示例
| 场景 | ❌ 错误做法 | ✅ 正确做法 |
|------|------------|-----------|
| 需要管理员权限 | "请以管理员运行" | 尝试用RunCommand绕过去，尝试Node.js绕过去，尝试别的路径写文件 |
| 文件写入被拒绝 | "请手动复制文件到..." | 换Node.js写、换PowerShell写、换cmd写 |
| 需要用户点击UAC | "请点击确认" | 先尝试不需要提权的方案 |
| 需要用户安装软件 | "请手动安装XXX" | 用install-software Skill自动安装 |
| 需要用户重启 | "请重启电脑" | 先尝试无需重启的方案（刷新PATH、重启服务等） |

### 通知用户的前提条件
必须同时满足以下**全部**条件才能通知用户手动操作：
1. 已尝试 **3种以上** 不同的自动化方案
2. 每种方案都有明确的失败原因
3. 确认不存在其他可尝试的自动化路径
4. 通知时给出 **最简单、最具体** 的操作步骤（不超过3步）
