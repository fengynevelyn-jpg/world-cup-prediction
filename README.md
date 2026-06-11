# World Cup Prediction

An experimental football match prediction project built around the **2018** and **2022** men's FIFA World Cups.

This repository helps you build and evaluate a **pre-match football outcome prediction pipeline** for World Cup matches.

The main goal is simple:

- take match-level inputs that are known **before kickoff**
- turn them into structured features
- train baseline or adaptive models
- output **90-minute win / draw / loss probabilities**

The current modeling focus is a **Version B** setup:

- use historical World Cup matches as the training base
- allow in-tournament rolling state features when they exist
- compare simple priors against richer state-driven models
- prioritize probability quality over raw accuracy

## Who this is for

Use this repo if you want to:

- study how much signal Elo, recent form, FIFA rank, player state, squad value, or xG add
- build a reproducible World Cup prediction experiment
- compare simple baselines against richer feature sets
- generate probability predictions instead of only hard labels

This repo is probably **not** the right fit if you want:

- a production betting system
- bundled proprietary datasets
- a one-command fully automated data scraper for every source

## What is in this repo

- feature-building scripts for Elo, recent form, player-state proxies, optional squad value, and sparse xG/xGA
- baseline and adaptive prediction scripts
- a schema document and lightweight example/template CSVs

## What is intentionally excluded

This public repo does **not** bundle:

- raw third-party datasets
- locally generated feature tables
- experiment output tables
- internal handoff notes

That is intentional for both privacy and data-rights reasons.

## Quick start

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Read the schema:

- `world_cup_prediction_schema.md`

3. Start with the template or demo file:

- `world_cup_matches_template.csv`
- `world_cup_matches_example.csv`
- `world_cup_matches_demo.csv`

4. Run the lightweight baseline:

```bash
python3 train_world_cup_baseline.py \
  --input world_cup_matches_demo.csv \
  --output baseline_predictions.csv
```

What this gives you:

- a minimal end-to-end run
- multiclass `team_a_win / draw / team_b_win` probabilities
- a simple example of the expected input table shape

## Typical workflow

The usual workflow looks like this:

1. Gather or prepare match data and keep it local.
2. Build or fill a feature table using the schema in `world_cup_prediction_schema.md`.
3. Start with the baseline trainer on a small CSV.
4. Move on to the Version B experiment scripts when you want rolling in-tournament evaluation.
5. Use the adaptive predictor for future-match inference once your feature table is ready.

## What you need to prepare

At minimum, you should have:

- one CSV with one row per match
- a target column `target_result_90m` for labeled historical matches
- core pre-match features such as `elo_diff`, `fifa_rank_diff`, recent-form fields, and match context

If you want the richer workflow, you can also prepare:

- player-state proxies
- squad-value features
- sparse rolling `xG/xGA`

The full field list is documented in:

- `world_cup_prediction_schema.md`

## Data and compliance

Please read [world_cup_data_sources.md](world_cup_data_sources.md) before using the pipeline.

Short version:

- obtain third-party data yourself
- check and follow each source's license or terms
- attribute sources where required
- do not assume that a locally generated CSV is automatically safe to redistribute

## Repository layout

- `build_world_cup_pre_match_features.py`: builds Elo, recent form, FIFA rank, rest-day, and match-context features
- `build_world_cup_player_status_features.py`: builds rolling player-state and sparse xG/xGA features from event data
- `build_world_cup_squad_values.py`: derives squad-value features from local squad/value sources
- `train_world_cup_baseline.py`: trains a minimal multiclass baseline from a CSV
- `run_world_cup_version_b_experiments.py`: runs Version B walk-forward experiments
- `run_world_cup_version_b_adaptive_experiments.py`: evaluates adaptive model-selection strategies
- `predict_world_cup_version_b_adaptive.py`: predicts future matches with the current adaptive strategy
- `world_cup_prediction_schema.md`: field definitions and modeling notes

## Main entry points

- `build_world_cup_pre_match_features.py`
- `build_world_cup_player_status_features.py`
- `build_world_cup_squad_values.py`
- `train_world_cup_baseline.py`
- `run_world_cup_version_b_experiments.py`
- `run_world_cup_version_b_adaptive_experiments.py`
- `predict_world_cup_version_b_adaptive.py`
- `world_cup_prediction_schema.md`
- `world_cup_matches_template.csv`
- `world_cup_matches_example.csv`
- `world_cup_matches_demo.csv`

## Current modeling takeaway

The most practical setup so far is an adaptive Version B strategy:

- `close` matches: use `base_form`
- `medium` matches: use `player_state_squad_value_xg`
- `lopsided` matches: use `base_form`

This repo treats that as an experiment workflow, not a production forecasting system.

## Example commands

Train the minimal baseline:

```bash
python3 train_world_cup_baseline.py \
  --input world_cup_matches_demo.csv \
  --output baseline_predictions.csv
```

Run Version B walk-forward experiments:

```bash
python3 run_world_cup_version_b_experiments.py
```

Run adaptive-strategy experiments:

```bash
python3 run_world_cup_version_b_adaptive_experiments.py
```

Predict future matches with the current adaptive strategy:

```bash
python3 predict_world_cup_version_b_adaptive.py \
  --input your_feature_table.csv \
  --output predictions.csv
```

## Metrics

The project mainly tracks:

- `log loss`
- `Brier score`

Accuracy is reported, but it is not the primary decision criterion.

## License

- Open-source license: `MIT`
- Separate commercial terms: available on request through the repository contact channel
- Note: the MIT License already permits commercial use; a separate commercial license is an optional alternative for teams that need extra contractual terms

## Current limitations

- third-party raw data is intentionally not bundled
- some richer features are sparse and depend on local source coverage
- this is a small-sample World Cup experiment, so results can move around across evaluation setups
- opening matches often need a cleaner pre-tournament branch because current-tournament state does not exist yet

## 中文说明

这是一个基于 **2018** 和 **2022** 男足世界杯的实验性足球比赛预测项目。

它的核心用途很直接：

- 输入赛前就能知道的比赛信息
- 构造成结构化特征
- 训练胜 / 平 / 负三分类模型
- 输出 **90 分钟内** 的概率预测

当前仓库重点是 **Version B** 实验口径：

- 用历史世界杯比赛作为训练底座
- 在有条件时允许使用赛会进行中的滚动状态特征
- 对比简单先验和更丰富的状态特征
- 更重视概率质量，而不是只看准确率

### 适合谁来用

如果你想做下面这些事，这个仓库就是为你准备的：

- 研究 Elo、近期状态、FIFA 排名、球员状态、身价、xG 到底有没有预测增益
- 搭一个可复现的世界杯预测实验
- 比较简单 baseline 和更复杂特征组合
- 输出概率，而不只是拍一个输赢标签

如果你想要的是下面这些，这个仓库就不一定合适：

- 直接拿来做生产级投注系统
- 仓库里自带完整第三方数据
- 一键全自动抓取所有来源数据

### 快速开始

1. 安装依赖：

```bash
pip install -r requirements.txt
```

2. 先看字段说明：

- `world_cup_prediction_schema.md`

3. 再从模板或示例数据开始：

- `world_cup_matches_template.csv`
- `world_cup_matches_example.csv`
- `world_cup_matches_demo.csv`

4. 运行最小 baseline：

```bash
python3 train_world_cup_baseline.py \
  --input world_cup_matches_demo.csv \
  --output baseline_predictions.csv
```

这一步跑通后，你会得到：

- 一个最小可运行闭环
- `主胜 / 平 / 客胜` 三分类概率输出
- 一份很直观的输入表格式参考

### 典型使用流程

1. 先把比赛数据准备在本地。
2. 按 `world_cup_prediction_schema.md` 把字段整理成一张特征表。
3. 先用 baseline 脚本跑一个小样本。
4. 如果要做赛会进行中的滚动实验，再用 Version B 脚本。
5. 如果要预测未来比赛，再用自适应预测脚本。

### 你至少需要准备什么

最少要有：

- 一张按“每场比赛一行”整理的 CSV
- 历史比赛的 `target_result_90m`
- 一些核心赛前特征，比如 `elo_diff`、`fifa_rank_diff`、近期状态和比赛上下文

如果你想走更完整的实验链路，还可以再补：

- 球员状态代理特征
- 阵容总身价
- 稀疏滚动 `xG/xGA`

完整字段说明在：

- `world_cup_prediction_schema.md`

### 仓库包含什么

- Elo、近期状态、球员状态代理特征、可选身价特征、稀疏 `xG/xGA` 的特征构建脚本
- baseline 和 adaptive 预测脚本
- 字段 schema、模板 CSV、示例 CSV

### 目录说明

- `build_world_cup_pre_match_features.py`：构建 Elo、近期状态、FIFA 排名、休息天数和比赛上下文特征
- `build_world_cup_player_status_features.py`：从事件数据构建滚动球员状态和稀疏 `xG/xGA`
- `build_world_cup_squad_values.py`：从本地名单与球员价值数据生成阵容价值特征
- `train_world_cup_baseline.py`：训练最小三分类 baseline
- `run_world_cup_version_b_experiments.py`：运行 Version B 滚动实验
- `run_world_cup_version_b_adaptive_experiments.py`：评估自适应策略
- `predict_world_cup_version_b_adaptive.py`：用当前自适应策略预测未来比赛
- `world_cup_prediction_schema.md`：字段定义和建模说明

### 仓库不包含什么

这个公开仓库**不直接附带**：

- 第三方原始数据
- 本地生成的完整特征表
- 实验结果表
- 内部交接笔记

这样做主要是为了更稳地控制隐私暴露和第三方数据再分发风险。

### 数据与合规

使用前请先阅读 [world_cup_data_sources.md](world_cup_data_sources.md)。

简化原则：

- 第三方数据请自行获取
- 按各数据源的许可证或使用条款来使用
- 需要署名的数据源要保留署名
- 不要默认认为“自己生成的 CSV”就一定可以公开再分发

### 常用命令

训练最小 baseline：

```bash
python3 train_world_cup_baseline.py \
  --input world_cup_matches_demo.csv \
  --output baseline_predictions.csv
```

运行 Version B 滚动实验：

```bash
python3 run_world_cup_version_b_experiments.py
```

运行自适应策略实验：

```bash
python3 run_world_cup_version_b_adaptive_experiments.py
```

预测未来比赛：

```bash
python3 predict_world_cup_version_b_adaptive.py \
  --input your_feature_table.csv \
  --output predictions.csv
```

### 许可证

- 开源许可：`MIT License`
- 商业条款：如需单独商业授权、支持、担保或其他合同条款，请通过仓库主页联系方式联系维护者
- 说明：`MIT` 本身已经允许商业使用；单独商业授权是可选的替代安排，不是对 MIT 的非商业限制

### 当前局限

- 仓库刻意不打包第三方原始数据
- 一些更丰富的特征覆盖率还不高，取决于你本地数据源是否齐全
- 世界杯样本本身不大，所以不同评估切分下结果会有波动
- 揭幕阶段这类比赛往往更适合走纯赛前分支，因为赛内状态还不存在
