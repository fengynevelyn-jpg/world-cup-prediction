# 世界杯预测实验对比

更新时间：2026-06-10

## 数据状态

- 总比赛数：`128`
- 已有 `Elo` / `FIFA rank` / 最近 5 场 / `rest days`：`128` 场全覆盖
- 已有球员状态 `events` 文件：`52`
- 已有完整可用 `events` 文件：`52`
- 带 `top11_rating_diff` / `top11_minutes_diff` 的比赛：`36`
- 同时带全部当前球员状态列的比赛：`30`
- 已有 `squad_value_diff` 的比赛：`127 / 128`

## 对比场景

### 1. 无球员状态

- 数值特征：
  - `elo_diff`
  - `fifa_rank_diff`
  - `last5_points_diff`
  - `goals_for_diff`
  - `goals_against_diff`
  - `last5_goal_diff_gap`
  - `rest_days_diff`
- 类别特征：
  - `stage`
  - `confederation_pair`
- 结果：
  - `accuracy = 0.538`
  - `log loss = 1.254`
  - `Brier = 0.549`

### 2. 收敛后的球员状态

- 在上面基础上增加：
  - `top11_rating_diff`
  - `top11_minutes_diff`
- 覆盖率：
  - `36 / 128` 场
- 结果：
  - `accuracy = 0.615`
  - `log loss = 1.131`
  - `Brier = 0.520`

### 3. 收敛后的球员状态 + squad value

- 在场景 2 基础上增加：
  - `squad_value_diff`
- 覆盖率：
  - `127 / 128` 场
- 结果：
  - `accuracy = 0.615`
  - `log loss = 1.073`
  - `Brier = 0.510`

### 4. 全量当前球员状态

- 在上面基础上增加：
  - `attack_core_form_diff`
  - `gk_form_diff`
  - `starts_stability_diff`
  - `key_absence_diff`
- 覆盖率：
  - `30 / 128` 场全部非空
- 结果：
  - `accuracy = 0.654`
  - `log loss = 1.255`
  - `Brier = 0.558`

## 当前判断

- 如果看 `accuracy`，全量球员状态最高。
- 如果看更适合概率预测的 `log loss` 和 `Brier`，当前最稳的是：
  - `top11_rating_diff`
  - `top11_minutes_diff`
- `squad_value_diff` 现在已经是有效增益项：
  - 它没有继续提高 `accuracy`
  - 但把 `log loss` 从 `1.131` 压到了 `1.073`
  - 把 `Brier` 从 `0.520` 压到了 `0.510`
- 所以当前 baseline 的合理默认口径是：
  - `Elo`
  - `FIFA rank`
  - 最近 5 场 form
  - `top11_rating_diff`
  - `top11_minutes_diff`
  - `squad_value_diff`

## 版本 B

- 口径：
  - 用 `2018` 世界杯作为历史训练底座
  - 对 `2022` 世界杯 `64` 场比赛按日期逐场滚动训练和预测
  - 允许使用世界杯进行中的滚动状态特征
- 当前 `xG` 特征覆盖：
  - `team_a_avg_xg_last5` / `team_b_avg_xg_last5`：`36` 场
  - `xg_diff` / `xga_diff`：`33` 场
- 结果明细见：
  - `/Users/evelynfeng/Documents/gaming/world_cup_version_b_experiment_results.md`
- 当前版本 B 下的主要结论：
  - `base_form` 的 `accuracy = 0.469`
  - `player_state` 的 `accuracy = 0.438`
  - `player_state_squad_value` 的 `accuracy = 0.453`
  - `player_state_xg` 的 `accuracy = 0.422`
  - `player_state_squad_value_xg` 的 `accuracy = 0.453`
  - `all_signals` 的 `accuracy = 0.469`
  - 如果按概率质量看，版本 B 最稳的是 `player_state_squad_value`
  - 它的 `log loss = 1.667`，优于：
    - `base_form = 1.790`
    - `player_state = 1.787`
    - `player_state_xg = 1.857`
    - `player_state_squad_value_xg = 1.722`
    - `all_signals = 1.785`
- 这说明在版本 B 里：
  - `squad_value_diff` 仍然是有效增益
  - `top11_rating_diff + top11_minutes_diff` 单独加进去还不够稳
  - 但和 `squad_value_diff` 组合后，概率质量变得更好
  - 当前覆盖率下，`xG/xGA` 还没有形成稳定正增益
  - 所以现阶段不建议把 `xg_diff / xga_diff` 并入默认 baseline
- 如果继续细分到比赛阶段：
  - 小组赛里，`player_state_squad_value` 的 `log loss` 最好，为 `1.815`
  - 淘汰赛里，`player_state_squad_value` 和 `player_state` 都明显优于 `base_form`
  - 但淘汰赛样本只有 `16` 场，所以这部分更适合看方向，不适合过度解释
- 如果继续细分到赛前强弱差距：
  - `close` 和 `lopsided` 比赛里，`base_form` 更稳
  - `medium` 比赛里，`player_state_squad_value` / `player_state_squad_value_xg` 更强
  - 基于这个分层做出的自适应版本 B，比当前最佳单一配置更稳
  - 当前最像默认策略的是：
    - `close` 用 `base_form`
    - `medium` 用 `player_state_squad_value_xg`
    - `lopsided` 用 `base_form`

## 说明

- `squad_value_diff` 目前只有 `3` 场比赛仍缺失，全部和 `Saudi Arabia` 的匹配覆盖不足有关。
- 球员状态层目前仍是稀疏特征，后续如果继续补 `events`，这张对比表值得重跑一次。
