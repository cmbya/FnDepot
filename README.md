# FnDepot

这是 `cmbya` 的 fnOS 第三方应用源。

当前自动索引以下仓库的**最新非 Draft Release（包含 Pre-release）**：

- `cmbya/StreamCap-fnOS`
- `cmbya/biliLive-tools-fnOS`
- `cmbya/TaoSync-fnOS`
- `cmbya/OpenList-fnOS`
- `cmbya/MeTube-fnOS`
- `cmbya/LitePan-fnOS`
- `cmbya/FNAMS`（Hermes Agent、Hermes Studio）
- `cmbya/ZJJX`
- `cmbya/F2Media-fnOS`

## 自动更新规则

GitHub Actions 每天运行一次，并且支持手动 `Run workflow`。

收录 GitHub 最新的非 Draft Release：
- Draft：不收录
- Pre-release 和正式 Release：均收录

Pre-release 会在更新说明中标记。

## FnDepot 添加源

在 FnDepot 中添加 GitHub 仓库根地址：

`https://github.com/cmbya/FnDepot`

根目录 `fnpack.json` 为 V2 索引（需 FnDepot v0.0.7 或更高版本）；另保留 `fnpack-v1.json` 供旧版客户端通过 JSON 直链使用。已有 `fnpack-v2.json` 直链保持可用。

此次迁移用于验证“可更新”列表的版本识别；FnDepot 已能在历史版本中找到新版，因此迁移后是否出现更新仍需在客户端实测。

## 如果你的 GitHub 用户名/仓库名不同

编辑 `apps.json` 中的 `repo`、`release_name_prefix`、`bug_report_url` 和 `source_info` 即可。

同一个仓库包含多个应用时，可以在 `apps.json` 中配置多条记录，并使用
`release_name_prefix` 按 Release 名称分别匹配对应应用。
