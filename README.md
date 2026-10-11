# 大学物理实验报告：私有发行

本仓库 `craftsfool/physics-lab-skill-release` 及所有Release均为Private，无公开安装包、公开镜像或公开源码。访问与下载需要已授权的GitHub账号。

开发与API维护在另一个私有仓库 `physics-lab-reference-api`。这里仅保存分发说明；`dist/`忽略Git，ZIP及校验文件作为私有Release附件上传。包内含skill运行文本、辅助脚本、MATLAB样式及210×290 mm四页通用空白模板；不包含教材、前人报告、提取库、账户信息或服务端密钥。

## 安装

通过具备访问权限的GitHub账号下载私有Release附件及SHA256校验文件，在本机校验ZIP。使用发行附件 `install_skill.py --archive <ZIP> --sha256-file <校验文件> --destination <Codex skills目录>` 安装。默认安装为新名字`physics-lab-report`，不覆盖已有的`university-physics-lab-report`。如目标目录已存在，先检查已安装版本，安装程序不会自动覆盖。

当前私有发行版本为[v0.1.7](https://github.com/craftsfool/physics-lab-skill-release/releases/tag/v0.1.7)。通过已授权账号下载：

```bash
gh release download v0.1.7 --repo craftsfool/physics-lab-skill-release --dir release-v0.1.7
python3 release-v0.1.7/install_skill.py --archive release-v0.1.7/physics-lab-report-0.1.7.zip --sha256-file release-v0.1.7/physics-lab-report-0.1.7.zip.sha256 --destination "$HOME/.codex/skills"
```

生产接口为`https://physics-lab-reference-api.vercel.app/api/reference`，只接受带个人令牌的POST。当前已发布98个审核模块（教材76、参考报告22），覆盖18个教材实验与22份代表性参考报告。其他提取稿不是已审核内容；安装包不包含原资料。

API端点和用户令牌通过维护者私下配置环境提供。教材/前人资料只经鉴权API，或者由用户明确提供本地文件。API响应只用于当前任务，不写文件；允许缓存AI归纳的知识和来源索引。

安装者可以阅读本机skill与客户端；私有分发不能阻止其复制已获得的内容。安装包只有写作与处理能力，私有资料的访问范围由服务端控制。

## 维护者打包

在开发仓库运行 `python3 scripts/package_skill.py --output ../physics-lab-skill-release/dist --version <版本>`。显式文件清单与每文件哈希决定包内容。校验包内无原文、账号数据及服务端密钥后，再上传至已确认的私有Release；不要把整理库直接打包。

## v0.1.7环境适配

首次使用运行skill内的 `scripts/setup_environment.py --project <报告项目目录>`。无API则建立空白教材、前人智慧目录；材料不足时继续独立工作并询取必要条件。无LaTeX时提供官方TinyTeX一键安装入口，用户授权后执行，并检验中文及公式编译。PDF仅在真实编译和版面检查后交付，失败不覆盖已有PDF。

无本地MATLAB可使用MATLAB Online、Python或Excel，输出注明实际工具；附带标准库CSV线性拟合及可选Excel读取/绘图脚本。保留原本地skill，发行版安装为独立名称；私有API响应不落盘，只允许AI提炼缓存。
