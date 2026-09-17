# FnDepot

这是 `cmbya` 的 fnOS 第三方应用源。

当前自动索引以下仓库的**最新正式 Release**：

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

只收录 GitHub **正式 Release**：
- Draft：不收录
- Pre-release：不收录
- 正式 Release：收录

因此建议流程：

1. 各 `*-fnOS` 仓库自动生成 Pre-release FPK。
2. 在飞牛真机安装测试。
3. 测试正常后，在 GitHub Release 页面编辑该 Release，取消 `Set as a pre-release`。
4. 本仓库下一次 Actions 会自动把它写入 `fnpack.json`。

## FnDepot 添加源

在 FnDepot 中添加 GitHub 仓库根地址：

`https://github.com/cmbya/FnDepot`

根目录必须存在 `fnpack.json`。

## 如果你的 GitHub 用户名/仓库名不同

编辑 `apps.json` 中的 `repo`、`release_name_prefix`、`bug_report_url` 和 `source_info` 即可。

同一个仓库包含多个应用时，可以在 `apps.json` 中配置多条记录，并使用
`release_name_prefix` 按 Release 名称分别匹配对应应用。
