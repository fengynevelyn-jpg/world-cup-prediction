# 世界杯预测实验数据源

## 已经落地到本地的数据

### 1. StatsBomb 公开世界杯比赛数据

来源：

- https://github.com/statsbomb/open-data
- https://statsbomb.com/news/statsbomb-release-free-2022-world-cup-data/

本地文件：

- `/Users/evelynfeng/Documents/gaming/statsbomb_competitions.json`
- `/Users/evelynfeng/Documents/gaming/data/statsbomb/matches/world_cup_2018_matches.json`
- `/Users/evelynfeng/Documents/gaming/data/statsbomb/matches/world_cup_2022_matches.json`

从这些文件已经整理出的表：

- `/Users/evelynfeng/Documents/gaming/world_cup_match_results_2018_2022.csv`
- `/Users/evelynfeng/Documents/gaming/world_cup_matches_seed_2018_2022.csv`

这些数据现在已经足够提供：

- 2018 世界杯全部 64 场比赛
- 2022 世界杯全部 64 场比赛
- 比赛日期
- 比赛阶段
- 主客队
- 90 分钟比分
- `target_result_90m`
- 球场
- 教练名
- 裁判名

### 2. 已写好的处理脚本

- `/Users/evelynfeng/Documents/gaming/build_statsbomb_world_cup_matches.py`
- `/Users/evelynfeng/Documents/gaming/build_world_cup_model_seed.py`
- `/Users/evelynfeng/Documents/gaming/download_statsbomb_world_cup_assets.py`

## 还缺但值得补的数据

### 1. FIFA 官方排名日期锚点

来源：

- https://inside.fifa.com/en/fifa-world-ranking/men

用途：

- `team_a_fifa_rank`
- `team_b_fifa_rank`
- `fifa_rank_diff`

说明：

- 这是官方来源
- 我们已经从 FIFA 页面的历史日期元数据确认了两届世界杯赛前最近一次男足排名发布日期：
  - `2018-06-07`
  - `2022-10-06`
- 官方页面对历史表格的自动化提取并不友好，所以实际落表时用了下方的历史快照页做归档抓取

### 2. 历史 FIFA 排名快照页（实际已用于建模）

来源：

- https://en.fifaranking.net/ranking/?d=2018-06-07
- https://en.fifaranking.net/ranking/?d=2022-10-06

本地文件：

- `/Users/evelynfeng/Documents/gaming/data/fifa/fifaranking_2018_06_07.html`
- `/Users/evelynfeng/Documents/gaming/data/fifa/fifaranking_2022_10_06.html`

用途：

- `team_a_fifa_rank`
- `team_b_fifa_rank`
- `fifa_rank_diff`

说明：

- 这是第三方历史快照站点，不是 FIFA 官方主站
- 但它保留了我们需要的两个赛前发布时间点的完整排名表
- 对这次实验来说，它足够适合作为 `2018` 与 `2022` 世界杯赛前排名输入

### 3. Elo

推荐做法：

- 不依赖第三方网页抄数
- 直接基于历史国家队比赛结果自己计算 Elo

这样更稳，因为：

- 口径可控
- 可以保证只用赛前信息
- 后续还能调参数，比如主场优势、平局修正、比赛重要性权重

如果只想先做 baseline，也可以先用第三方 Elo 表，但那会引入额外来源管理问题。

### 4. 球员与阵容层数据

优先来源：

- StatsBomb 事件数据和阵容数据

用途：

- 首发阵容
- 门将信息
- 射门和 `xG`
- 核心球员出场情况
- 近期比赛表现聚合

说明：

- 这部分已经有下载脚本
- 已经从 `events` 里做出了：
  - `top11_rating_diff`
  - `top11_minutes_diff`
  - `attack_core_form_diff`
  - `gk_form_diff`
  - `starts_stability_diff`
  - `key_absence_diff`
  - `team_a_avg_xg_last5`
  - `team_b_avg_xg_last5`
  - `xg_diff`
  - `team_a_avg_xga_last5`
  - `team_b_avg_xga_last5`
  - `xga_diff`
- 但当前 `events` 覆盖还不完整，所以 `xG/xGA` 和球员状态都属于稀疏特征

### 5. 阵容总身价（现已接入）

来源：

- 世界杯最终名单页：
  - https://en.wikipedia.org/wiki/2018_FIFA_World_Cup_squads
  - https://en.wikipedia.org/wiki/2022_FIFA_World_Cup_squads
- Transfermarkt 系球员市场价值数据集：
  - https://github.com/salimt/football-datasets

本地文件：

- `/Users/evelynfeng/Documents/gaming/data/world_cup_squads_2018.html`
- `/Users/evelynfeng/Documents/gaming/data/world_cup_squads_2022.html`
- `/Users/evelynfeng/Documents/gaming/data/player_profiles.csv`
- `/Users/evelynfeng/Documents/gaming/data/player_market_value.csv`
- `/Users/evelynfeng/Documents/gaming/world_cup_squad_player_values.csv`
- `/Users/evelynfeng/Documents/gaming/world_cup_team_squad_values.csv`

用途：

- `team_a_squad_value`
- `team_b_squad_value`
- `squad_value_diff`

说明：

- 这不是官方估值，而是第三方市场价值数据
- 当前做法不是直接抄“球队总身价榜”，而是：
  1. 先从世界杯最终名单页解析每队球员名单
  2. 再用球员姓名 + 出生日期去匹配市场价值数据集
  3. 对每名球员取世界杯开赛前最近一次市场价值
  4. 最后按队汇总成 `squad_value`
- 当前已经覆盖：
  - `127 / 128` 场比赛
  - 仍缺 `3` 场，全部与 `Saudi Arabia` 球员转写匹配不足有关

## 当前建议的最小数据路径

第一阶段先用已经拿到的比赛数据，再补两类信息：

1. 自己计算的 Elo
2. FIFA 排名快照

这样你就能先跑一个比较扎实的 baseline：

- `elo_diff`
- `fifa_rank_diff`
- `stage`
- `is_knockout`
- `target_result_90m`

第二阶段再加：

- 球员状态
- 门将状态
- 核心球员缺阵
- `xG`
- 继续补齐 `Saudi Arabia` 等低覆盖队伍的 squad value 匹配

## 现在你已经可以直接用的文件

- 比赛结果总表：`/Users/evelynfeng/Documents/gaming/world_cup_match_results_2018_2022.csv`
- 建模种子表：`/Users/evelynfeng/Documents/gaming/world_cup_matches_seed_2018_2022.csv`
- 当前特征总表：`/Users/evelynfeng/Documents/gaming/world_cup_matches_features_elo_form.csv`
- squad value 处理脚本：`/Users/evelynfeng/Documents/gaming/build_world_cup_squad_values.py`
- 训练脚本：`/Users/evelynfeng/Documents/gaming/train_world_cup_baseline.py`
