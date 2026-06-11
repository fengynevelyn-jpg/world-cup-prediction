# World Cup Prediction

An experimental football match prediction project built around the **2018** and **2022** men's FIFA World Cups.

The current modeling focus is a **Version B** setup:

- use historical World Cup matches as the training base
- allow in-tournament rolling state features when they exist
- compare simple priors against richer state-driven models
- prioritize probability quality over raw accuracy

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

## Main files

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

## Metrics

The project mainly tracks:

- `log loss`
- `Brier score`

Accuracy is reported, but it is not the primary decision criterion.

## License

- Open-source license: `MIT`
- Separate commercial terms: available on request through the repository contact channel
- Note: the MIT License already permits commercial use; a separate commercial license is an optional alternative for teams that need extra contractual terms

## 中文说明

这是一个基于 **2018** 和 **2022** 男足世界杯的实验性足球比赛预测项目。

当前仓库重点是 **Version B** 实验口径：

- 用历史世界杯比赛作为训练底座
- 在有条件时允许使用赛会进行中的滚动状态特征
- 对比简单先验和更丰富的状态特征
- 更重视概率质量，而不是只看准确率

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

### 许可证

- 开源许可：`MIT License`
- 商业条款：如需单独商业授权、支持、担保或其他合同条款，请通过仓库主页联系方式联系维护者
- 说明：`MIT` 本身已经允许商业使用；单独商业授权是可选的替代安排，不是对 MIT 的非商业限制
