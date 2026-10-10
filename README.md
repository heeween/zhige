# user_growth — 用户增长分析应用

基于 [Frappe Framework](https://github.com/frappe/frappe)（v15）的自定义 App，包含三项交付内容：

| # | 交付物 | 名称 | 说明 |
|---|--------|------|------|
| 1 | DocType | **User Service Record / 用户服务记录** | 用户服务开通/流失单据，含 800 条、覆盖近 24 个月的剧情化 mock 数据 |
| 2 | Report | **User Growth Analysis / 用户增长分析** | Script Report，逐月输出新增/流失/净增/在网/流失率/MRR |
| 3 | Page | **用户增长数据大屏** | 免登录深色大屏 `http://localhost:8000/growth-dashboard`，ECharts + 中国地图 |

App 另附带公共工作台「**用户增长**」（`growth/workspace/`）：登录后台后侧边栏直达，
含三个快捷入口——用户服务记录（列表，带数量角标）、用户增长分析（报表）、用户增长大屏（免登录页）。

## 快速开始（本仓库自带 Docker 环境）

前置要求：Docker（含 compose v2）。

```bash
# 1. 启动基础设施（首次会拉取镜像，走 DaoCloud 加速）
docker compose up -d

# 2. 初始化：建站 + 安装 App（after_install 钩子自动灌入 800 条 mock 数据）+ 构建前端资源
docker compose exec frappe bash /workspace/scripts/bootstrap.sh

# 3. 启动 Web 服务
docker compose exec -d frappe bash -lc 'cd /home/frappe/frappe-bench && bench serve --port 8000 --host 0.0.0.0'

# 4. 访问
#    大屏（免登录）：   http://localhost:8000/growth-dashboard
#    管理后台：        http://localhost:8000/app
#    登录账号：Administrator / admin（或完成向导后创建的 admin@example.com）
#    单据列表：        http://localhost:8000/app/user-service-record
#    增长分析报表：    http://localhost:8000/app/query-report/User%20Growth%20Analysis
```

## 三项内容说明

### 1. DocType：User Service Record（用户服务记录）

一条单据 = 一个用户的一次服务订阅。

| 字段 | 类型 | 说明 |
|------|------|------|
| 用户姓名 / 手机号 | Data | 手机号仅内部管理，对外接口与大屏不会输出 |
| 客户类型 | Select | 个人 / 企业 |
| 套餐类型 | Select | 基础版（¥49）/ 标准版（¥99）/ 旗舰版（¥199） |
| 月费金额 | Currency | 促销月可能有折扣价（¥39 / ¥89 / ¥159） |
| 开通日期 / 获客渠道 / 省份 | Date / Select | 渠道：线上广告、地推、转介绍、自然流入；省份 10 个 |
| 状态 | Select | 在网 / 已流失 |
| 流失日期 | Date | 状态为"已流失"时必填且须晚于开通日期（模型层校验） |

单据编号规则 `USR-{YYYY}-{#####}`；权限仅 System Manager。

**Mock 数据**（`user_growth/seed.py`，随机种子固定，可复现）：

- 约 800 条订阅记录，覆盖最近 24 个月（以安装日为终点回溯）；
- 剧情化生成：获客量逐月上升（约 20→50 条/月）、春秋季节波动、
  第 14 个月"调价风波"当月流失率冲高至 9%、第 21 个月"大促拉新"当月新增冲高 35%、
  约 12% 流失用户会在 1~2 个月内回流再开通（同手机号多条记录）；
- 幂等：已有数据时自动跳过。

重灌命令：

```bash
docker compose exec frappe bash -lc \
  'cd /home/frappe/frappe-bench && bench --site growth.localhost execute user_growth.seed.reset_and_seed'
```

### 2. Report：User Growth Analysis（用户增长分析）

Script Report（Python 服务端），路径 `/app/query-report/User Growth Analysis`。
筛选器：开始/结束日期、省份、套餐类型、获客渠道。

统计口径（与 `user_growth/analytics.py` 一致）：

- **期初在网**：当月 1 日仍处于在网状态的用户数；
- **新增开通**：当月开通的记录数；
- **流失**：当月发生流失的记录数（含窗口期前开通的用户）；
- **净增** = 新增 − 流失；**期末在网** = 期初在网 + 新增 − 流失；
- **流失率** = 流失 ÷ 期初在网 × 100%（≥5% 标红）；
- **MRR**：月末在网记录的月费总额。

末行为"合计/月末"汇总行；净增为负标红。

### 3. Page：用户增长数据大屏

- 路由 `http://localhost:8000/growth-dashboard`（www 网站页面，**免登录**可访问；
  desk 路由规则见 `hooks.py` 的 `website_route_rules`）；
- 数据接口 `user_growth.api.get_dashboard_data`（`allow_guest=True`），
  **只输出聚合统计与脱敏信息**（姓名脱敏为"张\*\*"，不含手机号）；
- 技术栈：ECharts 5 与中国地图 geojson 均打包在 `user_growth/public/`，离线可用；
- 内容：6 个 KPI 卡片（在网/本月新增/本月流失/本月净增/流失率/MRR）、
  近 24 个月新增流失净增组合图、在网趋势 + MRR 虚线、套餐环形图、
  渠道条形图、省份地图填色、最新流失动态（脱敏）；
- 30 秒自动刷新；按 1920×1080 设计、整屏等比缩放，适合大屏幕/投屏常驻。

## 目录结构

```
docker-compose.yml            # 本地演示环境（Frappe v15 + MariaDB 10.6 + Redis）
scripts/bootstrap.sh          # 容器内一次性初始化脚本
user_growth/                  # App 源码（bench 标准 App 结构）
├── pyproject.toml
└── user_growth/
    ├── hooks.py              # after_install、大屏路由规则
    ├── install.py            # 安装后自动灌数据
    ├── seed.py               # mock 数据生成器（剧情化、幂等）
    ├── analytics.py          # 报表/大屏共用的统计口径
    ├── api.py                # 免登录大屏数据接口（仅聚合）
    ├── growth/               # 模块 "Growth"
    │   ├── doctype/user_service_record/    # 单据：JSON 模型 + 校验逻辑
    │   ├── report/user_growth_analysis/    # Script Report：py + js(筛选器/格式化)
    │   └── workspace/user_growth/          # 公共工作台「用户增长」（侧边栏入口）
    ├── www/growth_dashboard.{html,py}      # 大屏页面
    └── public/               # css / js / echarts.min.js / china.geojson.json
```

## 常用运维命令

```bash
# 改了 App 代码后同步模型/报表到站点
docker compose exec frappe bash -lc 'cd /home/frappe/frappe-bench && bench --site growth.localhost migrate'

# 重新构建前端资源
docker compose exec frappe bash -lc 'cd /home/frappe/frappe-bench && bench build --app user_growth'

# 查看数据量
docker compose exec frappe bash -lc \
  'cd /home/frappe/frappe-bench && bench --site growth.localhost execute frappe.db.count --args "[\"User Service Record\"]"'
```
