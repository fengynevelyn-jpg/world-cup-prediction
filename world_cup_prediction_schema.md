# 世界杯胜平负预测实验整理

## 1. Elo 是什么

Elo 是一种给球队或选手打“动态实力分”的方法，最早用于国际象棋，也很适合足球。

核心思想：

- 每支球队都有一个当前分数
- 强队赢弱队，分数只小幅上涨
- 弱队赢强队，分数会大幅上涨
- 平局也会让双方分数变化

所以，`Elo` 可以理解成一种比静态排名更有用的“实时实力值”。

在足球预测里，最常用的不是单独看某队 Elo，而是看两队差值：

- `elo_diff = team_a_elo - team_b_elo`

这个变量通常很有预测力，因为它把长期实力浓缩成了一个数字。

## 2. 这次实验建议怎么定义

建议目标：

- 预测 `90分钟内` 的 `主胜 / 平 / 客胜`

这里的“主客”在世界杯里可以理解为：

- `team_a`
- `team_b`

不要先把加时赛、点球大战混进去，不然标签会变脏。

## 3. 建表原则

只保留 `赛前可知` 信息。

最稳的做法是：

- 先记录 `team_a` 和 `team_b` 各自的数据
- 再派生差值字段

## 4. 推荐字段

### 4.1 比赛基础信息

- `match_id`
- `match_date`
- `tournament`
- `stage`
- `is_knockout`
- `team_a`
- `team_b`

说明：

- `stage` 可取 `group / round_of_16 / quarterfinal / semifinal / final`
- `is_knockout` 可取 `0/1`

### 4.2 长期实力字段

- `team_a_elo`
- `team_b_elo`
- `elo_diff`
- `team_a_fifa_rank`
- `team_b_fifa_rank`
- `fifa_rank_diff`
- `team_a_squad_value`
- `team_b_squad_value`
- `squad_value_diff`

说明：

- `elo_diff` 通常比单看 FIFA 排名更稳定
- `fifa_rank_diff = team_b_fifa_rank - team_a_fifa_rank`
- 因为排名越小越强，所以这个方向要统一

### 4.3 近期球队状态

- `team_a_last5_points`
- `team_b_last5_points`
- `last5_points_diff`
- `team_a_last5_goals_for`
- `team_b_last5_goals_for`
- `goals_for_diff`
- `team_a_last5_goals_against`
- `team_b_last5_goals_against`
- `goals_against_diff`
- `team_a_last5_goal_diff`
- `team_b_last5_goal_diff`
- `last5_goal_diff_gap`

说明：

- `last5_points` 可以按 `胜=3, 平=1, 负=0` 统计
- 如果你觉得 5 场太短，也可以改成 10 场

### 4.4 近期球员状态聚合字段

这部分不要一开始就做全量球员明细，先聚合成球队级变量。

- `team_a_top11_avg_rating_last5`
- `team_b_top11_avg_rating_last5`
- `top11_rating_diff`
- `team_a_top11_avg_minutes_last5`
- `team_b_top11_avg_minutes_last5`
- `top11_minutes_diff`
- `team_a_attack_core_form_score`
- `team_b_attack_core_form_score`
- `attack_core_form_diff`
- `team_a_gk_form_score`
- `team_b_gk_form_score`
- `gk_form_diff`
- `team_a_recent_starts_stability`
- `team_b_recent_starts_stability`
- `starts_stability_diff`

说明：

- `top11_avg_rating_last5`：预计主力 11 人近 5 场平均评分
- `top11_avg_minutes_last5`：预计主力 11 人近 5 场平均出场时间
- `attack_core_form_score`：前场 2 到 3 名核心球员的状态分
- `gk_form_score`：主力门将状态分，建议单独保留
- `recent_starts_stability`：近几场首发阵容是否稳定

### 4.5 伤停和可用性

- `team_a_key_absence_score`
- `team_b_key_absence_score`
- `key_absence_diff`
- `team_a_rest_days`
- `team_b_rest_days`
- `rest_days_diff`

说明：

- `key_absence_score` 可以先人工定义
- 例如：头号球星缺阵记 `1.5`，主力门将记 `1.2`，普通核心主力记 `1.0`

### 4.6 上下文信息

- `confederation_a`
- `confederation_b`
- `confederation_pair`
- `same_confederation_flag`

说明：

- 比如 `UEFA vs CONMEBOL`
- 有时这类变量会补充风格和强弱结构信息

## 5. 标签字段

- `target_result_90m`

建议编码：

- `0 = team_a_win`
- `1 = draw`
- `2 = team_b_win`

如果以后想做二级任务，也可以另外加：

- `target_qualify`

但第一版先不要混在一起。

## 6. 最小可用版本

如果你想先做最小实验，我建议先只保留下面这些：

- `elo_diff`
- `fifa_rank_diff`
- `last5_points_diff`
- `last5_goal_diff_gap`
- `attack_core_form_diff`
- `gk_form_diff`
- `key_absence_diff`
- `rest_days_diff`
- `stage`
- `is_knockout`
- `target_result_90m`

这一版已经能跑出一个很像样的 baseline。

## 7. 一个样例

```text
match_id: 2022_qf_arg_ned
match_date: 2022-12-09
tournament: FIFA World Cup
stage: quarterfinal
is_knockout: 1
team_a: Argentina
team_b: Netherlands
team_a_elo: 2143
team_b_elo: 2054
elo_diff: 89
team_a_fifa_rank: 3
team_b_fifa_rank: 8
fifa_rank_diff: 5
team_a_last5_points: 12
team_b_last5_points: 11
last5_points_diff: 1
team_a_attack_core_form_score: 8.6
team_b_attack_core_form_score: 7.9
attack_core_form_diff: 0.7
team_a_gk_form_score: 7.8
team_b_gk_form_score: 7.5
gk_form_diff: 0.3
team_a_key_absence_score: 0
team_b_key_absence_score: 0
key_absence_diff: 0
target_result_90m: 1
```

## 8. 实验建议

第一版建模建议顺序：

1. 只用 `Elo + 排名 + 最近战绩`
2. 再加入 `球员状态聚合字段`
3. 再加入 `伤停 / 门将 / 核心球员` 修正

这样你比较容易看出：

- 球员状态到底有没有增量价值
- 关键球员变量是不是比球队近期战绩更有效
- 哪类特征只是噪声

## 9. 结论

如果只说优先级，我建议是：

1. `Elo`
2. 近期球队状态
3. 关键球员状态
4. 伤停和门将
5. 其他背景变量

其中，`Elo` 是长期实力基线，`近期状态` 和 `关键球员状态` 是对这个基线做短期修正。
