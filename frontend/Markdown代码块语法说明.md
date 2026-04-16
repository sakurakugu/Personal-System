# Markdown 代码块语法说明

本文档记录 `frontend` 当前 Markdown 渲染链已支持的代码块能力，便于和 `other/Firefly` 对照验证。

## 当前已支持

### 基础语法高亮

````md
```ts
const message = 'hello'
console.log(message)
```
````

### 标题栏

````md
```ts title="example.ts"
const answer = 42
```
````

### 行号

````md
```ts showLineNumbers
const first = 1
const second = 2
```
````

### 关闭行号

````md
```ts showLineNumbers=false
const first = 1
const second = 2
```
````

### 自定义起始行号

````md
```ts showLineNumbers startLineNumber=5
const first = 1
const second = 2
```
````

### 行高亮

````md
```ts {1,3-4}
const first = 1
const second = 2
const third = 3
const fourth = 4
```
````

### 组合示例

````md
```ts title="example.ts" showLineNumbers startLineNumber=10 {11-12}
const first = 1
const second = 2
const third = 3
```
````

### 无外框代码块

````md
```ts frame="none"
const answer = 42
console.log(answer)
```
````

### 终端外框

````md
```bash frame="terminal" title="deploy.sh"
pnpm install
pnpm build
pnpm preview
```
````

### 自动换行

````md
```ts wrap
const veryLongMessage = '这一行非常长，用来验证代码块是否会在容器宽度不足时自动换行展示'
```
````

### 关闭自动换行

````md
```ts wrap=false
const veryLongMessage = '这一行非常长，用来验证代码块仍然保持横向滚动而不是自动换行'
```
````

### 保留换行缩进

````md
```ts wrap preserveIndent
function greet() {
  const message = '这是一段很长很长的文本，用来验证自动换行后后续内容仍然保持原有缩进层级'
  return message
}
```
````

### 插入行标记

````md
```ts ins={2-3}
const version = 1
const featureA = true
const featureB = true
console.log(version)
```
````

### 删除行标记

````md
```ts del={2}
const version = 1
const legacyFlag = true
console.log(version)
```
````

## 当前未支持

- 文本级高亮，如 `"given text"`
- 正则高亮，如 `/pattern/`
- `ins="..."` / `del="..."`
- 带标签的行标记
- `collapse={...}` 折叠区间
- ANSI 颜色序列渲染

## 验收建议

可直接把下面示例粘贴到文章或关于页中，快速验证本轮兼容项：

````md
## 代码块兼容性检查

```ts title="line-number-demo.ts" showLineNumbers startLineNumber=5
const first = 1
const second = 2
const third = 3
```

```ts title="line-number-off.ts" showLineNumbers=false
const hidden = true
console.log(hidden)
```

```ts title="highlight-demo.ts" showLineNumbers {2-3}
const alpha = 1
const beta = 2
const gamma = 3
```

```ts frame="none"
const plain = 'no frame'
console.log(plain)
```

```bash frame="terminal" title="deploy.sh"
pnpm install
pnpm build
pnpm preview
```

```ts wrap
const veryLongMessage = '这一行非常长，用来验证代码块是否会在容器宽度不足时自动换行展示'
```

```ts wrap preserveIndent ins={2} del={4}
function greet() {
  const message = '这是一段很长很长的文本，用来验证自动换行后后续内容仍然保持原有缩进层级'
  console.log(message)
  return message
}
```
````

## 说明

- `startLineNumber` 目前仅影响显示出来的行号。
- 行高亮范围仍按代码块内的自然行序解析。
- `ins={...}` / `del={...}` 与普通 `{...}` 高亮可以同时存在，分别对应插入、删除和普通强调三种语义。
- `ins={...}` / `del={...}` 只看元数据指定的行号，不要求代码内容前面额外写 `+` / `-`。
- 插入行和删除行会在行号槽位显示 `+` / `-`；开启行号时表现为 `+ 12` / `- 12`。
- `frame="code"` 为默认表现，不写时也会走普通代码框。
- `frame="terminal"` 会渲染终端风格头部与深色外框。
- `frame="none"` 会移除外层框体，只保留代码内容本身。
- 默认超过 18 行的代码块会自动折叠，并在底部显示“展开剩余 N 行” / “收起代码”按钮。
- `wrap` 会启用块内自动换行，`wrap=false` 保持当前横向滚动行为。
- `preserveIndent` 仅在 `wrap` 开启时生效，用于让折行后的文本继续保持原始缩进层级。
- Mermaid 代码块仍走原有分支，不使用这里的增强代码块外壳。
