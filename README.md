# 郑公泽指数投资每日资讯推送系统

## 📁 文件说明

| 文件 | 说明 |
|------|------|
| `run_daily_push.js` | 主推送脚本 |
| `setup_schedule.bat` | 设置Windows任务计划（自动每天运行） |
| `push_now.bat` | 手动立即推送（测试用） |
| `reports/` | 历史报告存档目录 |
| `push_current.html` | 临时推送文件（自动生成） |

## 🚀 快速开始

### 方式一：手动推送（测试）
双击 `push_now.bat` 即可立即推送一次日报

### 方式二：设置自动推送（推荐）
1. 右键点击 `setup_schedule.bat` → **以管理员身份运行**
2. 任务创建成功后，每天 **08:05** 会自动推送

### 任务管理命令
- 查看任务: `schtasks /query /tn "郑公泽每日资讯推送"`
- 删除任务: `schtasks /delete /tn "郑公泽每日资讯推送" /f`
- 立即运行: `schtasks /run /tn "郑公泽每日资讯推送"`

## 🔧 配置说明

### 修改推送时间
编辑 `setup_schedule.bat`，找到 `/st 08:05`，修改为您想要的时间（24小时制）

### 修改Server酱SendKey
在 `run_daily_push.js` 顶部修改：
```javascript
const SENDKEY = process.env.SCT_SENDKEY || '您的SendKey';
```

## 📱 移动端适配
- iPhone 14 Plus (428px宽度) 完美适配
- 卡片式新闻块，圆角+阴影设计
- 行业彩色渐变区块区分
- 利好/利空彩色标签
- 风险提示突出显示

## 📝 日报内容结构
1. 市场速览（三大指数+一句话总结）
2. 宽基指数要闻（6条）
3. 行业指数新闻（5个行业，每个3条）
4. 风险提示（4条）

---
*本系统使用Edge浏览器自动提交POST表单实现Server酱推送*
