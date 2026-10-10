# user_growth

基于 Frappe Framework v15 的用户增长分析自定义 App。

- **DocType `User Service Record`（用户服务记录）**：用户服务开通/流失单据；
  安装后由 `after_install` 钩子自动灌入约 800 条、覆盖近 24 个月的剧情化 mock 数据（幂等）。
- **Report `User Growth Analysis`（用户增长分析）**：Script Report，
  逐月统计新增开通、流失、净增、期末在网、流失率、MRR，支持日期/省份/套餐/渠道筛选。
- **Page 用户增长数据大屏**：免登录页面 `/growth-dashboard`，
  ECharts + 中国地图，深色科技风，30 秒自动刷新，1920×1080 等比缩放。
  数据接口仅输出聚合统计与脱敏信息。

统计口径、mock 数据剧情、环境启动与运维命令见仓库外层 `README.md`
（App 内统计口径实现位于 `user_growth/analytics.py`）。

重灌 mock 数据：

```bash
bench --site <site> execute user_growth.seed.reset_and_seed
```
