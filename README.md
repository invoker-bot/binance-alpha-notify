# binance-alpha-notify

![Python](https://img.shields.io/badge/python-%E2%89%A53.9-blue)
![License](https://img.shields.io/badge/license-MIT-green)

监控 **Binance Alpha 空投**（数据来自 [alpha123.uk](https://alpha123.uk)）并通过 [Apprise](https://github.com/caronc/apprise) 推送通知的命令行工具。安装后一条命令即可用，跑一次就退出，定时交给系统调度器。

> 灵感来自一个跑在服务器 crontab 上的裸脚本，重写为跨平台、可 `pip`/`pipx` 安装、带去重与测试的 CLI。

## 特性

- 🛰️ 抓取当天**尚未到期、且有具体领取时间**的空投，并附带价格估算
- 🔔 通过 Apprise 推送到 80+ 渠道：Telegram、Bark、钉钉、飞书、企业微信、Server酱、邮件、Discord、Slack…
- 🧠 SQLite 去重，**同一空投只推一次**；`--test` 可强制重发且不污染去重库
- 💻 跨平台（Linux / macOS / Windows），一次性命令，调度交给 cron / 计划任务
- 📂 配置与数据放在系统标准用户目录（platformdirs），支持环境变量覆盖
- ✅ 模块化实现，68 个单元测试，离线可测（不打真实网络/不发真实通知）

## 安装

```bash
# 从源码安装
pip install -e .

# 或用 pipx 隔离安装（推荐，命令全局可用且互不污染）
pipx install .
```

安装后会得到 `alpha-notify` 命令（等价于 `python -m alpha_notify`）。

## 配置

```bash
alpha-notify config init      # 在标准位置生成配置模板
alpha-notify config path      # 查看配置 / 数据文件的实际位置
alpha-notify config show      # 查看当前生效配置（密钥脱敏）
```

编辑生成的 `config.ini`，填入 `apprise_urls`：

```ini
[alpha-notify]
# 每行一个 URL，或单行用逗号分隔；
# 若某个 URL 本身包含逗号（如 mailto 的多收件人 ?to=a,b），请让它单独成行。
apprise_urls =
    tgram://BOT_TOKEN/CHAT_ID
    bark://DEVICE_KEY@HOST

# HTTP 请求超时（秒）
timeout = 30

# 时区小时偏移（北京时间为 8）
timezone = 8
```

也可以用环境变量覆盖（优先级最高，适合 cron / 容器）：

```bash
export APPRISE_URLS="tgram://BOT_TOKEN/CHAT_ID"
```

各渠道的 URL 格式见 [Apprise 文档](https://github.com/caronc/apprise/wiki)。

## 使用

```bash
alpha-notify run            # 抓取并推送（无子命令时等同 alpha-notify）
alpha-notify run --dry-run  # 只预览，不发送、不写库（首次配置时先用它确认）
alpha-notify run --test     # 强制发送，忽略去重（测试通知是否畅通）
alpha-notify run --debug    # 详细日志 + 出错时打印 traceback
alpha-notify --version
```

## 定时运行

本工具跑一次即退出，定时交给系统调度器。

**Linux / macOS（cron，每 5 分钟）：**

```cron
*/5 * * * * APPRISE_URLS="tgram://BOT_TOKEN/CHAT_ID" /path/to/alpha-notify run
```

**Windows（任务计划程序）：** 新建基本任务 → 触发器设为按间隔重复 → 操作执行
`alpha-notify`（或 `python -m alpha_notify run`）。

## 工作原理

1. 从 `alpha123.uk` 拉取空投列表与价格；
2. 筛选**今天、有具体时间 (HH:MM)、且尚未到期**的空投；
3. 用 SQLite 按空投唯一标识去重，跳过已推送的；
4. 用 Apprise 把待推送的空投格式化后发送到所有配置渠道，并记录已发送。

## 数据位置

- 配置：`<user_config_dir>/alpha-notify/config.ini`
- 去重 DB / 缓存：`<user_data_dir>/alpha-notify/`（运行 `config path` 可查看实际路径）
- 可用 `ALPHA_NOTIFY_DB_PATH` / `ALPHA_NOTIFY_CACHE_PATH` 覆盖（支持 `~` 展开，父目录会自动创建）

## 开发

```bash
pip install -e ".[dev]"
pytest -v
```

## 免责声明

本工具仅从公开接口读取信息并做本地通知，不进行任何交易或下单操作。空投信息以官方与 `alpha123.uk` 为准，请自行核实。

## 许可证

[MIT](LICENSE)
