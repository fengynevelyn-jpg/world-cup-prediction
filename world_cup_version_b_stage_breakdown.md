# 世界杯版本 B 分阶段结果

更新时间：2026-06-10

口径：用 `2018` 训练底座，对 `2022` 比赛逐场滚动预测；按 `group/knockout` 和具体阶段拆分。

## Group vs Knockout

| preset | segment | evaluated_matches | accuracy | log_loss | brier |
|---|---|---:|---:|---:|---:|
| all_signals | group | 48 | 0.417 | 1.951 | 0.835 |
| all_signals | knockout | 16 | 0.688 | 1.350 | 0.556 |
| base_form | group | 48 | 0.417 | 1.916 | 0.835 |
| base_form | knockout | 16 | 0.625 | 1.413 | 0.593 |
| player_state | group | 48 | 0.375 | 1.975 | 0.852 |
| player_state | knockout | 16 | 0.625 | 1.222 | 0.562 |
| player_state_squad_value | group | 48 | 0.396 | 1.815 | 0.829 |
| player_state_squad_value | knockout | 16 | 0.625 | 1.221 | 0.570 |
| player_state_squad_value_xg | group | 48 | 0.396 | 1.880 | 0.839 |
| player_state_squad_value_xg | knockout | 16 | 0.625 | 1.249 | 0.596 |
| player_state_xg | group | 48 | 0.354 | 2.062 | 0.863 |
| player_state_xg | knockout | 16 | 0.625 | 1.242 | 0.570 |

## By Stage

| preset | stage | evaluated_matches | accuracy | log_loss | brier |
|---|---|---:|---:|---:|---:|
| all_signals | final | 1 | 0.000 | 2.343 | 1.477 |
| all_signals | group | 48 | 0.417 | 1.951 | 0.835 |
| all_signals | quarterfinal | 4 | 0.250 | 2.852 | 1.182 |
| all_signals | round_of_16 | 8 | 0.875 | 0.981 | 0.336 |
| all_signals | semifinal | 2 | 1.000 | 0.000 | 0.000 |
| all_signals | third_place | 1 | 1.000 | 0.000 | 0.000 |
| base_form | final | 1 | 0.000 | 7.268 | 1.994 |
| base_form | group | 48 | 0.417 | 1.916 | 0.835 |
| base_form | quarterfinal | 4 | 0.250 | 2.250 | 0.980 |
| base_form | round_of_16 | 8 | 0.750 | 0.792 | 0.446 |
| base_form | semifinal | 2 | 1.000 | 0.002 | 0.000 |
| base_form | third_place | 1 | 1.000 | 0.001 | 0.000 |
| player_state | final | 1 | 0.000 | 4.961 | 1.959 |
| player_state | group | 48 | 0.375 | 1.975 | 0.852 |
| player_state | quarterfinal | 4 | 0.250 | 2.066 | 0.923 |
| player_state | round_of_16 | 8 | 0.750 | 0.790 | 0.418 |
| player_state | semifinal | 2 | 1.000 | 0.001 | 0.000 |
| player_state | third_place | 1 | 1.000 | 0.001 | 0.000 |
| player_state_squad_value | final | 1 | 0.000 | 3.262 | 1.770 |
| player_state_squad_value | group | 48 | 0.396 | 1.815 | 0.829 |
| player_state_squad_value | quarterfinal | 4 | 0.250 | 2.504 | 1.047 |
| player_state_squad_value | round_of_16 | 8 | 0.750 | 0.782 | 0.395 |
| player_state_squad_value | semifinal | 2 | 1.000 | 0.001 | 0.000 |
| player_state_squad_value | third_place | 1 | 1.000 | 0.000 | 0.000 |
| player_state_squad_value_xg | final | 1 | 0.000 | 3.219 | 1.746 |
| player_state_squad_value_xg | group | 48 | 0.396 | 1.880 | 0.839 |
| player_state_squad_value_xg | quarterfinal | 4 | 0.250 | 2.497 | 1.040 |
| player_state_squad_value_xg | round_of_16 | 8 | 0.750 | 0.847 | 0.453 |
| player_state_squad_value_xg | semifinal | 2 | 1.000 | 0.001 | 0.000 |
| player_state_squad_value_xg | third_place | 1 | 1.000 | 0.000 | 0.000 |
| player_state_xg | final | 1 | 0.000 | 4.847 | 1.954 |
| player_state_xg | group | 48 | 0.354 | 2.062 | 0.863 |
| player_state_xg | quarterfinal | 4 | 0.250 | 2.074 | 0.889 |
| player_state_xg | round_of_16 | 8 | 0.750 | 0.841 | 0.451 |
| player_state_xg | semifinal | 2 | 1.000 | 0.001 | 0.000 |
| player_state_xg | third_place | 1 | 1.000 | 0.001 | 0.000 |
