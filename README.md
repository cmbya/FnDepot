# FnDepot

这是 `cmbya` 的 fnOS 第三方应用源。

当前索引分两类：

**自动构建（由 [`cmbya/fnos-buildbot`](https://github.com/cmbya/fnos-buildbot) 产出，跟随上游自动更新）**

- OpenList（`OpenListTeam/OpenList`）
- CLIProxyAPI（`router-for-me/CLIProxyAPI`）
- TaoSync（`dr34m-cn/taosync`）
- biliLive-tools（`renmu123/biliLive-tools` 正式 Release 固定 tag/SHA 源码构建；内置匹配的 Node、前后端及媒体工具，离线部署，保留原应用 ID、3000 端口、数据和录像目录）

**自动转存现成 FPK（由同一 buildbot 每天北京时间 10:05 / 22:05 检查）**

- F2Media：从 `cmbya/F2Media-fnOS` 的正式 Release 获取 FPK
- ZJJX：从 `cmbya/ZJJX` 的正式 Release 获取 FPK

这两个应用不重新编译、不重新打包；校验后原样转存到本仓日期 Release，再更新索引。无新版本则跳过。

**冻结（保留最后收录的版本，不再自动扫描）**

- `cmbya/StreamCap-fnOS`

- `cmbya/MeTube-fnOS`
- `cmbya/LitePan-fnOS`



冻结的应用在 `apps.json` 里带 `"frozen": true`。索引脚本会直接沿用它们上次收录的结果，
不会联网扫描，也不会因为停止扫描而把它们从索引里移除。
它们的包仍由各自应用仓自行发版；需要重新收录时，删掉该条 `frozen` 即可。

## 自动更新规则

索引**不再定时运行**。触发方式：

1. `cmbya/fnos-buildbot` 构建发布后自动调用（`repository_dispatch` 事件 `refresh-index`，或 `workflow_dispatch`）
2. 手动 `Run workflow`

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

## biliLive-tools 版本迁移

biliLive-tools 的新 FPK 直接采用上游版本 `3.22.1`，旧封装版本 `3.22.8` / `3.22.108` 在数值上更高，因此 FnDepot 不会把 `3.22.1` 判为这些旧包的可更新版本。现有安装需要另行迁移；本源不能通过修改索引让低版本显示为升级。

## 其他应用上游版本迁移

以下应用的新 FPK 直接使用上游版本，不再添加 `native` 修订号。旧包能否显示“可更新”取决于安装来源与版本大小；旧版本高于新版本时需要单独迁移，索引无法将降版本显示为升级。

| 应用 | 旧索引版本 | 新版本 |
| --- | --- | --- |
| MeTube | `2026.09.27-native2` | `2026.09.28` |
| LitePan | `0.5.6-beta-native1` | `0.5.6-beta` |
| OpenList | `4.2.6-native1` | `4.2.6` |
| StreamCap | `1.0.307` | `1.0.3` |
| TaoSync | `0.4.0-native1` | `0.4.0` |
