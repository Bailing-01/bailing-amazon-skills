# CLI Spec — 生成 skill 的工具流子树

每个 `{industry}-master.skill` 不只是 markdown 思维顾问，还附一套 bash CLI 把认知 OS「物化成可执行操作」。Phase 3 在写完 `SKILL.md` 后调 `tools/cli_writer.py` 自动生成 `cli/` 子树。

---

## 设计原则

1. **思维顾问 + 实操 CLI 套件**，不是 RPA。CLI 的工作是把行业 OS 的「执行端」结构化成对话式工具：交互问询 → 应用 playbook / protocol → 输出推荐 + markdown 报告。
2. **零外部依赖** — 纯 bash 4 + POSIX coreutils。不要求 `jq` / `yq` / Python。CLI 必须在裸装 macOS / Linux 上跑通。
3. **对应 synthesis.md 的章节**，不是凭空设计：
   - Section 9 (Agentic Protocol) → `cli/protocol/agentic.sh`
   - Section 2 (Playbook 「如果 X，则 Y」规则) → `cli/decision/{slug}.sh`
   - Section 4 (Workflows / SOP) → `cli/workflow/{slug}.sh`
4. **标准接口** — 每个 script 必须支持 4 个 flag：`--help` / `--explain` / `--dry-run` / `--json`。
5. **可教学** — `--explain` 不是简短帮助，是把背后的心智模型 + 来源贴出来，让用户理解为什么这样做。

---

## 目录布局

```
{industry-slug}-master/
└── cli/
    ├── README.md                # 全部脚本总览 + 用法 + 一行说明
    ├── lib/
    │   └── common.sh            # 公共工具：彩色输出、确认提示、写报告函数
    ├── protocol/
    │   └── agentic.sh           # Agentic Protocol CLI 化（按 N 维度收集 + 出报告）
    ├── decision/
    │   ├── {area-1}.sh          # 决策树之一（从 playbook 抽取）
    │   └── {area-2}.sh
    └── workflow/
        ├── {wf-1}.sh            # SOP 走查脚本之一
        └── {wf-2}.sh
```

`{slug}` 命名规则：英文 lowercase + hyphen，最长 32 字符。例：`framework-select` / `build-rag-agent` / `eval-strategy`.

---

## 标准接口

每个 `.sh` 文件必须实现以下 4 个 flag：

| Flag | 行为 |
|------|------|
| `--help` | 用法 + 1-3 句说明这个 script 解决什么问题 |
| `--explain` | 打印背后的心智模型 / playbook rule / 来源（教学模式，不交互） |
| `--dry-run` | 走完所有问题但不写报告文件，结果只 echo 到 stdout |
| `--json` | 报告以 JSON 格式 echo 到 stdout（机器可读，pipeline 可消化） |

无 flag → 交互式默认模式，最后写 markdown 报告到 `./{script-name}-{date}.md`。

`--help` 应当少于 30 行。`--explain` 可以更长（包含心智模型一段引文）。

---

## 三类脚本模板

### A. `cli/protocol/agentic.sh` — Agentic Protocol 落地

**作用**：拿到一个新问题时，按这一行人的 N 个研究维度去做功课。来自 synthesis.md Section 9.

**伪代码骨架**：

```bash
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../lib/common.sh"

usage() { ... }
explain() {
  cat <<'EOT'
本脚本把 {industry} 行业的 Agentic Protocol 落地。
拿到一个新问题时，资深从业者会按 N 个维度做功课再答。
心智模型: ...
来源: synthesis.md Section 9
EOT
}

# 解析 flag
DRY_RUN=0; JSON=0
for arg in "$@"; do
  case "$arg" in
    --help|-h) usage; exit 0 ;;
    --explain) explain; exit 0 ;;
    --dry-run) DRY_RUN=1 ;;
    --json) JSON=1 ;;
  esac
done

ms_section "Agentic Protocol · {industry}"
ms_info "请描述你拿到的新问题（可以多行，空行结束）："
problem="$(ms_read_multiline)"

# 按 N 维度逐一问
declare -a dim_titles=("9.1 维度名" ...)
declare -a dim_questions=("看什么..." ...)
declare -a dim_sources=("在哪看..." ...)
declare -a dim_outputs=()

for i in "${!dim_titles[@]}"; do
  ms_section "${dim_titles[$i]}"
  echo "${dim_questions[$i]}"
  echo "建议来源: ${dim_sources[$i]}"
  ms_prompt "你的发现 / 推断:"
  read -r ans
  dim_outputs+=("$ans")
done

# 输出报告
if [[ $JSON -eq 1 ]]; then
  ms_emit_json problem "${dim_titles[@]}" "${dim_outputs[@]}"
elif [[ $DRY_RUN -eq 1 ]]; then
  ms_emit_md_stdout
else
  ms_emit_md_file "agentic-protocol"
fi
```

### B. `cli/decision/{area}.sh` — Playbook 决策树

**作用**：把 synthesis.md Section 2 中相关的几条「如果 X，则 Y」规则组合成一个交互决策树。

**生成规则**：把 playbook 7 条规则按主题聚类（framework-select / eval-strategy / observability / RAG-design 等），每个聚类生成一个 decision script。

**伪代码**：

```bash
explain() {
  cat <<'EOT'
本脚本: framework selection decision tree
基于 playbook rule 3 / rule 4
心智模型: thin vs thick framework （来自 mental model 1.1）
EOT
}

# 第一问：multi-agent ≥ 3 actors?
ms_prompt "你的项目需要 ≥ 3 个 agent 协作吗? [y/N]"
read -r ans1
if [[ "$ans1" =~ ^[Yy] ]]; then
  ms_prompt "需求是否真的不能拆成单 agent + tool calling? [y/N]"
  read -r ans2
  ...
fi

# 综合给推荐
case "$path" in
  thin) recommendation="default 选项: thin framework (Vercel ai-sdk / pydantic-ai) + 直接 SDK" ;;
  thick) recommendation="必要条件下用 thick orchestration (LangGraph / CrewAI). 但..." ;;
esac

ms_emit_decision "$recommendation"
```

### C. `cli/workflow/{wf-slug}.sh` — Workflow 走查 checklist

**作用**：把 synthesis.md Section 4 引用的 SOP 落成 checklist。每步问用户「做了吗 / 怎么做的 / 跳过原因」。

**生成规则**：从 03-workflows.md 拉每个 workflow 的入门 SOP 步骤 + 资深差异点 + 失败模式。生成的 script 一次跑完一个 workflow，最后输出报告含「完成步骤 / 跳过步骤 / 失败模式自检」三段。

```bash
explain() {
  cat <<'EOT'
本脚本: build production-ready RAG agent (SOP 走查)
来源: synthesis.md Section 4 + 03-workflows.md
失败模式: ${failure_modes[*]}
EOT
}

declare -a steps=(
  "step1: ..."
  "step2: ..."
)

for step in "${steps[@]}"; do
  ms_section "$step"
  ms_prompt "状态? [d=done / s=skipped / b=blocked]"
  read -r status
  case "$status" in
    s) ms_prompt "跳过原因 (资深路径合理跳过 vs 没意识到):"
       read -r reason; ... ;;
    b) ms_prompt "blocker:"; ... ;;
  esac
done

# 失败模式自检
ms_section "失败模式自检"
for failure in "${failure_modes[@]}"; do
  echo "- [ ] 没踩 $failure?"
done

ms_emit_md_file "workflow-{slug}"
```

---

## `cli/lib/common.sh` 函数清单

CLI script 共用的 helper，避免每个 script 重复造轮子：

| 函数 | 作用 |
|------|------|
| `ms_section "$title"` | 打印分节标题（彩色） |
| `ms_info "$msg"` | 打印提示信息 |
| `ms_warn "$msg"` | 打印警告（黄） |
| `ms_error "$msg"` | 打印错误（红） |
| `ms_prompt "$question"` | 打印提问（不读输入） |
| `ms_read_multiline` | 读多行直到空行，返回拼接字符串 |
| `ms_confirm "$question"` | y/N 确认，返回 0/1 |
| `ms_emit_md_file "$slug"` | 把当前 markdown buffer 写到 `./{slug}-YYYY-MM-DD.md` |
| `ms_emit_md_stdout` | dry-run 时 echo markdown buffer |
| `ms_emit_json ...` | 拼出 JSON 字符串 echo |
| `ms_buffer_append "$line"` | 往全局 markdown buffer 追加一行 |

实现要求：纯 bash 4，无 awk/sed 依赖（mac BSD 行为差异）；ANSI color 兼容 macOS Terminal / iTerm / VS Code Terminal。

---

## `cli/README.md` 模板

每个 `{industry}-master/cli/README.md` 由 `cli_writer.py` 自动生成。模板：

```markdown
# {industry-cn-name} CLI

把 {industry} master skill 的 Agentic Protocol / playbook / SOP 物化为 bash 工具。
不替代认知 OS 本身（看 ../SKILL.md），是它的「执行端」。

## 用法

所有脚本都支持 `--help` / `--explain` / `--dry-run` / `--json`。

```bash
./cli/protocol/agentic.sh           # 拿到新问题时，按 N 维度做功课
./cli/decision/framework-select.sh  # framework 选型决策树
./cli/workflow/build-rag-agent.sh   # 生产级 RAG agent SOP 走查
```

## 脚本清单

| 脚本 | 作用 | 来源章节 |
|------|------|---------|
| protocol/agentic.sh | Agentic Protocol N 维度落地 | synthesis 9 |
| decision/{area}.sh | 决策树 | playbook + mental models |
| workflow/{wf}.sh | SOP 走查 | workflows |

## 设计

看 ../references/cli-spec.md.
```

---

## 生成规则（cli_writer.py 实现细节）

`cli_writer.py` 从 `synthesis.md` 解析以下信息，生成 cli/ 子树：

1. **Agentic Protocol** (Section 9 / `## 9.`)
   → 抽出每个 9.X 子节的 标题 / "看什么" / "在哪看" / "输出格式"
   → 生成 `cli/protocol/agentic.sh`，dim_titles/questions/sources 直接 inline 进 bash array

2. **Playbook rules** (Section 2 / `## 2.`)
   → 解析每条「N. 如果 {场景}, 则 {决策}.」格式，按关键词聚类（framework / eval / RAG / observability / multi-agent ...）
   → 每个聚类 ≥ 2 条 → 生成 `cli/decision/{cluster-slug}.sh`，做交互式决策树

3. **Workflows** (Section 4 引用 + research/03-workflows.md)
   → 直接读 `03-workflows.md`，找 `### Workflow N: {title}` 块
   → 抽 入门 SOP 步骤 + 失败模式
   → 每个 workflow 一个 `cli/workflow/{wf-slug}.sh`

4. **Mental models 引用** (Section 1)
   → 不直接生成 script，而是被 `--explain` 模式引用（每个 decision/workflow script 在 explain 中引用对应 mental model 名称 + 一句话）

最少生成数：每个 prototype 至少有
- 1 个 protocol/agentic.sh
- ≥ 1 个 decision/*.sh（如果 playbook ≥ 4 条，至少 2 个）
- ≥ 1 个 workflow/*.sh（如果 workflows ≥ 1）

少于这个数 → cli_writer 报警 + 用占位 stub 脚本，让用户知道 synthesis 需要补足。

---

## 跑通验证标准

每个生成的脚本在「`bash -n {script}` (语法检查) 通过」+「`./script --help` 返回 0」+「`./script --explain` 返回 0 + ≥ 5 行输出」即视为生成成功。完整端到端验证（用户走完交互） 在 Phase 4 中以人工 sanity check 完成。
