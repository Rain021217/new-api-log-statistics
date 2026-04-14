# GitHub 授权与认证 FAQ

这份文档整理了在本项目发布流程里，`Git`、`SSH`、`gh` CLI、浏览器授权、Token 授权之间的关系。

## 1. `git push` 和 `gh auth login` 是一回事吗

不是。

- `git push`、`git clone`、`git fetch`
  解决的是 Git 传输认证问题
- `gh auth login`
  解决的是 GitHub API 访问认证问题

在本项目的发布流程里，这两类认证通常会同时存在。

## 2. SSH 密钥认证是做什么的

SSH 密钥主要用于：

- `git clone git@github.com:...`
- `git push`
- `git fetch`
- `git pull`

也就是说，它主要负责 Git 仓库内容传输。

## 3. `gh auth login` 是做什么的

`gh` 是 GitHub CLI。

它除了可以执行 Git 相关辅助命令，还会调用 GitHub API 做这些事情：

- 创建仓库
- 创建 Release
- 查看 PR / Issue
- 上传 Release 附件

这些动作不是单靠 SSH key 就能完成的，所以还需要 `gh` 的登录态。

## 4. 为什么我已经能 `ssh -T git@github.com` 成功了，还要 `gh auth login`

因为这两个认证解决的问题不同。

即使你已经可以：

```bash
ssh -T git@github.com
```

看到：

```text
Hi <username>! You've successfully authenticated, but GitHub does not provide shell access.
```

这也只说明：

1. 你的 SSH key 可用于 Git 传输
2. 不代表 `gh` 已经获得 GitHub API 登录态

## 5. `gh auth login` 的浏览器登录方式是什么

这是 `gh` 默认推荐的方式。

流程是：

1. 运行：

```bash
gh auth login
```

2. 选择：
   - `GitHub.com`
   - `SSH` 或 `HTTPS` 作为 Git protocol
   - `Login with a web browser`
3. 浏览器打开 GitHub 授权页
4. 完成授权后，`gh` 在本机保存一个 token

这个 token 之后供 `gh` 使用，而 Git 操作协议仍然可以保持为 SSH。

## 6. `gh auth login` 里的 “Upload your SSH public key” 是什么

这是在帮助你把当前本机的 SSH 公钥上传到 GitHub 账号。

如果这把 key 之前没有加到 GitHub 账户里，这一步很有用。

但如果你已经能成功执行：

```bash
ssh -T git@github.com
```

那通常说明这把 key 已经可用，可以直接选择：

```text
Skip
```

## 7. 浏览器登录和 Token 登录有什么区别

### 浏览器登录

优点：

- 最省事
- 适合本机交互环境
- 不需要先手动创建 token

缺点：

- 需要浏览器交互

### Token 登录

命令一般是：

```bash
gh auth login --with-token < mytoken.txt
```

或者：

```bash
echo 'YOUR_TOKEN' | gh auth login --with-token
```

优点：

- 适合无头服务器
- 适合自动化
- 更方便做权限和过期时间控制

缺点：

- 需要你自己先去 GitHub 创建 Personal Access Token

## 8. Token 登录用的 token 最少需要哪些权限

`gh auth login --help` 里说明，最少需要：

- `repo`
- `read:org`
- `gist`

这也是当前 `gh` CLI 给出的最低建议范围。

## 9. Token 登录和环境变量 `GH_TOKEN` 有什么关系

两者都可以给 `gh` 提供 GitHub API 登录态。

区别在于：

- `gh auth login --with-token`
  更适合把 token 保存成本地 `gh` 登录态
- `GH_TOKEN`
  更适合临时会话、自动化脚本、CI/CD

示例：

```bash
export GH_TOKEN=your_token_here
gh auth status
```

## 10. 在本项目里推荐哪种方式

推荐分场景：

### 本机维护发布

推荐：

- Git 走 SSH
- `gh` 走浏览器登录

原因是最省事。

### 服务器或自动化发布

推荐：

- Git 走 SSH 或 HTTPS
- `gh` 用 `GH_TOKEN` 或 `--with-token`

原因是更适合无人值守。

## 11. 我怎么确认自己当前到底登录没登录

先看 `gh`：

```bash
gh auth status
```

再看 SSH：

```bash
ssh -T git@github.com
```

两者都成功，才说明：

1. Git 传输认证可用
2. GitHub API 认证也可用

## 12. 本项目当前发布流程依赖哪些认证

如果你要把项目发到 GitHub，通常需要：

1. SSH 认证可用
   用于 `git push`
2. `gh` 登录态可用
   用于：
   - `gh repo create`
   - `gh release create`
   - 上传 Release 附件

## 13. 一句话总结

- SSH key 解决 Git 传输
- `gh` 登录态解决 GitHub API
- 浏览器授权和 Token 授权，本质上都是在给 `gh` 提供 API 认证
