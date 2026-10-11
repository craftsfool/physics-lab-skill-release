# 大学物理实验报告：私有发行

本仓库 `craftsfool/physics-lab-skill-release` 及所有Release均为Private，无公开安装包、公开镜像或公开源码。访问与下载需要已授权的GitHub账号。

开发与API维护在另一个私有仓库 `physics-lab-reference-api`。这里仅保存分发说明；`dist/`忽略Git，ZIP及校验文件作为私有Release附件上传。包内含skill运行文本、辅助脚本、MATLAB样式及210×290 mm四页通用空白模板；不包含教材、前人报告、提取库、账户信息或服务端密钥。

## 安装

通过具备访问权限的GitHub账号下载私有Release附件及SHA256校验文件，在本机校验ZIP。使用发行附件 `install_skill.py --archive <ZIP> --sha256-file <校验文件> --destination <Codex skills目录>` 安装。默认安装为新名字`physics-lab-report`，不覆盖已有的`university-physics-lab-report`。如目标目录已存在，先检查已安装版本，安装程序不会自动覆盖。

API端点和用户令牌通过维护者私下配置环境提供。教材/前人资料只经鉴权API，或者由用户明确提供本地文件。API响应只用于当前任务，不写文件；允许缓存AI归纳的知识和来源索引。

安装者可以阅读本机skill与客户端；私有分发不能阻止其复制已获得的内容。安装包只有写作与处理能力，私有资料的访问范围由服务端控制。

## 维护者打包

在开发仓库运行 `python3 scripts/package_skill.py --output ../physics-lab-skill-release/dist --version <版本>`。显式文件清单与每文件哈希决定包内容。校验包内无原文、账号数据及服务端密钥后，再上传至已确认的私有Release；不要把整理库直接打包。
