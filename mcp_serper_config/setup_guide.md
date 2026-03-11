# CodeBuddy MCP 配置指南

## ✅ 已配置的服务器

你的 CodeBuddy 现在包含以下 MCP 服务器：

| 服务器 | 功能 | 状态 |
|--------|------|------|
| firecrawl | 网页抓取、搜索、数据提取 | ✅ 已配置 |
| github | GitHub 仓库操作、代码搜索 | ✅ 已配置 |
| memory | 知识图谱、记忆存储 | ✅ 已配置 |
| serper-search | Google 搜索、网页抓取 | ✅ 新添加 |

## 🔧 配置步骤

### 方法1: 通过 CodeBuddy UI 添加（推荐）

1. 点击左侧边栏 **「集成」** 按钮
2. 找到 **「MCP 服务器」** 选项
3. 点击 **「添加 MCP 服务器」**
4. 选择类型：**Command**
5. 填写以下信息：

```
名称: serper-search
命令: npx
参数: -y serper-search-scrape-mcp-server
环境变量: SERPER_API_KEY=9de569e3285d36c7fc1e95720d305ba59457e418
```

6. 点击 **「保存」**
7. 重启 CodeBuddy 或刷新页面

### 方法2: 直接修改配置文件

配置文件位置：
- macOS: `~/.codebuddy/mcp_config.json`
- Windows: `%USERPROFILE%\.codebuddy\mcp_config.json`

将 `codebuddy_mcp_config.json` 的内容复制到该文件中。

## 🧪 验证配置

配置完成后，你可以测试以下命令：

1. **搜索测试**: "搜索黄金价格最新走势"
2. **高级搜索**: "搜索 site:investing.com 黄金技术分析"
3. **文件搜索**: "搜索 filetype:pdf 黄金投资策略"
4. **网页抓取**: "抓取 https://www.investing.com 的金价信息"

## 🛠️ 可用工具说明

### Serper MCP 工具

1. **google_search**
   - 普通搜索: "搜索黄金价格"
   - 站点限定: "搜索 site:gov.cn 黄金政策"
   - 文件类型: "搜索 filetype:pdf 黄金报告"
   - 时间筛选: "搜索黄金价格 after:2024-01-01"
   - 精确匹配: "搜索 \"黄金价格走势\""

2. **scrape**
   - 抓取网页: "抓取 https://example.com 的内容"
   - 提取信息: "从 https://example.com 提取正文"

## 🔒 安全建议

1. **API Key 保护**:
   - 不要在公开场合分享你的 API Key
   - 定期更换 API Key
   - 监控 API 使用量

2. **用量监控**:
   - 免费额度：2500次/月
   - 查看用量：https://serper.dev/dashboard

## 📝 配置文件备份

完整配置已保存到：
`/Users/ydy/CodeBuddy/20260310193311/mcp_serper_config/codebuddy_mcp_config.json`

## 🚀 使用示例

配置完成后，你可以直接问 AI：

```
"搜索最新黄金价格走势"
"查找黄金技术分析报告 filetype:pdf"
"搜索 site:shfe.com.cn 黄金期货数据"
"抓取这个网页的内容 [URL]"
```

## ❓ 常见问题

**Q: 配置后没有反应？**
A: 请重启 CodeBuddy 或刷新页面

**Q: 搜索返回错误？**
A: 检查 API Key 是否正确，或查看 https://serper.dev/dashboard 用量

**Q: 如何禁用某个 MCP？**
A: 在 CodeBuddy 设置中取消勾选该 MCP 服务器
