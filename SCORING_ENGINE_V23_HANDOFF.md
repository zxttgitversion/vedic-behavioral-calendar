# Behavioral Calendar Scoring/Data Flow v2.3 (Guru + PM Handoff)

本文档说明当前代码里的真实链路：从 `zz.txt` 输入，到每日分数与页面展示输出。

示例输入文件：`behavioral-calendar/user_input_example/zz.txt`

## 1. `.md` 文件是做什么的

`.md`（Markdown）是项目的说明文档格式，用来记录：
- 业务规则（算法、阈值、术语定义）
- 数据流（输入字段 -> 计算 -> 输出字段）
- 交接信息（给 PM、占星师、SDE 对齐）

它不直接参与运行，但决定团队对“系统应该怎么工作”的共识。

## 2. 端到端流程

1. 上传文本
- 路由：`POST /upload`
- 文件：`behavioral-calendar/app/api/upload.py`

2. 解析 `zz.txt` 为结构化 profile
- 文件：`behavioral-calendar/app/core/jh_report_parser.py`
- 函数：`parse_report_text(text, today)`

3. 存储 profile
- 文件：`behavioral-calendar/app/storage/profile_store.py`
- 路径：`behavioral-calendar/storage/profiles/{file_id}.json`

4. 逐日评分（通常生成 30 天）
- 文件：`behavioral-calendar/app/core/scoring.py`
- 函数：`score_day(parsed_profile, d)`

5. 页面渲染
- 日历页：`behavioral-calendar/app/templates/calendar.html`
- 单日页：`behavioral-calendar/app/templates/day.html`

## 3. 关键输入字段（来自 `zz.txt` + 动态天文）

### 3.1 静态解析字段（`jh_report_parser.py`）
- `natal_nakshatra_name: str`（本命星宿）
- `lagna_rasi: str`（上升星座）
- `natal_moon_rasi: str`（本命月亮星座）
- `dasha_maha: str`、`dasha_antar: str`
- `dasha_maha_house: int`、`dasha_antar_house: int`
- `planet_rasi: dict[str, str]`
- `planet_houses: dict[str, int]`
- `bav_rasi: dict`（当前主评分不依赖）

### 3.2 动态字段（`daily_features.py`）
- `transit_nakshatra`
- `moon_rasi`
- `planet_rasi`（当日七曜/行星位置）
- `planet_status`（含 `is_retrograde`）

## 4. v2.3 评分核心（当前实现）

文件：`behavioral-calendar/app/core/scoring.py`

### Step A. Dasha 基准分

由 MD/AD 关系（`1/1, 6/8, 5/9...`）查 `rules.yaml -> dasha_relative_matrix` 得 `base_score`。

### Step B. Tara 修正

`natal_nakshatra_name + transit_nakshatra -> tara_label`，再查 `tara_bala_modifiers` 得每个维度的 `tara_modifier`。

### Step C. Gochara 修正（Dual-Lagna + Vedha + Status）

对每个维度的关键行星：
- Dual-Lagna：`S_L` 与 `S_C` 加权得到 `S_raw`
- Vedha：命中且 `S_raw > 0` 时，强制清零
- Status：Dignity/Retrograde 得到倍率，`S_final = S_raw * status_multiplier`
- 汇总成维度 `gochara_modifier`

### Step D. v2.3 新公式（加权求和模型）

每个维度：

`daily_dynamic = 70 * tara_modifier * (1 + gochara_modifier * 2.0)`

`dim_score = dasha_component * 0.4 + daily_dynamic * 0.6`

再做 `clamp(5, 99)` 和四舍五入。

其中：
- `dasha_component = base_score`
- 流年放大系数 `2.0` 来自 `score_model.gochara_amplifier`

### Step E. 总分聚合

总分公式保持不变：

`total_index = clamp(max(dim_scores)*0.3 + mean(dim_scores)*0.7, 5, 99)`

## 5. 信号灯（v2.3）

`classify_signal(total_index, tara_label, rules)`：

1. 一票否决：
- `Naidhana` -> 直接 `red`

2. 阈值：
- `green`: `score >= 75`
- `yellow`: `60 <= score < 75`
- `red`: `< 60`

3. 阻碍星宿封顶：
- `Vipat` / `Pratyari` 默认最高到 `yellow`
- 但当 `score >= 85` 可强制 `green`

配置来源：`rules.yaml -> signal_thresholds`

## 6. 当前规则配置位置

文件：`behavioral-calendar/app/rules/rules.yaml`

关键段：
- `dasha_relative_matrix`
- `score_model`（`dasha_weight`, `daily_dynamic_weight`, `daily_dynamic_baseline`, `gochara_amplifier`）
- `signal_thresholds`
- `dual_lagna_weights`
- `gochara_rules`
- `status_rules`
- `tara_bala_modifiers`
- `dimension_weights`

## 7. 输出给 UI 的关键字段

`score_day` 返回里主要给前端用：
- `scores.total_index`
- `scores.dimensions`
- `scores.deltas`（由 `calendar.py` 注入：今日 - 昨日）
- `scores.dimension_breakdown`（含 dasha/daily_dynamic/gochara 放大后的中间值）
- `scores.score_model`
- `signal`
- `summary_llm`
- `astrological_triggers.obstruction`
- `astrological_triggers.key_transits`
- `components.*`（术语映射、双语标签、状态详情）

## 8. 当前版本说明

本文件对应当前代码实现的 v2.3 逻辑，不是历史方案说明。
