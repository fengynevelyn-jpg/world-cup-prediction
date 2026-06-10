# 世界杯版本 B 强弱分层结果

更新时间：2026-06-10

口径：按 `2022` 评估窗口里的 `abs(elo_diff)` 分位数分桶。

- `close`: `abs(elo_diff) <= 75.735`
- `medium`: `75.735 < abs(elo_diff) <= 218.435`
- `lopsided`: `abs(elo_diff) > 218.435`

| preset | strength_bucket | evaluated_matches | accuracy | log_loss | brier |
|---|---|---:|---:|---:|---:|
| all_signals | close | 16 | 0.375 | 2.217 | 0.953 |
| all_signals | lopsided | 16 | 0.562 | 2.019 | 0.706 |
| all_signals | medium | 32 | 0.500 | 1.484 | 0.701 |
| base_form | close | 16 | 0.500 | 2.169 | 0.871 |
| base_form | lopsided | 16 | 0.500 | 1.564 | 0.646 |
| base_form | medium | 32 | 0.438 | 1.714 | 0.790 |
| player_state | close | 16 | 0.438 | 2.092 | 0.893 |
| player_state | lopsided | 16 | 0.562 | 1.609 | 0.636 |
| player_state | medium | 32 | 0.375 | 1.723 | 0.794 |
| player_state_squad_value | close | 16 | 0.312 | 2.065 | 0.968 |
| player_state_squad_value | lopsided | 16 | 0.500 | 1.779 | 0.761 |
| player_state_squad_value | medium | 32 | 0.500 | 1.411 | 0.664 |
| player_state_squad_value_xg | close | 16 | 0.375 | 2.105 | 0.965 |
| player_state_squad_value_xg | lopsided | 16 | 0.438 | 2.048 | 0.819 |
| player_state_squad_value_xg | medium | 32 | 0.500 | 1.367 | 0.665 |
| player_state_xg | close | 16 | 0.438 | 2.129 | 0.911 |
| player_state_xg | lopsided | 16 | 0.500 | 1.849 | 0.676 |
| player_state_xg | medium | 32 | 0.375 | 1.725 | 0.786 |
