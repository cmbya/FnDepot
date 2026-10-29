# Sub-Store

原生 FPK，依赖飞牛 `nodejs_v24`，默认端口 **21678**，支持安装后修改端口。单个 Node 进程提供前端和后端，默认 API 路径 `/path`。

- 应用标识 `Sub-Store`，数据保存在飞牛应用 `${TRIM_PKGVAR}` 目录；覆盖升级不主动清理数据，卸载默认保留。
- 无额外登录层，**不要直接暴露公网**。远程访问请使用可信 VPN 或带鉴权的反向代理。
- 模板是 `all` 通用 JS 包；本应用源沿用现有 x86 收录范围，ARM 真机未验证。
- [使用、构建、验证与限制](https://github.com/cmbya/fnos-buildbot/blob/main/docs/substore.md)
- [打包源码及前端默认路径修改脚本](https://github.com/cmbya/fnos-buildbot/blob/main/scripts/build_substore.py)
- [后端对应源码（AGPL-3.0）](https://github.com/sub-store-org/Sub-Store/tags)
- [前端对应源码（GPL-3.0）](https://github.com/sub-store-org/Sub-Store-Front-End/tags)

FPK 中 `BUILD.json` 记录对应版本 tag 与 SHA256，`SOURCES.txt` 提供精确源码链接。尚未完成真实 fnOS 安装、升级回归。
