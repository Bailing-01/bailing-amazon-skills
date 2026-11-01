# 来源与实际实现

旧制作资料（2026-10-30的research.md、视觉内容学习笔记及bot聊天）明确参考多个仓库，并非已证实从某一个仓库直接fork。

| 项目 | 对旧流程的参考 | 本次核查范围 |
|---|---|---|
|https://github.com/Win-Hao/knowledge-video|知识短片、话题形状、短句、卡拍分镜、开头先行|2026-11-02查看仓库页面，描述为HyperFrames知识视频skill|
|https://github.com/remotion-dev/skills|Remotion帧驱动动画实现|2026-11-02查看官方仓库页面；旧10秒样片有Remotion源码|
|https://github.com/Vincentwei1021/video-shotcraft|镜头设计、beat sync、音效与QA|2026-11-02查看仓库页面；本次未调用其实现|
|https://github.com/heygen-com/hyperframes|代码视频与可复用动效|旧笔记列为参考；本次未重新审计其源码或许可|

今天的定价利润v4实际使用本地`@napi-rs/canvas`逐帧绘制+FFmpeg编码；用NumPy频谱通量分析当前原曲，并与旧段落时间作局部对照。没有在今天的环境里运行librosa，没有用Remotion渲染本片，也没有调用Seedance。

本skill的新增规则来自用户对v1–v4的反馈：原曲保留、逐拍渐进文字、柱段与标签成对、公式按实测宽度紧凑拼接、亏损避让、正确的曲线方向、重点结论提亮加粗及数学口径纠正。

本次提供的是原创流程整理与数学示例，不捆绑第三方仓库源码或原曲。不把“参考过”写成“已安装且验证全部功能”。若后续复制第三方代码，先核对其当时许可并保留所需声明。
