/* 用户增长数据大屏
 * 数据源：/api/method/user_growth.api.get_dashboard_data（免登录聚合接口）
 * 布局按 1920x1080 设计，等比缩放适配；每 30 秒自动刷新。
 */
(function () {
	"use strict";

	var DESIGN_W = 1920;
	var DESIGN_H = 1080;
	var REFRESH_MS = 30000;
	var DATA_URL = "/api/method/user_growth.api.get_dashboard_data";
	var GEO_URL = "/assets/user_growth/maps/china.geojson.json";

	var COLOR = {
		cyan: "#38bdf8",
		blue: "#3b82f6",
		purple: "#a78bfa",
		green: "#34d399",
		red: "#fb7185",
		amber: "#fbbf24",
		ink2: "#9db4d8",
		axis: "rgba(157, 180, 216, 0.55)",
		split: "rgba(96, 130, 190, 0.14)",
	};

	var charts = {};
	var geoReady = fetch(GEO_URL)
		.then(function (res) { return res.json(); })
		.then(function (geojson) { echarts.registerMap("china", geojson); })
		.catch(function () { /* 地图加载失败时该图留空 */ });

	/* ---------- 缩放适配 ---------- */
	function fitScreen() {
		var scale = Math.min(window.innerWidth / DESIGN_W, window.innerHeight / DESIGN_H);
		var screen = document.getElementById("screen");
		screen.style.transform =
			"translate(-50%, -50%) scale(" + scale + ")";
	}
	window.addEventListener("resize", function () {
		fitScreen();
		Object.keys(charts).forEach(function (k) { charts[k].resize(); });
	});

	/* ---------- 时钟 ---------- */
	function tickClock() {
		var now = new Date();
		var week = ["日", "一", "二", "三", "四", "五", "六"][now.getDay()];
		var pad = function (n) { return String(n).padStart(2, "0"); };
		document.getElementById("date-line").textContent =
			now.getFullYear() + "年" + (now.getMonth() + 1) + "月" + now.getDate() + "日 星期" + week;
		document.getElementById("clock").textContent =
			pad(now.getHours()) + ":" + pad(now.getMinutes()) + ":" + pad(now.getSeconds());
	}

	/* ---------- KPI ---------- */
	var KPI_DEFS = [
		{ key: "active_users", label: "在网用户", color: "#38bdf8", unit: "人" },
		{ key: "new_this_month", label: "本月新增", color: "#34d399", unit: "人" },
		{ key: "churned_this_month", label: "本月流失", color: "#fb7185", unit: "人" },
		{ key: "net_this_month", label: "本月净增", color: "#fbbf24", unit: "人", signed: true },
		{ key: "churn_rate", label: "当月流失率", color: "#a78bfa", unit: "%", percent: true },
		{ key: "mrr", label: "MRR 月经常性收入", color: "#7dd3fc", unit: "¥", money: true },
	];

	function renderKpis(kpi) {
		var row = document.getElementById("kpi-row");
		if (!row.children.length) {
			KPI_DEFS.forEach(function (def) {
				var card = document.createElement("div");
				card.className = "kpi";
				card.style.setProperty("--kpi-accent", def.color);
				card.innerHTML =
					'<div class="kpi-label">' + def.label + "</div>" +
					'<div class="kpi-value" data-key="' + def.key + '"></div>';
				row.appendChild(card);
			});
		}
		KPI_DEFS.forEach(function (def) {
			var el = row.querySelector('[data-key="' + def.key + '"]');
			var v = kpi[def.key] || 0;
			var cls = "kpi-value";
			if (def.signed) cls += v >= 0 ? " pos" : " neg";
			el.className = cls;
			var text;
			if (def.money) {
				text = Number(v).toLocaleString("zh-CN", { maximumFractionDigits: 0 });
			} else if (def.percent) {
				text = Number(v).toFixed(1);
			} else {
				text = String(Math.round(v));
			}
			el.innerHTML = text + '<span class="unit">' + def.unit + "</span>";
		});
	}

	/* ---------- 图表公共样式 ---------- */
	function baseAxis() {
		return {
			axisLine: { lineStyle: { color: COLOR.axis } },
			axisLabel: { color: COLOR.ink2, fontSize: 12 },
			axisTick: { show: false },
			splitLine: { lineStyle: { color: COLOR.split } },
		};
	}

	function tooltipStyle() {
		return {
			backgroundColor: "rgba(10, 22, 49, 0.92)",
			borderColor: "rgba(64, 120, 255, 0.4)",
			textStyle: { color: "#e8f1ff", fontSize: 13 },
		};
	}

	function fmtMonth(m) { return m.slice(2).replace("-", "."); }

	/* ---------- 近24个月 新增/流失/净增 ---------- */
	function updateMonthly(series) {
		var months = series.map(function (r) { return fmtMonth(r.month); });
		charts.monthly.setOption({
			tooltip: Object.assign({ trigger: "axis" }, tooltipStyle()),
			legend: {
				top: 0, right: 10, textStyle: { color: COLOR.ink2 },
				itemWidth: 14, itemHeight: 9, data: ["新增开通", "流失", "净增"],
			},
			grid: { left: 46, right: 20, top: 34, bottom: 26 },
			xAxis: Object.assign(baseAxis(), { type: "category", data: months, boundaryGap: true, splitLine: { show: false } }),
			yAxis: [Object.assign(baseAxis(), { type: "value" }), Object.assign(baseAxis(), { type: "value", splitLine: { show: false } })],
			series: [
				{
					name: "新增开通", type: "bar", data: series.map(function (r) { return r.new; }),
					barMaxWidth: 14, itemStyle: { color: COLOR.green, borderRadius: [3, 3, 0, 0] },
				},
				{
					name: "流失", type: "bar", data: series.map(function (r) { return r.churned; }),
					barMaxWidth: 14, itemStyle: { color: COLOR.red, borderRadius: [3, 3, 0, 0] },
				},
				{
					name: "净增", type: "line", yAxisIndex: 1,
					data: series.map(function (r) { return r.net; }),
					smooth: true, symbol: "circle", symbolSize: 5,
					lineStyle: { color: COLOR.amber, width: 2 },
					itemStyle: { color: COLOR.amber },
				},
			],
		});
	}

	/* ---------- 在网趋势 + MRR ---------- */
	function updateTrend(series) {
		var months = series.map(function (r) { return fmtMonth(r.month); });
		charts.trend.setOption({
			tooltip: Object.assign({ trigger: "axis" }, tooltipStyle()),
			legend: {
				top: 0, right: 10, textStyle: { color: COLOR.ink2 },
				itemWidth: 14, itemHeight: 9, data: ["在网用户", "MRR"],
			},
			grid: { left: 46, right: 56, top: 34, bottom: 26 },
			xAxis: Object.assign(baseAxis(), { type: "category", data: months, boundaryGap: false, splitLine: { show: false } }),
			yAxis: [Object.assign(baseAxis(), { type: "value" }), Object.assign(baseAxis(), { type: "value", splitLine: { show: false } })],
			series: [
				{
					name: "在网用户", type: "line", data: series.map(function (r) { return r.active_end; }),
					smooth: true, symbol: "none",
					lineStyle: { color: COLOR.cyan, width: 2.5 },
					areaStyle: {
						color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
							{ offset: 0, color: "rgba(56, 189, 248, 0.35)" },
							{ offset: 1, color: "rgba(56, 189, 248, 0.02)" },
						]),
					},
				},
				{
					name: "MRR", type: "line", yAxisIndex: 1,
					data: series.map(function (r) { return r.mrr; }),
					smooth: true, symbol: "none",
					lineStyle: { color: COLOR.purple, width: 2, type: "dashed" },
				},
			],
		});
	}

	/* ---------- 套餐环形图 ---------- */
	function updatePlan(data) {
		var colors = [COLOR.cyan, COLOR.blue, COLOR.purple];
		charts.plan.setOption({
			tooltip: Object.assign({ trigger: "item", formatter: "{b}: {c} 人 ({d}%)" }, tooltipStyle()),
			color: colors,
			legend: {
				bottom: 4,
				left: "center",
				itemWidth: 12,
				itemHeight: 8,
				textStyle: { color: COLOR.ink2, fontSize: 12 },
			},
			series: [{
				type: "pie",
				radius: ["42%", "62%"],
				center: ["50%", "44%"],
				itemStyle: { borderColor: "rgba(5, 11, 28, 0.6)", borderWidth: 2 },
				label: {
					color: "#e8f1ff",
					fontSize: 12,
					position: "inside",
					formatter: "{d}%",
				},
				data: data,
			}],
		});
	}

	/* ---------- 渠道条形图 ---------- */
	function updateChannel(data) {
		var names = data.map(function (d) { return d.name; }).reverse();
		var values = data.map(function (d) { return d.value; }).reverse();
		charts.channel.setOption({
			tooltip: Object.assign({ trigger: "axis", axisPointer: { type: "shadow" } }, tooltipStyle()),
			grid: { left: 76, right: 40, top: 12, bottom: 6 },
			xAxis: Object.assign(baseAxis(), { type: "value", splitLine: { lineStyle: { color: COLOR.split } } }),
			yAxis: Object.assign(baseAxis(), { type: "category", data: names, splitLine: { show: false } }),
			series: [{
				type: "bar", data: values, barMaxWidth: 16,
				label: { show: true, position: "right", color: COLOR.ink2, fontSize: 12 },
				itemStyle: {
					borderRadius: [0, 8, 8, 0],
					color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
						{ offset: 0, color: "rgba(59, 130, 246, 0.35)" },
						{ offset: 1, color: COLOR.cyan },
					]),
				},
			}],
		});
	}

	/* ---------- 地图 ---------- */
	function updateMap(data) {
		if (!echarts.getMap || !echarts.getMap("china")) {
			setTimeout(function () { updateMap(data); }, 300);
			return;
		}
		var maxV = Math.max.apply(null, data.map(function (d) { return d.value; }).concat([1]));
		charts.map.setOption({
			tooltip: Object.assign({
				trigger: "item",
				formatter: function (p) {
					return p.name + "：" + (p.value ? p.value + " 人" : "暂无数据");
				},
			}, tooltipStyle()),
			visualMap: {
				min: 0,
				max: maxV,
				left: 12,
				bottom: 12,
				text: ["高", "低"],
				textStyle: { color: COLOR.ink2, fontSize: 12 },
				inRange: { color: ["#132c5e", "#1d5fae", "#2f9de0", "#6fe0f5"] },
				calculable: false,
			},
			series: [{
				type: "map",
				map: "china",
				roam: false,
				zoom: 1.18,
				top: 28,
				selectedMode: false,
				label: { show: false, color: "#cfe6ff", fontSize: 11 },
				itemStyle: {
					borderColor: "rgba(120, 180, 255, 0.55)",
					borderWidth: 0.7,
					areaColor: "#0f2447",
					shadowColor: "rgba(20, 80, 180, 0.5)",
					shadowBlur: 8,
				},
				emphasis: { label: { show: true }, itemStyle: { areaColor: "#38bdf8" } },
				data: data,
			}],
		});
	}

	/* ---------- 流失动态 ---------- */
	function renderFeed(items) {
		var ul = document.getElementById("churn-feed");
		ul.innerHTML = items
			.map(function (it) {
				return (
					"<li>" +
					'<span class="feed-date">' + it.churn_date + "</span>" +
					'<span class="feed-user">' + it.user + "</span>" +
					'<span class="feed-meta">' + it.province + " · " + it.plan_type + "</span>" +
					'<span class="feed-fee">-¥' + it.monthly_fee + "</span>" +
					"</li>"
				);
			})
			.join("");
	}

	/* ---------- 刷新 ---------- */
	function initCharts() {
		["plan", "channel", "monthly", "trend", "map"].forEach(function (key) {
			var el = document.getElementById("chart-" + key);
			charts[key] = echarts.init(el);
		});
	}

	function loadData() {
		return fetch(DATA_URL, { headers: { Accept: "application/json" } })
			.then(function (res) { return res.json(); })
			.then(function (json) { return json.message; });
	}

	function refresh() {
		return loadData()
			.then(function (data) {
				renderKpis(data.kpi);
				updateMonthly(data.monthly);
				updateTrend(data.monthly);
				updatePlan(data.plan);
				updateChannel(data.channel);
				geoReady.then(function () { updateMap(data.province); });
				renderFeed(data.recent_churn);
				document.getElementById("updated-at").textContent = "更新于 " + data.updated_at;
			})
			.catch(function () {
				document.getElementById("updated-at").textContent = "加载失败，稍后自动重试…";
			});
	}

	fitScreen();
	tickClock();
	setInterval(tickClock, 1000);
	initCharts();
	refresh();
	setInterval(refresh, REFRESH_MS);
})();
