# 把大学物理实验报告分享给同学

## 现在可以怎样安装

插件目前采用私有分发，没有面向所有人的官方公共市场页面。推荐通过私有插件源安装，之后可接收版本更新。

1. 维护者先给对方的 GitHub 账号授予 `craftsfool/physics-lab-skill-release` 仓库访问权限。
2. 对方在已登录该 GitHub 账号的电脑上打开 Codex，可以直接让 Agent 执行：

   > 请从 GitHub 私有仓库 craftsfool/physics-lab-skill-release 添加插件源，安装其中的“大学物理实验报告”插件，然后带我完成首次设置。

3. 如果选择自己执行，在终端运行：

```
codex plugin marketplace add craftsfool/physics-lab-skill-release
codex plugin add physics-lab-report@physics-lab-private
```

4. 打开新聊天，选择“大学物理实验报告”，告诉它实验名并提供记录和模板。第一次会介绍完整流程并带你完成设置。

无法访问 GitHub 私有仓库时，维护者也可以直接提供私有发行的 ZIP、SHA256 和安装器。接收者按发行包中的安装步骤操作。这种方式不需要获取维护者的登录凭据，但更新时需要重新取得新版包。

## 能发一个市场安装链接吗

可以提供这个 [桌面安装入口](codex://plugins/install/physics-lab-report?marketplace=physics-lab-private)，但接收者必须已经添加 `physics-lab-private` 插件源。链接只打开安装页，不会替对方添加插件源，也不会授予 GitHub 仓库权限。官方说明：[Plugin install](https://learn.chatgpt.com/docs/reference/commands)。

带 `marketplacePath=/Users/...` 的链接只指向发起者电脑上的文件，不能当作跨电脑安装链接。带 `mode=share` 的链接只打开本机分享流程，本身也不是已经生成的收件人分享链接。

如果希望对方只点击一个链接即可找到并安装，有两种正式分发方式：

- **同一 ChatGPT 工作区**：在具备权限的工作区发布或分享插件，选择具体成员/群组，再从实际分享界面复制收件人链接。需要工作区提供对应的分享/发布权限，未加入工作区的账号不能因此获得访问。
- **官方公共插件市场**：提交插件包，完成发布者验证和审核，获批并发布后才有面向公众的市场页面。目前尚未提交，不应编造 `chatgpt.com/plugins/...` 插件ID或承诺任意账号可安装。

官方依据：[插件打包与私有分发](https://developers.openai.com/plugins/build/plugins)、[团队分享](https://learn.chatgpt.com/docs/build-plugins)、[公共市场提交](https://developers.openai.com/plugins/deploy/submission)。
