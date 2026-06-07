# binance-alpha-notify

监控 Binance Alpha 空投（数据来自 `alpha123.uk`）并通过 [Apprise](https://github.com/caronc/apprise) 推送通知的命令行工具。安装后即可用 `alpha-notify` 命令。

## 安装

```bash
pip install -e .          # 从源码安装
# 或使用 pipx 隔离安装
pipx install .
```

## 配置

```bash
alpha-notify config init      # 生成配置模板
alpha-notify config path      # 查看配置/数据文件位置
```

编辑生成的 `config.ini`，填入 `apprise_urls`（多个用逗号分隔）：

```ini
[alpha-notify]
apprise_urls = tgram://BOT_TOKEN/CHAT_ID, mailto://user:pass@example.com
timeout = 30
timezone = 8
```

多个 URL 可逗号分隔，或每行一个；**若 URL 本身含逗号，请每行写一个**。

也可用环境变量覆盖（优先级最高）：

```bash
export APPRISE_URLS="tgram://BOT_TOKEN/CHAT_ID"
```

查看生效配置（密钥脱敏）：

```bash
alpha-notify config show
```

## 使用

```bash
alpha-notify run            # 抓取并推送（无子命令时等同 alpha-notify）
alpha-notify run --dry-run  # 只预览，不发送、不写库
alpha-notify run --test     # 强制发送，忽略去重
alpha-notify run --debug    # 详细日志 + traceback
```

## 定时运行

本工具只跑一次即退出，定时交给系统调度器。

Linux / macOS（cron，每 5 分钟）：

```cron
*/5 * * * * APPRISE_URLS="tgram://BOT_TOKEN/CHAT_ID" /path/to/alpha-notify run
```

Windows（任务计划程序）：创建基本任务，触发器设为按间隔重复，操作执行
`alpha-notify`（或 `python -m alpha_notify run`）。

## 数据位置

- 配置：`<user_config_dir>/alpha-notify/config.ini`
- 去重 DB / 缓存：`<user_data_dir>/alpha-notify/`（运行 `config path` 会创建这些目录）
- 可用 `ALPHA_NOTIFY_DB_PATH` / `ALPHA_NOTIFY_CACHE_PATH` 覆盖（覆盖路径的父目录需自行确保存在）

## 开发

```bash
pip install -e ".[dev]"
pytest -v
```
