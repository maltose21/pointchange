# 积分互兑中台系统设计文档 (Preliminary Design)

## 1. 系统架构概述
本系统作为“积分互兑中台”，向下连接各类业务资产（积分、优惠券、里程等），向上提供统一的兑换规则配置与计算服务。

### 核心模块
1.  **资产管理 (Asset Manager)**: 定义可参与兑换的资产及其底层接口信息。
2.  **规则引擎 (Rule Engine)**: 管理兑换汇率、门槛、限额及状态。
3.  **交易核心 (Transaction Core)**: (规划中) 处理实际的扣减与发放事务。

---

## 2. 数据库设计 (Database Schema)

### 2.1 资产定义表 (`assets`)
用于维护系统中所有可用的资产类型及其服务接入配置。

| 字段名 | 类型 | 必填 | 说明 | 示例 |
| :--- | :--- | :--- | :--- | :--- |
| **asset_code** | VARCHAR(32) | YES | **主键**，资产唯一标识，大写 | `MALL_POINT` |
| `asset_name` | VARCHAR(64) | YES | 资产显示名称 | `商城积分` |
| `service_url` | VARCHAR(255)| YES | 服务根地址 (Host) | `http://mall.internal` |
| `deduct_api` | VARCHAR(128)| NO | 扣减接口路径 | `/api/deduct` |
| `grant_api` | VARCHAR(128)| NO | 发放接口路径 | `/api/grant` |
| `query_api` | VARCHAR(128)| NO | 余额查询接口路径 | `/api/balance` |
| `auth_token` | VARCHAR(255)| NO | 接口调用凭证 (加密存储) | `sk_live_...` |
| `description`| TEXT | NO | 资产备注说明 | `核心购物积分` |
| `created_at` | DATETIME | YES | 创建时间 | `2026-02-10 12:00:00` |
| `updated_at` | DATETIME | YES | 更新时间 | `2026-02-10 12:00:00` |

### 2.2 兑换规则表 (`rules`)
定义源资产到目标资产的单向兑换逻辑。

| 字段名 | 类型 | 必填 | 说明 | 示例 |
| :--- | :--- | :--- | :--- | :--- |
| **rule_id** | VARCHAR(32) | YES | **主键**，规则唯一编号 | `R_20260210_001` |
| `name` | VARCHAR(128)| YES | 规则业务名称 | `积分兑换会员成长值` |
| `source_asset` | VARCHAR(32) | YES | **外键**，源资产代码 | `MALL_POINT` |
| `target_asset` | VARCHAR(32) | YES | **外键**，目标资产代码 | `VIP_GROWTH` |
| `exchange_rate`| DECIMAL(10,4)| YES | 兑换汇率 (1 Source = N Target) | `0.1000` |
| `step_size` | INT | YES | 兑换步长 (必须是该值的倍数) | `10` |
| `min_amount` | INT | YES | 起兑门槛 | `100` |
| `daily_limit` | INT | YES | 单日兑换限额 | `5000` |
| `status` | VARCHAR(16) | YES | 状态: `ENABLE`(启用), `DISABLE`(禁用) | `ENABLE` |
| `updated_by` | VARCHAR(64) | NO | 最后修改人 | `admin` |
| `updated_at` | DATETIME | YES | 最后修改时间 | `2026-02-10 12:00:00` |

---

## 3. 接口设计 (API Definitions)

### 3.1 管理端 API (Admin Portal)

#### 资产管理
- **查询资产列表**
    - `GET /api/v1/admin/assets`
- **录入新资产**
    - `POST /api/v1/admin/assets`
    - Body: `{ asset_code, asset_name, service_url, ... }`
- **更新资产配置**
    - `PUT /api/v1/admin/assets/{asset_code}`
- **删除资产**
    - `DELETE /api/v1/admin/assets/{asset_code}`

#### 规则配置
- **查询规则列表**
    - `GET /api/v1/admin/rules?page=1&status=ENABLE`
- **创建规则**
    - `POST /api/v1/admin/rules`
    - Body: `{ source_asset, target_asset, exchange_rate, ... }`
- **更新规则**
    - `PUT /api/v1/admin/rules/{rule_id}`
- **删除规则**
    - `DELETE /api/v1/admin/rules/{rule_id}`

### 3.2 业务端 API (Service Side) - *规划中*

#### 核心交易
- **兑换试算 (Calculate)**
    - `POST /api/v1/exchange/calculate`
    - Request: `{ rule_id, amount }`
    - Response: `{ source_deduct, target_grant, rate, fee }`

- **发起兑换 (Execute)**
    - `POST /api/v1/exchange/execute`
    - Request: `{ calc_token, user_id }`
    - Logic: 
        1. 锁定规则快照
        2. 调用 Source Asset `deduct_api`
        3. 调用 Target Asset `grant_api`
        4. 记录流水

---

## 4. 扩展性设计 (Future Plan)

1.  **多租户支持**: 在所有表增加 `tenant_id` 字段，支持 SaaS 化部署。
2.  **人群包定向**: `rules` 表增加 `user_group_id`，实现仅特定人群（如 VIP）可见高汇率规则。
3.  **风控接入**: 在 Execute 阶段增加风控前置校验。
