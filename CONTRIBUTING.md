# Contributing

欢迎补充方法论、组件、模板。提交前请保证下面四条全绿。

## 内容规范

- **与题材无关**：不写具体作品的人物名、地点名、专有道具；示例用通用题材（都市悬疑 / 科幻 / 古装等）。
- **可执行**：每条规则尽量给出参数、字段、代码片段或校验方式，避免"要注意真实感"这类空话。
- **有出处**：引用外部项目时写仓库名 + 用途，不复制代码。
- **不写死路径**：只用相对路径或 `~/.workbuddy-ai/skills/` 这类通用位置。

## 目录约定

| 类型 | 位置 |
|---|---|
| 总流程、质量门、铁律 | `SKILL.md` |
| 方法论细节 | `references/<topic>.md` |
| 可直接复制的代码/模板 | `templates/project/` |
| 可运行示例 | `examples/<name>/` |

新增 reference 时，在 `SKILL.md` 第 9 节「参考手册」加一行索引。

## 提交前检查

```bash
# 1. Python 语法
python3 -m py_compile templates/project/*.py

# 2. JS 语法
node --experimental-default-type=module --check templates/project/compute-state.js
node --experimental-default-type=module --check templates/project/export.js

# 3. JSON
node -e "JSON.parse(require('fs').readFileSync('templates/project/story.schema.json','utf8'))"

# 4. 示例可校验
python3 templates/project/validate_shots.py examples/minimal/story.json

# 5. 无绝对路径、无专有名词（只扫内容目录，避免命中检查脚本自身）
grep -rn "/Users/" SKILL.md references templates examples README.md CHANGELOG.md && echo "found absolute path"
grep -rnE "北冕|沈洛|老郑|烬海|灰海|浪谷|眼斑|搪瓷" SKILL.md references templates examples README.md CHANGELOG.md && echo "found story noun"
```

CI（`.github/workflows/validate.yml`）会跑同样的检查。

## 提交信息

```
feat(references): add rain-and-wet-surface recipe
fix(templates): correct shot duration check
docs: clarify authored-cuts camera mode
```
