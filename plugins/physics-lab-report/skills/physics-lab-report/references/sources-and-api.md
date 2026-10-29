# 资料和鉴权API

## 来源优先级

用户已确认数据决定事实；当次课程PPT、教师说明和模板决定要求；教材决定理论依据；前人报告仅为参考。读取扫描PDF时渲染相关页，避免漏掉公式、下标和单位。API摘要不是整章阅读，缺少正文细节时明确说明。

## 接入

维护者私下提供HTTPS API端点、API令牌、实验ID和允许的模块。运行环境设置 `PHYSICS_LAB_API_URL`（完整 `/api/reference` URL）及 `PHYSICS_LAB_API_TOKEN`。部署启用Vercel平台保护时，还需维护者私下提供 `PHYSICS_LAB_DEPLOYMENT_BYPASS`，客户端通过请求头提交；它只用于穿过平台保护，不能替代用户API令牌或绕过资料权限与配额。凭据经私密配置/环境注入，不放命令参数、对话、报告或版本库；客户端不需要任何Blob/Redis/GitHub服务端密钥。

```
python3 scripts/fetch_reference.py --experiment polarization --library textbook --topic theory
```

请求字段：`experiment` 为维护者分配的短ID，`library` 为 `textbook` 或 `senior`，`topic` 为 `purpose/theory/instruments/procedure/data_processing/uncertainty/questions/discussion`。每次仅一模块，不提供自由文本提示、URL、路径、分页、原文件下载或目录枚举。

输出包含 `schema_version`、`experiment`、`library`、`topic`、`version`、`summary`、`key_points`、`formulas`、`figures`（图注与文字说明）、`sources`、`retrieved_at`。来源只有可引用的标题及页码，不含内部路径。401/403要求合法授权，429等待配额恢复或联系维护者；不换令牌/身份绕过限制。5xx可稍后一次重试，同时推进无需资料的部分。

用户本地路线：记录其给出的文件/目录，定位对应章节，不上传原始数据和本地材料。没有API配置时先询问用户选择配置令牌或使用本地/无参考资料；答复前不创建目录，不自动回退搜索维护者库。用户选择后按环境说明执行；私密配置接入令牌，不在聊天中索取或打印。

## 响应与缓存边界

客户端只把响应送入当前任务工具上下文，**不提供输出文件参数，不写API响应副本**。调用时不得用文件重定向、tee、下载或工具日志落盘API正文，也不把JSON、整段原文、前人表格或截图保存进用户项目。

允许缓存AI基于响应重新提炼的知识：简短机制、量定义、必要公式、操作条件、自己的分析及待核对点；用自己的表达压缩，不拼接形成原章节。缓存至 `.lab-knowledge/<实验ID>/knowledge.md`，保留来源ID、页码、版本和提取日期供复核，不保存完整响应、下载链接、令牌或整份参考数据。后续任务读取该知识摘要；必要时重新按需请求API，不能用旧摘要冒充完整教材。

用户明确提供的本地文件由用户自行保留，这条不落盘规则针对来自维护者API的内容。维护者私有开发区的离线整理库不分发给技能安装者。

此规则是客户端/工作流约束，不是DRM；服务端只能控制返回的内容和配额。响应进入模型后，平台对话与工具记录可能保留内容，安装者也能修改客户端；不能宣称平台完全无痕或绝对不可复制。

## 设备和章节入口

新增 [设备签名与章节原文预览](device-and-chapters.md)：设备 Key 查询摘要仍不落盘；章节原文通过专门的短时浏览器会话阅读。原文预览有独立权限，不受摘要字符长度上限约束，也不能保证无法保存或复制。资料来源不再依赖 KOOK 或 OpenAI Client ID。
