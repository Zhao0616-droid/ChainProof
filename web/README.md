# web/ — 产品层前端(人 C)

> 一句话:上传 → 分析 → 结果页(证据/补丁/源码定位)真实全流程,契约以 schemas/ 为准、前端只读渲染。

## 技术栈

Vue 3 + Vite 7 + TypeScript + Vue Router + Pinia(设计系统 tokens 见 src/assets/main.css)

## 目录

| 目录 | 内容 |
|---|---|
| src/api.ts | fetch 封装(JSON 解析 + 错误提取 detail) |
| src/types.ts | 与 schemas/analysis_result.json 对应的接口类型 |
| src/stores/ | Pinia 状态(当前分析记录) |
| src/views/ | HomeView(上传/最近列表)、ResultView(结果页) |
| src/router/ | 路由:/ 与 /result/:id |
| src/assets/ | 设计 tokens 与样式 |

M1-M6 其余模块(项目空间/规约库/报告导出/批量审计/知识库)后续按排期实现。

## 运行

```bash
cd web
npm install
npm run dev        # 开发服务器,/api 自动代理到 127.0.0.1:8000
npm run build      # 类型检查 + 构建
```

## 纪律

- 只在本树内加文件;契约以 `schemas/` 为准,前端只读渲染。
- 提交信息格式:`[C] 模块: 做了什么`
