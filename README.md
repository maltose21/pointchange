# ScoreChange - 通用积分互兑规则中心

这是一个基于 Python 标准库实现的积分互兑规则中心 MVP Demo。

## 项目结构
- `server.py`: 后端服务，基于 `http.server`，内置 SQLite 数据库。
- `index.html`: 前端交互页面，使用 Vue.js + Tailwind CSS。
- `PRD.md`: 产品需求文档。

## 快速开始

### 1. 启动服务
在终端中运行以下命令启动后端服务：

```bash
python3 server.py
```
*服务默认运行在 http://localhost:8000*

### 2. 访问 Demo
打开浏览器访问：
[http://localhost:8000/index.html](http://localhost:8000/index.html)

## 功能演示
1. **规则加载**：系统会自动初始化默认规则（如商城积分兑换成长值）。
2. **选择规则**：点击列表中的规则卡片。
3. **输入试算**：输入源积分数量（如 15），点击“试算”。
4. **查看结果**：系统会展示“建议扣除”、“实际获得”以及“剩余保留”的数值。
5. **模拟交易**：点击确认交易，查看下方的模拟日志流。

## 技术栈
- **Backend**: Python 3 (No external dependencies)
- **Frontend**: HTML5, Vue 3 (CDN), Tailwind CSS (CDN)
- **Database**: SQLite3
