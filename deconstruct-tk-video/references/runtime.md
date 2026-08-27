# 跨平台运行规则

## 后端选择

按顺序选择首个可用方案：

| 环境 | 首选 | 降级 |
|---|---|---|
| Windows + NVIDIA | faster-whisper CUDA | faster-whisper CPU |
| Windows 无 NVIDIA | faster-whisper CPU | 更小模型 |
| Apple Silicon Mac | faster-whisper CPU | 更小模型 |
| Intel Mac | faster-whisper CPU | 更小模型 |

默认使用 `small` 模型；内存不足时用 `base`，用户明确要求更高精度时再使用 `medium`。不要默认下载 `large`。

## Python 隔离环境

始终优先使用初始化脚本创建的专用 Python 环境，不要把 `faster-whisper` 安装到系统 Python、Homebrew Python 或 uv 管理的 Python 里：

- Windows：`%LOCALAPPDATA%\tianguo-video\python-env\Scripts\python.exe`
- macOS：`~/Library/Caches/tianguo-video/python-env/bin/python`

环境检查和视频分析脚本必须先查找上述路径；不存在时才退回查找系统 `python` / `python3`，并仅用系统 Python 创建专用环境。这样可以避开 PEP 668、权限、PATH、不同 Python 小版本和新电脑预装状态差异。

## 缓存

中间文件放在任务工作区的 `.video-cache/<视频SHA-256>/`：

- `audio.wav`
- `transcript.json`
- `frames/`
- `metadata.json`
- `manifest.json`（模型、时长、抽帧数量和缓存版本）

模型放在用户缓存目录，不放入 Skill：

- Windows：`%LOCALAPPDATA%\tianguo-video\models`
- macOS：`~/Library/Caches/tianguo-video/models`

同一文件哈希命中缓存时直接复用。
复用前必须验证文件非空、转写 JSON 可解析且模型一致；模型变化或缓存损坏时只重建对应产物。

账号清单批量视频使用 `prepare-account-manifest.py`。它只加载一次 Whisper 模型并顺序处理待转写音频；下载、元数据和音频命中缓存时跳过。当前实现仍以本地 Whisper 作为统一可信转写后端；只有后续下载器稳定保存并验证 TikTok VTT 字幕后，才允许字幕优先跳过 Whisper，不得仅因元数据声明存在字幕就跳过识别。

## 抽帧规则与防漏门槛

核心原则：每次画面意义发生变化时看一眼；没有变化的长镜头才按固定间隔抽查。

按顺序建立目标不超过 30 张的帧清单。30 张是普通候选帧的效率上限，不得淘汰强制证据帧：

1. 前 3 秒按约 0.5 秒强制取帧。
2. 最后 3 秒按约 1 秒强制取帧。
3. 用 FFmpeg 场景变化检测提取主要镜头切换。
4. 没有对应场景帧的口播段落边界补一张。
5. 仍存在超过约 5 秒的长镜头空白时才做定时补位。

强制证据帧包括：前 3 秒、最后 3 秒、产品首次出现、价格/折扣/赠品/购买按钮、前后对比或效果证明、人物/地点/故事阶段改变，以及口播主题变化。若强制帧超过上限，提升本次上限并告警，不得静默删除。

结果写入 `frames.json`，记录每张帧的时间点、原因、是否强制保留和质量状态。抽帧失败、候选被上限舍弃、时间轴存在超过 5.5 秒空白时必须写入 `coverage_audit.warnings`，不得照常声称覆盖完整。

抽帧后执行以下硬门槛：

1. 前 3 秒最大检查间隔 0.5 秒；最后 3 秒最大检查间隔 1 秒。
2. 有口播的连续 5 秒不得没有代表帧；无变化长镜头最长约 8 秒抽查一次。
3. 镜头切换前后核对有效画面，不得用黑屏、闪白、模糊或转场叠帧充当证据；坏帧在原时间点前后 0.2～0.5 秒替换。
4. 单独核对顶部标题、中部产品/证明、底部字幕和价格/购买区域；同镜头文字变化也算意义变化。
5. 口播出现“你看、之前/之后、这个产品、现在只要”、数字、折扣或购买指令时，附近必须有对应画面，否则只对该局部补帧。
6. 只有画面、文字、动作和叙事作用均相同时才能去重。
7. 完成 `frames.json.coverage_audit.required_visual_checks` 后，将结果标记为通过；未通过前禁止进入第二步拆解。

局部补帧仅用于转写置信度低、口播与字幕冲突或关键产品文字不清的时间段。每个局部片段最多 8 张，最多处理 3 个片段。

## 故障处理

- FFmpeg 缺失：停止并运行初始化，不要尝试视觉兜底。
- 转写后端缺失：停止并报告安装命令；不得整片密集抽帧。
- GPU 后端失败：自动改用 CPU，并明确报告降级。
- 模型下载失败：保留已下载内容，报告网络或磁盘错误。
- 路径包含中文或空格：始终使用参数数组或完整引号，不拼接未转义命令。

### TikTok 公开链接下载失败

| 触发条件 | 一线修复 | 仍失败兜底 |
|---|---|---|
| Windows `gallery-dl` 非零退出，包括 `403 Forbidden`、JavaScript challenge、`No results` | `prepare-video.ps1` 自动调用一次无 Cookie 公开备用通道；只发送公开 URL，验证视频 ID、HTTPS TikTok CDN、文件大小、FFprobe 视频流和音频流 | 删除未通过校验的 `.partial.mp4`，报告主下载退出码与备用失败原因，保留任务目录并请求用户上传本地视频 |
| 备用返回其他视频 ID、非 HTTPS/非 TikTok CDN、空文件、无视频流或无音频流 | 判定备用结果无效，不进入 `analyze-video.ps1` | 请求本地 MP4/MOV/WebM/M4V；不得把封面图、无声文件或错误视频送入转写 |
| macOS `gallery-dl` 非零退出 | 当前不调用 Windows 备用实现 | 保留任务目录并请求本地视频，不声称已自动恢复 |

## 新电脑安装

- 运行检查脚本，分别读取 `local_video_ready` 和 `tiktok_link_ready`，不要只看工具是否存在或 Python 包能否导入。
- 缺项时运行平台 setup 脚本；Python 依赖安装到 `tianguo-video/python-env` 专用环境，不写入系统 Python。
- setup 必须用 tiny 模型真实加载一次转写后端并写入验证标记；仅 `import faster_whisper` 成功不算就绪。
- Windows 模型加载发生进程崩溃时，先更新微软官方 Visual C++ x64 运行库，再重跑 setup。
- setup 后必须重新检查；TikTok 链接任务还要确认专用 Python 环境可以导入 `gallery_dl`。
- macOS 的 `whisper-cli` 只作为探测信息；当前自动分析链以可脚本化的 faster-whisper 为准。
