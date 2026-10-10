app_name = "user_growth"
app_title = "User Growth"
app_publisher = "zhige"
app_description = "用户服务开通/流失单据、用户增长分析报表与增长数据大屏"
app_email = "zhige@example.com"
app_license = "mit"

after_install = "user_growth.install.after_install"

# 免登录大屏使用短横线路由，映射到 www 页面文件 growth_dashboard
website_route_rules = [
	{"from_route": "/growth-dashboard", "to_route": "/growth_dashboard"},
]

# 「用户增长」工作台快捷入口的自定义样式（选择器按 aria-label 限定作用范围）
app_include_css = ["/assets/user_growth/css/workspace.css"]
