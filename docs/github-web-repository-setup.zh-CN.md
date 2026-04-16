# GitHub 网页端新建仓库与首发流程

这份文档面向维护者，说明如何通过 GitHub 网页端新建仓库，并发布当前项目。

## 1. 前提

在开始前，先准备好：

1. 你的 GitHub 账号已登录
2. 本地已经准备好 GitHub-ready 目录：

```bash
cd /home/rain/projects/new-api-log-statistics
make github-repo
make verify-github
```

生成后的目录是：

```text
dist/new-api-log-statistics-0.2.0-github
```

## 2. 在 GitHub 网页端新建仓库

GitHub 官方文档的网页创建入口是：

- 在任意 GitHub 页面右上角，点击 `+`
- 再点击 `New repository`

官方文档：<https://docs.github.com/zh/repositories/creating-and-managing-repositories/creating-a-new-repository>

你也可以直接打开：

```text
https://github.com/new
```

更方便的方式是使用带参数的预填充链接：

```text
https://github.com/new?name=new-api-log-statistics&visibility=public
```

官方文档也说明了 `name`、`visibility`、`owner` 等 URL 查询参数的用法：
<https://docs.github.com/zh/repositories/creating-and-managing-repositories/creating-a-new-repository>

## 3. 网页上每一项怎么填

创建仓库页面打开后，按下面填：

1. `Owner`
   选择你的个人账号，或者你有权限的组织
2. `Repository name`
   建议填：`new-api-log-statistics`
3. `Description`
   可选，建议填：
   `Independent analytics dashboard for new-api log billing and cost statistics.`
4. `Visibility`
   如果你准备公开发布，选 `Public`
   如果你只是先内部测试，选 `Private`

## 4. 这三个初始化选项怎么选

如果你后面要把本地已经准备好的 GitHub-ready 目录直接推上去，建议：

- 不要勾选 `Add a README file`
- 不要勾选 `Add .gitignore`
- 不要勾选 `Choose a license`

原因很直接：

1. 这些文件在本地 GitHub-ready 目录里已经准备好了
2. GitHub 官方文档也说明，如果你是把现有仓库内容导入 GitHub，预先加这些内容可能引发合并冲突

官方说明出处：
<https://docs.github.com/zh/repositories/creating-and-managing-repositories/creating-a-new-repository>

## 5. 点击创建仓库

确认以上内容后，点击：

```text
Create repository
```

创建成功后，GitHub 会进入仓库的 `Quick setup` 页面。

## 6. 复制仓库地址

在 `Quick setup` 页面，点击 `HTTPS`，复制仓库地址，格式一般类似：

```text
https://github.com/<your-name>/new-api-log-statistics.git
```

如果你使用 SSH，也可以复制：

```text
git@github.com:<your-name>/new-api-log-statistics.git
```

## 7. 把本地 GitHub-ready 目录推上去

进入已经准备好的目录：

```bash
cd /home/rain/projects/new-api-log-statistics/dist/new-api-log-statistics-0.2.0-github
```

这个目录里我已经替你准备好了：

1. `git init`
2. 首个提交
3. `v0.2.0` tag

你只需要补远程并推送：

```bash
git remote add origin <你刚才复制的仓库地址>
git push -u origin main
git push origin v0.2.0
```

## 8. 在 GitHub 网页端创建 Release

代码推上去后，进入你刚创建的仓库页面。

然后按下面操作：

1. 点击右侧或顶部的 `Releases`
2. 点击 `Draft a new release`
3. 选择标签：`v0.2.0`
4. `Release title` 填：

```text
v0.2.0
```

5. `Describe this release`
   可以直接粘贴下面这个文件内容：

- [`docs/release-notes-v0.2.0.md`](/home/rain/projects/new-api-log-statistics/docs/release-notes-v0.2.0.md#L1)

6. 在附件区域上传这个发布包：

- [`new-api-log-statistics-0.2.0.tar.gz`](/home/rain/projects/new-api-log-statistics/dist/new-api-log-statistics-0.2.0.tar.gz)

7. 最后点击 `Publish release`

## 9. 你也可以这样理解整个流程

1. GitHub 网页端负责“创建空仓库”
2. 本地 `git push` 负责“上传源码和 tag”
3. GitHub Release 页面负责“生成版本发布页并上传附件”

## 10. 当前这台机器能不能替你完成

这台机器当前不能直接替你“在 GitHub 网页上创建仓库”，原因是：

1. 我不能替你点击 GitHub 网页
2. 当前环境里也没有可用的 `gh` 命令行工具

我已经检查过：

```text
gh: command not found
```

所以现在最稳的分工是：

1. 你先在 GitHub 网页端创建一个空仓库
2. 把仓库地址发给我
3. 我再继续帮你把远程地址接上、推送命令准备好，必要时也能替你在本地执行推送相关命令
