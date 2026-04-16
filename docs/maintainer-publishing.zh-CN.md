# 维护者发布说明

这份文档面向仓库维护者，不面向最终部署用户。

## 1. `.gitignore` 的作用边界

`.gitignore` 只能阻止后续把某些文件加入 Git 跟踪，不能把一个已经混着本地文档、运行日志、私有配置的工作目录自动清洗成可公开仓库。

因此本项目采用两层方案：

1. 用 `.gitignore` 防止本地敏感文件误提交
2. 用独立导出脚本生成干净的 GitHub-ready 目录

## 2. 生成用户发布包

用户发布包面向下载即部署，不包含 `.github` 和维护者文档。

```bash
make release-bundle
make verify-release
```

产物：

- `dist/new-api-log-statistics-0.2.0/`
- `dist/new-api-log-statistics-0.2.0.tar.gz`

## 3. 生成 GitHub-ready 仓库目录

GitHub-ready 目录基于用户发布包二次整理，额外带上：

- `.github/`
- 维护者文档
- release notes

命令：

```bash
make github-repo
make verify-github
```

产物：

- `dist/new-api-log-statistics-0.2.0-github/`
- `dist/new-api-log-statistics-0.2.0-github.tar.gz`

## 4. GitHub 上传步骤

建议不要直接拿当前工作目录上传，而是进入 GitHub-ready 目录：

```bash
cd dist/new-api-log-statistics-0.2.0-github
git init
git add .
git commit -m "Initial release"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

如果你希望按网页端一步一步创建空仓库，再回到本地推送，请先看：

- [`github-web-repository-setup.zh-CN.md`](/home/rain/projects/new-api-log-statistics/docs/github-web-repository-setup.zh-CN.md#L1)

## 5. 打 tag

```bash
git tag -a v0.2.0 -m "Release v0.2.0"
git push origin v0.2.0
```

## 6. GitHub Release 页面

GitHub 的 Release 页面不是通过 `git push` 自动上传附件的。

关系是：

1. `git push` 上传代码
2. `git push --tags` 上传 tag
3. Release 页面基于 tag 创建
4. 附件需要在网页端或 `gh release create` 时上传

推荐把这个文件作为 Release 附件：

- `dist/new-api-log-statistics-0.2.0.tar.gz`

如果使用 `gh` CLI：

```bash
gh release create v0.2.0 \
  /absolute/path/to/dist/new-api-log-statistics-0.2.0.tar.gz \
  --title "v0.2.0" \
  --notes-file docs/release-notes-v0.2.0.md
```
