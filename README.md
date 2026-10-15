# Big Data Hot News

一个全局可用的 Codex Skill，用于从维护好的信息源中发现、去重、评估并整理大数据领域的热点新闻。

覆盖方向包括：

- 数据库与分布式 SQL
- OLAP、MPP 与列式存储
- Kafka、Flink、CDC 与流处理
- 数据湖、开放表格式与 Lakehouse
- 数据仓库与 Analytics Engineering
- 查询引擎、向量化执行与数据基础设施
- 向量数据库与多模态数据存储

## 能力

这个 Skill 可以：

1. 按日期范围收集 RSS、Atom、GitHub Releases、JSON 列表和 LinkedIn Engineering 文章；
2. 合并官网、GitHub、LinkedIn、媒体等渠道对同一事件的重复报道；
3. 区分“文章是否值得读”和“事件是否正在被广泛讨论”；
4. 降低 RC、beta、nightly、普通补丁、营销文章和重复公告的优先级；
5. 对安全公告、正式版本、开放格式、架构变化、生产实践和可复现 Benchmark 提高优先级；
6. 生成日报、周报、指定日期范围热点榜和趋势总结；
7. 通过独立的 JSON 文件持续维护信息源。

## 安装

将仓库克隆到任意目录：

```bash
git clone git@github.com:lvyanquan/big-data-hot-news.git
```

复制到 Codex 全局 Skills 目录：

```bash
cp -R big-data-hot-news ~/.codex/skills/big-data-hot-news
```

也可以使用符号链接，方便后续通过 Git 更新：

```bash
ln -s /path/to/big-data-hot-news ~/.codex/skills/big-data-hot-news
```

如果目标目录已经存在，请先确认其中是否有尚未提交的自定义信息源，不要直接覆盖。

## 使用

在 Codex 中显式调用：

```text
使用 $big-data-hot-news 整理过去一周的大数据热点新闻。
```

更多示例：

```text
使用 $big-data-hot-news 整理 2026-10-09 到 2026-10-15 的十大热点。
```

```text
使用 $big-data-hot-news 检查最近三天数据库安全和版本发布动态。
```

```text
使用 $big-data-hot-news 比较本周 Iceberg、Paimon、Hudi 和 Delta Lake 的重要更新。
```

```text
使用 $big-data-hot-news 审核当前信息源，找出失效、重复或噪音过高的来源。
```

Skill 默认允许自动发现，相关的大数据新闻整理请求也可以自动触发。

## 信息源

信息源配置位于：

```text
references/sources.json
```

当前目录包含 36 个来源，默认启用 31 个。主要包括：

### 数据库与 OLAP

- PostgreSQL News
- DuckDB Blog
- PingCAP Blog
- ClickHouse Blog
- StarRocks Blog
- Apache Doris Blog
- Databend Blog

### 查询与计算

- Trino
- Apache Flink
- Apache Arrow
- Velox

### 数据湖与 Lakehouse

- Apache Paimon
- Apache Hudi
- Delta Lake
- Databricks
- AWS Big Data
- Apache Iceberg Releases（默认关闭）

### 实时数据与流处理

- Apache Kafka
- Confluent
- Confluent Developer
- Apache Fluss
- Decodable

### 数据工程与媒体

- dbt Labs
- LinkedIn Engineering
- Data Engineering Weekly
- The New Stack Data
- InfoQ Architecture & Design

### Lance 生态

- LanceDB Blog
- Lance Releases
- LanceDB Releases

详细 URL、分级、主题、主体归并和编辑说明均保存在 `references/sources.json`。

## 信息源字段

每个来源的主要字段：

| 字段 | 说明 |
|---|---|
| `id` | 稳定的信息源标识 |
| `name` | 显示名称 |
| `kind` | `rss`、`atom`、`json_list` 或 `linkedin_engineering` |
| `url` | 采集地址 |
| `homepage` | 官方页面 |
| `tier` | `T1` 官方一手、`T1_5` 官方账号、`T2` 媒体或个人 |
| `owner_key` | 独立参与方标识，用于合并同一机构的不同渠道 |
| `participation` | `editorial` 可独立成为新闻，`signal` 只作为辅助信号 |
| `topics` | 关注领域 |
| `enabled` | 是否默认采集 |
| `notes` | 采集和编辑注意事项 |

更新方法见：

```text
references/source-maintenance.md
```

## 本地采集

采集脚本只依赖 Python 标准库，建议使用 Python 3.9 或更高版本。

查看全部信息源：

```bash
python3 scripts/collect_feeds.py --list
```

采集指定日期范围：

```bash
python3 scripts/collect_feeds.py \
  --from 2026-10-09 \
  --to 2026-10-15
```

只采集指定来源：

```bash
python3 scripts/collect_feeds.py \
  --from 2026-10-09 \
  --to 2026-10-15 \
  --source apache-flink \
  --source apache-paimon-releases
```

以表格形式查看：

```bash
python3 scripts/collect_feeds.py \
  --from 2026-10-09 \
  --to 2026-10-15 \
  --format table
```

输出 JSON：

```bash
python3 scripts/collect_feeds.py \
  --from 2026-10-09 \
  --to 2026-10-15 \
  --format json \
  --output candidates.json
```

采集脚本用于发现候选文章，不应直接作为最终事实依据。生成报告前仍应打开官方原文，核实版本状态、日期、指标和测试边界。

## 热点评估原则

Skill 将两个维度分开判断。

### 编辑价值

判断事件本身是否值得读，主要考虑：

- 实质份量
- 信息增量
- 证据强度
- 影响范围
- 可操作性

### 讨论热度

判断同一事件被多少独立组织、项目、媒体或社区参与者关注。

同一机构的官网、GitHub Releases 和 LinkedIn 等渠道使用相同的 `owner_key`，只算一个独立参与方，避免人为放大热度。

完整规则见：

```text
references/editorial-rubric.md
```

## 目录结构

```text
.
├── SKILL.md
├── README.md
├── agents/
│   └── openai.yaml
├── references/
│   ├── editorial-rubric.md
│   ├── source-maintenance.md
│   └── sources.json
└── scripts/
    └── collect_feeds.py
```

## 验证

检查信息源 JSON：

```bash
python3 -m json.tool references/sources.json >/dev/null
```

检查采集脚本和目录：

```bash
python3 scripts/collect_feeds.py --list
```

检查 Skill 格式：

```bash
/usr/bin/python3 \
  ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  .
```

`quick_validate.py` 依赖 PyYAML。如果当前 Python 环境没有 `yaml` 模块，可以换用已安装 PyYAML 的 Python 解释器。

