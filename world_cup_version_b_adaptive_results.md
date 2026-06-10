# 世界杯版本 B 自适应策略结果

更新时间：2026-06-10

口径：先按 `abs(elo_diff)` 把比赛分成 `close / medium / lopsided`，再为每个桶选择不同 preset。

| strategy | description | close | medium | lopsided | evaluated_matches | accuracy | log_loss | brier |
|---|---|---|---|---|---:|---:|---:|---:|
| adaptive_best_bucket | 每个强弱桶单独拿当前 log loss 最优 preset | player_state_squad_value | player_state_squad_value_xg | player_state | 64 | 0.469 | 1.602 | 0.733 |
| adaptive_base_svgxg | close/lopsided 用 base_form，medium 用 player_state_squad_value_xg | base_form | player_state_squad_value_xg | base_form | 64 | 0.500 | 1.617 | 0.711 |
| adaptive_base_svg | close/lopsided 用 base_form，medium 用 player_state_squad_value | base_form | player_state_squad_value | base_form | 64 | 0.500 | 1.639 | 0.711 |

## 当前判断

- 当前最稳的自适应策略是 `adaptive_best_bucket`。
- 它的指标是：`accuracy 0.469`，`log loss 1.602`，`Brier 0.733`。
