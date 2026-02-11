# PointChange - 通用积分互兑中台

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)
![Vue 3](https://img.shields.io/badge/vue-3.x-green.svg)

PointChange 是一个轻量级的积分资产互兑中台解决方案。它提供了一套完整的管理后台，用于配置和管理企业内部不同业务线（如商城积分、游戏币、会员成长值）之间的兑换规则。

## ✨ 核心特性

*   **💎 资产定义中台化**：支持动态录入资产类型，配置下游服务的 API 接口地址与鉴权信息。
*   **⚙️ 规则配置灵活化**：可视化配置兑换汇率、起兑门槛、步长限制及单日限额。
*   **🛡️ 完备的后台交互**：
    *   支持资产/规则的增删改查 (CRUD)。
    *   实时状态切换 (启用/禁用)。
    *   完善的表单校验与操作反馈 (Toast)。
*   **🚀 零依赖极速部署**：后端纯 Python 标准库实现 (No pip install needed)，前端 Vue 3 CDN 引入。

## 📸 系统截图

### 1. 规则配置管理
直观管理所有兑换规则，支持状态筛选与快速切换。
*(此处可插入规则列表页截图)*

### 2. 资产接入配置
统一管理各业务线的资产接口信息，实现标准化接入。
*(此处可插入资产录入弹窗截图)*

## 🛠️ 快速开始

### 前置要求
*   Python 3.8+
*   现代浏览器 (Chrome/Edge/Safari)

### 启动服务

```bash
# 1. 克隆仓库
git clone https://github.com/maltose21/pointchange.git
cd pointchange

# 2. 启动后端 (自动初始化 SQLite 数据库)
python3 server.py
```

服务默认运行在 `http://localhost:8000`。

### 访问管理后台
打开浏览器访问：**[http://localhost:8000/index.html](http://localhost:8000/index.html)**

## 📂 项目结构

```text
pointchange/
├── DESIGN.md       # 技术架构设计文档 (Schema & API)
├── PRD.md          # 产品需求文档
├── server.py       # 核心后端服务 (HTTP Server + SQLite)
├── index.html      # 管理后台前端 (Vue 3 + Tailwind)
└── README.md       # 项目说明
```

## 🔗 API 文档
详细的接口定义与数据库设计请参考 [DESIGN.md](./DESIGN.md)。

## 🤝 贡献
欢迎提交 Issue 或 Pull Request。对于重大变更，请先在 Issue 中讨论。

## 📄 许可证
MIT License
