# 《唐开元占经》规则黄金集政策

## 数据分层

`development`、`validation`、`holdout` 的 case ID 必须互不相交。每个 case
绑定 passage ID、source fingerprint、卷、天象类别、关系词、复杂度、
可计算性、证据风险、两名独立审核者和标注手册版本。

审核者身份允许使用项目从 pilot ID 确定性生成的匿名席位，不要求外部账号
或披露个人信息。两个席位必须由两个不同真人独立完成；席位生成不构成审核。

development/validation 可保存 reviewed expected label。holdout 的公开 case
不得包含 expected label；标签保存在独立 sealed asset，只有显式
release-gate API 在核验文件 hash、case ID 集合和 guide version 后可读。

## 更新

普通测试和命令只读。更新须独立 PR，包含 before/after、理由、两名审核者、
受影响 split、manifest hash 和批准记录。禁止以连续卷代替分层抽样，也
禁止把 PR-A 的 contract 示例冒充人工 pilot。

## 最低覆盖

人工 pilot 必须跨卷覆盖日、月、五星、二十八宿、客星、彗星、流星、
日月食、云气，以及合、犯、入、守、掩、离、留、逆；并包含可计算、
部分可计算、不可计算、歧义、重复和冲突案例。
