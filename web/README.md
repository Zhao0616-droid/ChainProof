# web/ — 产品层前端(人 C)

> 一句话:喂 mock JSON 全流程可点,换真引擎后一行不改。

## 技术栈

Vue 3 + Vite 7 + TypeScript + Vue Router + Pinia(设计系统 tokens 见 src/assets/main.css)

## 目录

| 目录 | 内容 |
|---|---|
| src/core 将来放 | 路由/状态/组件库/设计系统(路由与状态已在 router/ stores/ 落地) |
| src/modules/m1-m6 | 六个功能模块,当前为占位页 |
| src/components/ | 通用组件 |
| src/assets/ | 设计 tokens 与静态资源 |

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
