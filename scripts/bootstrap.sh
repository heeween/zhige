#!/usr/bin/env bash
# 在 frappe 容器内初始化：配置 → 注册 App → 建站并安装 App（含 mock 数据）→ 构建资源
# 前提：docker compose up -d 已启动且数据库健康
set -euo pipefail

cd /home/frappe/frappe-bench

echo "==> 写入服务连接配置"
bench set-config -g db_host db
bench set-config -g redis_cache redis://redis-cache:6379
bench set-config -g redis_queue redis://redis-queue:6379
bench set-config -g redis_socketio redis://redis-queue:6379

echo "==> 注册 user_growth App"
# 生产镜像使用 frappe-bench/env 虚拟环境，直接用 .pth 把 App 挂进 sys.path（等价 editable 安装，无需构建后端）
SITE_PKGS=$(ls -d /home/frappe/frappe-bench/env/lib/python3*/site-packages | head -1)
echo "/home/frappe/frappe-bench/apps/user_growth" > "$SITE_PKGS/user_growth.pth"
# 确保 apps.txt 一行一个 App（原文件可能缺尾部换行）
touch sites/apps.txt
printf "\n" >> sites/apps.txt
grep -qx "user_growth" sites/apps.txt || echo "user_growth" >> sites/apps.txt

SITE=growth.localhost
if [ ! -d "sites/$SITE" ]; then
	echo "==> 创建站点 $SITE 并安装 App（含 after_install 自动灌入 mock 数据）"
	bench new-site "$SITE" \
		--mariadb-root-password admin \
		--admin-password admin \
		--install-app user_growth
fi

bench use "$SITE"
bench config dns_multitenant off

echo "==> 构建前端资源"
bench build --app user_growth

# 确保静态资源目录可被 /assets 访问到
if [ ! -e "sites/assets/user_growth" ]; then
	ln -sfn ../../apps/user_growth/user_growth/public sites/assets/user_growth
fi

echo "==> 完成。启动服务：docker compose exec -d frappe bash -lc 'cd /home/frappe/frappe-bench && bench serve --port 8000 --host 0.0.0.0'"
