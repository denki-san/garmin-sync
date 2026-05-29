# garmin-sync

> 把佳明（Garmin Connect）的健康数据同步成本地 JSON 文件。专为
> AI 助手（Claude Code / Codex / Hermes / ChatGPT 等）消费而设计。

[English](./README.md) · [简体中文](./README.zh-CN.md)

`garmin-sync` 是一个极简的 Python CLI + 库，把佳明账号每日健康数据拉
到本地、写成结构化 JSON 文件。没有 daemon，没有第三方服务器，没有云
端——只有一个脚本和一个数据目录，你的 AI 助手（或你自己的脚本）可以
直接读。

```bash
pip install garmin-sync          # 核心
pip install 'garmin-sync[plots]' # 加上 matplotlib 趋势图
```

## 为什么做这个

佳明 app 看每日情况还行，但你没法问它"我最近一个月的 HRV 趋势和睡眠分
对应得怎么样？"或者"周四头痛那天我 Body Battery 债务是不是特别重？"——
这些问题适合 LLM 来答。

`garmin-sync` 就是把数据从佳明搬到 AI 助手能消费的格式的那段管道。一
旦某天的 JSON 落到磁盘上，后面所有事（分析、日报、告警、画图）都只是
读文件而已。

### 和相邻项目对比

|   | garmin-sync | [nftechie/garmin-skill](https://github.com/nftechie/garmin-skill) | [arpanghosh8453/garmin-grafana](https://github.com/arpanghosh8453/garmin-grafana) |
|---|---|---|---|
| 架构 | Python → 本地 JSON | 第三方 SaaS（Transition） | Docker + InfluxDB + Grafana |
| 数据归属 | 完全本地 | 在 Transition 服务器 | 本地 Docker 数据卷 |
| 运维成本 | `pip install` + cron | API key | Docker 全家桶 |
| LLM 友好输出 | ✅ JSON +（可选）Markdown | ❌ 只有 AI Coach 对话 | ❌ Grafana 看板 |
| `garmin.cn` 支持 | ✅ | 未验证 | ✅ |
| 可视化 | 轻量 matplotlib | — | 完整 Grafana |
| 离线可用 | ✅ | ❌ | ✅ |

## 快速上手

### 1. 一次性授权

```bash
garmin-sync setup --domain garmin.com --email you@example.com
# 会提示输入密码；或者预先 export GARMIN_PASSWORD=...
```

OAuth token 会缓存到 `~/.garminconnect-garmin_com/`（或你在 profile 里
配的 `token_dir`）。大约一年后 token 过期需要再跑一次。

> **两步验证账号**：garth 的 SSO 流程目前不支持 MFA。请在跑一次性
> setup 时**临时关闭佳明 app 里的两步验证**，跑完再打开即可，缓存的
> token 不受影响。详见
> [`docs/auth-troubleshooting.md`](docs/auth-troubleshooting.md)。

### 2. 每日同步

```bash
# 同步昨天
garmin-sync sync --domain garmin.com --days 1

# 回填最近 30 天
garmin-sync sync --domain garmin.com --days 30

# 指定某一天
garmin-sync sync --domain garmin.com --date 2026-05-15
```

JSON 默认写到 `./health/`，用 `--output-dir` 覆盖。

### 3.（可选）配置 profile

`~/.config/garmin-sync/profiles.toml`：

```toml
[profiles.me]
email      = "you@example.com"
domain     = "garmin.com"
token_dir  = "~/.garminconnect-garmin_com"
output_dir = "~/garmin-data/me"

[profiles.spouse]
email            = "spouse@example.com"
domain           = "garmin.cn"
token_dir        = "~/.garminconnect-spouse-cn"
output_dir       = "~/garmin-data/spouse"
password_env_var = "SPOUSE_GARMIN_PASSWORD"
```

之后命令更短：

```bash
garmin-sync setup --profile me --email you@example.com
garmin-sync sync  --profile me --days 1
```

完整说明见 [`docs/multi-user.md`](docs/multi-user.md)。

## 同步了哪些数据

每天一个 JSON 文件，例如 `2026-05-28.json`：

```json
{
  "date": "2026-05-28",
  "sleep": {
    "score": 88,
    "start": "2026-05-28 00:56",
    "end": "2026-05-28 08:30",
    "stages": {
      "total_min": 450, "deep_min": 114, "light_min": 272, "rem_min": 64,
      "awake_min": 4, "avg_respiration": 12.0, "avg_sleep_stress": 10.0
    }
  },
  "steps": {"total": 8833, "distance_km": 7.269, "goal": 7540},
  "hrv": {
    "weekly_avg_ms": 47, "last_night_ms": 46, "status": "BALANCED",
    "last_night_5_min_high_ms": 61,
    "baseline": {"balanced_low": 39, "balanced_upper": 51, "marker_value": 0.58},
    "feedback_phrase": "HRV_BALANCED_6"
  },
  "spo2":           {"avg_pct": 93.0, "min_pct": 86, "avg_hr_bpm": 60.0},
  "body_battery":   {"charged": 86, "drained": 92, "max": 99, "min": 7},
  "stress":         {"overall": 43, "level": "中", "rest_min": 494, ...},
  "respiration":    {"low": 9.0, "high": 22.0},
  "intensity_minutes": {"moderate_min": 3, "vigorous_min": 0, "weekly_goal_min": 150},
  "resting_heart_rate": {"value": 56.0},          // 需要密码登录 fallback
  "vo2_max":            {"running": 43.0, "running_precise": 42.5}   // 同上
}
```

静息心率和 VO2 Max 需要额外的 `garminconnect` 密码登录，因为 garth 的
OAuth scope 拿不到这两个端点（会 403）。设置 `GARMIN_PASSWORD` 环境变量
（或 profile 里的 `password_env_var`）就能启用，不设的话这两个 key 会
安静地缺席，不影响其他数据。详见
[`docs/garminconnect-fallback.md`](docs/garminconnect-fallback.md)。

## CSV 导出

```bash
garmin-sync export-csv --profile me --start 2026-05-01 --end 2026-05-29 \
    --out ~/garmin-may.csv
```

把每日 JSON 扁平化成一行一天的 CSV，列结构稳定。缺失值用空字符串而不
是 `0`——所以 Excel/Numbers 能区分"没数据"和"值是 0"。详见
[`docs/csv-and-plots.md`](docs/csv-and-plots.md)。

## 趋势图

```bash
pip install 'garmin-sync[plots]'

garmin-sync plot --profile me --metric hrv --days 30 --out hrv.png
garmin-sync plot --profile me --metric sleep_score --days 90 --out sleep.png
```

单指标线图 + 7 天滑动均值。headless 安全（Agg 后端），扔进 cron 没问题。

支持的 metric：`hrv` / `hrv_5min_high` / `sleep_score` / `sleep_total_min` /
`steps` / `body_battery_min` / `body_battery_max` / `stress_overall` /
`rhr` / `vo2_max_running`。

## Cron 示例

Linux/macOS，每天早上 6:30 同步：

```cron
30 6 * * * GARMIN_PASSWORD='...' /usr/local/bin/garmin-sync sync --profile me --days 1 >> /var/log/garmin-sync.log 2>&1
```

## 作为库使用

```python
from garmin_sync.auth import authenticate
from garmin_sync.collect import collect_day
from garmin_sync.profile import load_profile
from garmin_sync.storage import write_day_json

profile = load_profile("me")
client = authenticate(profile)
data = collect_day(client, "2026-05-28", profile=profile)
write_day_json(data, profile.output_dir)
```

## FAQ

**`garmin.cn` 国区账号能用吗？**
睡眠、步数、HRV、SpO2、压力、运动强度、活动都能拿。但 Body Battery、
静息心率、VO2 Max、训练准备度在 `garmin.cn` 上**无论 token 怎么发都
是 404**——这几个数据只有 `garmin.com` 国际版账号才有。如果你是国区
账号又想要全套数据，需要联系佳明客服把账号迁到国际版。

**为什么写着 `garth` 已弃用？**
上游 `garth` 项目进入了维护模式，现在还能用。哪天真不能用了，
`garmin-sync` 会切到社区的新方案。数据抓取层是刻意写得很薄的——只
有认证层那一块需要换。

**支持两步验证吗？**
目前不支持。setup 时临时关掉 2FA，跑完再开。token 有效期约 1 年。

**token 和密码存哪？**
Token 以明文 JSON 存在 `token_dir`（默认 `~/.garminconnect-<domain>/`）。
密码只从环境变量读（或者 `~/.hermes/.env`，存在的话），从不回写到磁
盘。

**会被佳明限流吗？**
`garmin-sync sync --days 30` 大概是 12 个 API × 30 天 ≈ 360 次请求。佳
明的单账号限流挺宽松，每天 cron 一次完全没问题；循环调用迟早会触发
429。

## 状态

Pre-1.0。JSON schema "已经稳定到我自己每天用"的程度，但可能会加字段。
删字段或改字段名需要 minor 版本号 bump。

## License

[MIT](LICENSE)
