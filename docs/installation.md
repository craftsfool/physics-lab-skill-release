# 安装和分享大学物理实验报告

插件代码采用MIT许可开源。任何人都可以读取源码、下载发行包和添加插件源，不需要维护者授予GitHub仓库权限。教材资料服务独立授权，开源代码不包含教材原文或访问凭据。

## 推荐安装

在 Codex 中发送：

> 请从 GitHub 仓库 craftsfool/physics-lab-skill-release 添加插件源，安装其中的“大学物理实验报告”插件，然后带我完成首次设置。

也可以在终端执行：

```
codex plugin marketplace add craftsfool/physics-lab-skill-release
codex plugin add physics-lab-report@physics-lab-private
```

`physics-lab-private` 是为兼容既有安装保留的插件源标识，不表示仓库仍然私有。

安装后打开新聊天，选择“大学物理实验报告”，提供实验名称、记录和需要的栏目。已有用户可先运行 `codex plugin marketplace upgrade physics-lab-private`，再执行上面的安装命令更新。

## 安装链接

已添加插件源的电脑可点击 [安装大学物理实验报告](codex://plugins/install/physics-lab-report?marketplace=physics-lab-private)。这个链接不会自动添加插件源；首次使用者先执行第一条命令。带 `marketplacePath=/Users/...` 的本机路径链接不能在其他人的电脑上直接使用。

开源仓库不等于已经上架OpenAI官方公共插件目录。目前还没有该目录的公开插件页面。要进入官方公共目录，需要完成提交、审核与发布；同一ChatGPT工作区也可按权限分享给成员。

依据：[官方安装链接](https://learn.chatgpt.com/docs/reference/commands)、[插件分发](https://developers.openai.com/plugins/build/plugins)、[公共目录提交](https://developers.openai.com/plugins/deploy/submission)。

## 资料与隐私

首次登记设备可按当前规则获得30天资料访问，也可以只使用自己的教材和记录。设备密钥是软件凭据，不代表实名身份或硬件唯一身份。后台服务器、教材原文和生产密钥不在开源范围内。
