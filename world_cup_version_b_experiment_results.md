# 世界杯版本 B 实验结果

更新时间：2026-06-10

口径：用 `2018` 世界杯作为历史训练底座，并在 `2022-11-20` 到 `2022-12-18` 之间逐场滚动训练和预测；允许使用世界杯进行中的滚动状态特征。

| preset | description | evaluated_matches | accuracy | log_loss | brier | feature_count |
|---|---|---:|---:|---:|---:|---:|
| player_state_squad_value | Player-state preset + squad value | 64 | 0.453 | 1.667 | 0.764 | 37 |
| player_state_squad_value_xg | Player-state + squad value + rolling xG/xGA | 64 | 0.453 | 1.722 | 0.778 | 41 |
| player_state | Base + top11 rating/minutes | 64 | 0.438 | 1.787 | 0.779 | 35 |
| base_form | Elo + FIFA + recent form + stage/confederation | 64 | 0.469 | 1.790 | 0.774 | 31 |
| all_signals | Player-state + squad value + rolling xG/xGA + all current player-state fields | 64 | 0.484 | 1.801 | 0.765 | 49 |
| player_state_xg | Base + top11 rating/minutes + rolling xG/xGA | 64 | 0.422 | 1.857 | 0.790 | 39 |

## 当前判断

- 如果版本 B 以概率质量为主，当前最稳的 preset 是 `player_state_squad_value`。
- 它的指标是：`accuracy 0.453`，`log loss 1.667`，`Brier 0.764`。

## 分阶段补充

- 分层结果见：
  - `/Users/evelynfeng/Documents/gaming/world_cup_version_b_stage_breakdown.md`
- 小组赛里，`player_state_squad_value` 的概率质量最好：
  - `log loss 1.815`
  - `Brier 0.829`
- 淘汰赛里，`player_state_squad_value` 和 `player_state` 都明显优于 `base_form`：
  - `player_state_squad_value log loss 1.221`
  - `player_state log loss 1.222`
  - `base_form log loss 1.413`
- 但这里要保守解释：
  - 淘汰赛只有 `16` 场
  - 半决赛只有 `2` 场
  - 决赛只有 `1` 场
  - 所以具体到 `quarterfinal / semifinal / final` 的数值更适合看方向，不适合下强结论

## 强弱分层补充

- 强弱分层结果见：
  - `/Users/evelynfeng/Documents/gaming/world_cup_version_b_strength_breakdown.md`
- 这里用的是 `2022` 评估窗口里的 `abs(elo_diff)` 分位数分桶：
  - `close`: `abs(elo_diff) <= 75.735`
  - `medium`: `75.735 < abs(elo_diff) <= 218.435`
  - `lopsided`: `abs(elo_diff) > 218.435`
- 当前最有用的结论：
  - `close` 比赛里，`base_form` 反而最稳：
    - `log loss 2.169`
    - `Brier 0.871`
  - `medium` 比赛里，带状态和身价的配置明显更强：
    - `player_state_squad_value log loss 1.411`
    - `player_state_squad_value_xg log loss 1.367`
  - `lopsided` 比赛里，简单配置更稳：
    - `base_form log loss 1.564`
    - `player_state log loss 1.609`
- 所以按当前样本看：
  - 真正有增量价值的区间，更像是“中等强弱差距”的比赛
  - 非常接近的比赛和非常悬殊的比赛，复杂特征暂时没有稳定压过基础特征
- 这里也要保守解释：
  - `close` 只有 `16` 场
  - `lopsided` 只有 `16` 场
  - `medium` 也只有 `32` 场
  - 所以这更适合当下一轮特征设计的方向，而不是最终策略

## 自适应策略补充

- 自适应结果见：
  - `/Users/evelynfeng/Documents/gaming/world_cup_version_b_adaptive_results.md`
- 和当前最佳单一配置 `player_state_squad_value` 相比：
  - 单一配置：
    - `accuracy 0.453`
    - `log loss 1.667`
    - `Brier 0.764`
  - `adaptive_best_bucket`：
    - `accuracy 0.469`
    - `log loss 1.602`
    - `Brier 0.733`
  - `adaptive_base_svgxg`：
    - `accuracy 0.500`
    - `log loss 1.617`
    - `Brier 0.711`
- 这说明：
  - 如果只追求 `log loss`，当前最好的是 `adaptive_best_bucket`
  - 如果希望 `accuracy / Brier / log loss` 更均衡，`adaptive_base_svgxg` 其实更有实用价值
- 当前最像“可落地默认策略”的版本是：
  - `close` 用 `base_form`
  - `medium` 用 `player_state_squad_value_xg`
  - `lopsided` 用 `base_form`
