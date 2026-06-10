# 世界杯预测项目交接摘要

更新时间：2026-06-10

## 1. 项目背景

- 目标：对足球比赛胜平负进行预测。
- 当前聚焦：`2018` 与 `2022` 男足世界杯数据，用来搭建和验证实验框架。
- 当前口径已经明确为：
  - **版本 B**
  - 允许使用世界杯进行中的滚动状态信息
  - 但对于揭幕阶段这类“赛内状态尚未产生”的比赛，要回退到更合适的赛前分支

## 2. 当前核心数据资产

### 比赛与标签

- [world_cup_match_results_2018_2022.csv](/Users/evelynfeng/Documents/gaming/world_cup_match_results_2018_2022.csv)
- [world_cup_matches_seed_2018_2022.csv](/Users/evelynfeng/Documents/gaming/world_cup_matches_seed_2018_2022.csv)
- 这两张表已经覆盖：
  - `2018` 世界杯 `64` 场
  - `2022` 世界杯 `64` 场
  - 合计 `128` 场

### 当前主特征表

- [world_cup_matches_features_elo_form.csv](/Users/evelynfeng/Documents/gaming/world_cup_matches_features_elo_form.csv)
- 目前已经包含：
  - `Elo`
  - `FIFA rank`
  - 最近 5 场 form
  - 休息天数
  - 洲别组合
  - 球员状态特征
  - `squad value`
  - 稀疏覆盖的 `xG/xGA`

### 关键脚本

- [build_statsbomb_world_cup_matches.py](/Users/evelynfeng/Documents/gaming/build_statsbomb_world_cup_matches.py)
- [build_world_cup_model_seed.py](/Users/evelynfeng/Documents/gaming/build_world_cup_model_seed.py)
- [build_world_cup_pre_match_features.py](/Users/evelynfeng/Documents/gaming/build_world_cup_pre_match_features.py)
- [build_world_cup_player_status_features.py](/Users/evelynfeng/Documents/gaming/build_world_cup_player_status_features.py)
- [build_world_cup_squad_values.py](/Users/evelynfeng/Documents/gaming/build_world_cup_squad_values.py)
- [train_world_cup_baseline.py](/Users/evelynfeng/Documents/gaming/train_world_cup_baseline.py)
- [run_world_cup_version_b_experiments.py](/Users/evelynfeng/Documents/gaming/run_world_cup_version_b_experiments.py)
- [run_world_cup_version_b_adaptive_experiments.py](/Users/evelynfeng/Documents/gaming/run_world_cup_version_b_adaptive_experiments.py)
- [predict_world_cup_version_b_adaptive.py](/Users/evelynfeng/Documents/gaming/predict_world_cup_version_b_adaptive.py)

## 3. 已接入的主要特征

### 长期实力层

- `team_a_elo`
- `team_b_elo`
- `elo_diff`
- `team_a_fifa_rank`
- `team_b_fifa_rank`
- `fifa_rank_diff`

### 近期状态层

- `team_a_last5_points`
- `team_b_last5_points`
- `last5_points_diff`
- `goals_for_diff`
- `goals_against_diff`
- `last5_goal_diff_gap`
- `rest_days_diff`

### 球员状态层

- `top11_rating_diff`
- `top11_minutes_diff`
- `attack_core_form_diff`
- `gk_form_diff`
- `starts_stability_diff`
- `key_absence_diff`

### 阵容身价层

- `team_a_squad_value`
- `team_b_squad_value`
- `squad_value_diff`

### 稀疏 xG 层

- `team_a_avg_xg_last5`
- `team_b_avg_xg_last5`
- `xg_diff`
- `team_a_avg_xga_last5`
- `team_b_avg_xga_last5`
- `xga_diff`

## 4. 当前数据覆盖情况

### 球员状态

- 本地完整可用 StatsBomb `events` 文件：`52`
- 带 `top11_rating_diff / top11_minutes_diff` 的比赛：大约 `36` 场

### squad value

- `127 / 128` 场已覆盖
- 还缺 `3` 场
- 缺失集中在 `Saudi Arabia`
- 原因是球员名字转写匹配仍不完整

### xG / xGA

- `team_a_avg_xg_last5 / team_b_avg_xg_last5`：`36` 场
- `xg_diff / xga_diff`：`33` 场
- 目前仍属于稀疏特征

## 5. 已跑出的关键实验结论

### A. 单一 baseline 口径

- 只用基础特征时，概率质量一般。
- 在加入：
  - `top11_rating_diff`
  - `top11_minutes_diff`
  - `squad_value_diff`
 之后，概率质量明显提升。

### B. 版本 B 总体结论

- 版本 B 定义：
  - 用 `2018` 世界杯作为历史训练底座
  - 对 `2022` 世界杯 `64` 场比赛按日期逐场滚动训练和预测
  - 允许使用世界杯进行中的滚动状态特征

- 当前最佳单一配置：
  - `player_state_squad_value`
  - 指标：
    - `accuracy = 0.453`
    - `log loss = 1.667`
    - `Brier = 0.764`

- `xG/xGA` 在当前覆盖率下**没有形成稳定正增益**
  - 所以不建议直接并入默认 baseline

### C. 分阶段结论

- 小组赛中：
  - `player_state_squad_value` 概率质量最好
- 淘汰赛中：
  - `player_state_squad_value` 和 `player_state` 都优于 `base_form`
- 但淘汰赛样本只有 `16` 场
  - 适合看方向
  - 不适合过度解释

### D. 强弱分层结论

- 按 `2022` 评估窗口里的 `abs(elo_diff)` 分桶：
  - `close`: `abs(elo_diff) <= 75.735`
  - `medium`: `75.735 < abs(elo_diff) <= 218.435`
  - `lopsided`: `abs(elo_diff) > 218.435`

- 当前观察：
  - `close` 比赛里，`base_form` 更稳
  - `medium` 比赛里，状态 + 身价特征更有价值
  - `lopsided` 比赛里，简单模型更稳

### E. 自适应版本 B 结论

- 已实现自适应策略实验
- 当前最像“可落地默认策略”的是：
  - `close` 用 `base_form`
  - `medium` 用 `player_state_squad_value_xg`
  - `lopsided` 用 `base_form`

- 这个策略对应：
  - `adaptive_base_svgxg`
  - 指标：
    - `accuracy = 0.500`
    - `log loss = 1.617`
    - `Brier = 0.711`

- 如果只看 `log loss`，`adaptive_best_bucket` 更低：
  - `log loss = 1.602`
- 但从整体均衡性和可解释性上，`adaptive_base_svgxg` 更像当前推荐默认值

## 6. 当前“推荐默认策略”

### 对 `2022` 这类版本 B 场景

- 优先使用：
  - **自适应版本 B**
  - 具体脚本：
    - [predict_world_cup_version_b_adaptive.py](/Users/evelynfeng/Documents/gaming/predict_world_cup_version_b_adaptive.py)
- 当前默认策略：
  - `adaptive_base_svgxg`

### 对揭幕阶段 / 本届尚无赛内状态的新比赛

- 不要机械套版本 B 的赛内状态分支
- 应回退到：
  - 赛前分支
  - 以 `Elo + 近期 form + rest days + 基础上下文` 为主

## 7. 已生成的重要结果文件

- [world_cup_experiment_comparison.md](/Users/evelynfeng/Documents/gaming/world_cup_experiment_comparison.md)
- [world_cup_version_b_experiment_results.md](/Users/evelynfeng/Documents/gaming/world_cup_version_b_experiment_results.md)
- [world_cup_version_b_stage_breakdown.md](/Users/evelynfeng/Documents/gaming/world_cup_version_b_stage_breakdown.md)
- [world_cup_version_b_strength_breakdown.md](/Users/evelynfeng/Documents/gaming/world_cup_version_b_strength_breakdown.md)
- [world_cup_version_b_adaptive_results.md](/Users/evelynfeng/Documents/gaming/world_cup_version_b_adaptive_results.md)

## 8. 当前经验教训

### 1. 样本很少，不能迷信单次 split

- `128` 场样本非常少
- 单次切分极容易高估某些特征
- 逐场滚动评估比单次留出更可信

### 2. 足球平局很多，必须做三分类

- 不要偷懒做简单二分类
- `主胜 / 平 / 客胜` 才是合理目标

### 3. 概率质量比 accuracy 更重要

- `accuracy` 很容易误导
- 当前项目应优先看：
  - `log loss`
  - `Brier`

### 4. 复杂特征不一定总是更强

- `xG` 在直觉上很强
- 但在当前覆盖率下是噪声
- 是否有用，必须通过实验验证

### 5. 特征有“适用场景”

- 同一组特征，在：
  - 小组赛
  - 淘汰赛
  - 势均力敌比赛
  - 强弱悬殊比赛
 里的效果并不一样

### 6. 名字匹配是一个实际瓶颈

- `squad value` 最大的工程问题不是模型
- 而是跨数据源名字转写、国家别名、姓名顺序

### 7. 揭幕阶段不能硬套赛内状态

- 版本 B 的前提是“杯赛内状态已经开始形成”
- 对第一轮最早几场比赛，这个前提不成立
- 需要切回赛前模型

## 9. 如果后面继续，最自然的下一步

优先顺序建议：

1. 补齐 `Saudi Arabia` 的球员匹配
2. 补更多 StatsBomb `events`
3. 覆盖更多 `xG/xGA` 与球员状态样本
4. 再重跑版本 B、自适应策略和分层实验

## 10. 一句话结论

- 当前项目已经从“想法讨论”进入到“有数据、有特征、有滚动评估、有自适应策略”的阶段。
- 当前最值得保留的核心认知是：
  - **中等强弱差距的比赛最适合吃状态/身价特征**
  - **极接近或极悬殊的比赛，简单模型反而更稳**
  - **默认预测策略应优先使用自适应版本 B，而不是单一固定模型**
