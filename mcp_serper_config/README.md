# Serper MCP Server 安装指南

## 📋 前置要求

1. **Node.js >= 18** (必需)
2. **Serper API Key** (从 https://serper.dev 获取)

## 🔑 获取 Serper API Key

1. 访问 https://serper.dev
2. 注册账号（免费额度：2500次查询/月）
3. 进入 Dashboard 获取 API Key

## 🚀 安装方法

### 方法1: 使用 npx 直接运行（推荐，最简单）

无需克隆仓库，直接在 MCP 配置中使用：

```json
{
  "mcpServers": {
    "serper-search": {
      "command": "npx",
      "args": ["-y", "serper-search-scrape-mcp-server"],
      "env": {
        "SERPER_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

### 方法2: 本地安装

```bash
# 1. 克隆仓库
git clone https://github.com/marcopesani/mcp-server-serper.git
cd mcp-server-serper

# 2. 安装依赖
npm install

# 3. 编译
npm run build

# 4. 配置环境变量
echo "SERPER_API_KEY=your_api_key_here" > .env
```

## 📁 配置文件

已为你创建以下配置文件：

- `mcp_config.json` - MCP 服务器配置
- `.env.example` - 环境变量示例

## 🛠️ 可用工具

### 1. `google_search` - Google 搜索
支持高级搜索运算符：
- `site:` 限定特定域名
- `filetype:` 限定文件类型 (pdf, doc等)
- `inurl:` URL中包含的关键词
- `intitle:` 标题中包含的关键词
- `before:` / `after:` 时间筛选
- `exact:` 精确匹配
- `exclude:` 排除关键词

### 2. `scrape` - 网页内容抓取
提取网页的纯文本和 markdown 内容

## 💡 使用示例

添加 MCP 服务器后，你可以问 AI：

- "搜索黄金价格最新走势"
- "查找 site:gov.cn 黄金期货政策"
- "搜索 filetype:pdf 黄金投资报告"
- "抓取这个网页的内容 https://example.com"

## 🔧 在 CodeBuddy 中使用

1. 打开 CodeBuddy 设置
2. 找到 MCP 服务器配置
3. 添加 `mcp_config.json` 中的配置
4. 将 `your_api_key_here` 替换为你的真实 API Key
5. 保存并重启

## 📊 API 用量

- 免费版：2500 次查询/月
- 付费版：$0.001/次查询

查看用量：https://serper.dev/dashboard
