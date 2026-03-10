# Snap3D - AI 驱动的免建模 3D 生成助手
> **版本**：V1.0 (Live Implementation)  
> **状态**：已上线 / 核心功能完备  
> **更新日期**：2026-03-02

---

## 1. 产品概述 (Product Overview)

### 1.1 产品定位
**Snap3D** 是一款面向 3D 打印爱好者和初级创作者的 AI 生产力工具。它利用最新的生成式 AI 技术（Generative AI），将 2D 图像或文本描述直接转换为高质量的 3D 模型，极大降低了 3D 内容创作的门槛，打通了从“创意”到“打印”的最后一公里。

### 1.2 核心价值
*   **零门槛创作**：无需掌握 Blender/CAD 等复杂建模软件。
*   **多模态输入**：支持“以图生图”和“文生图”两种创作模式。
*   **所见即所得**：集成了 WebGL 3D 预览与 AR 预览能力。
*   **打印友好**：输出兼容主流切片软件的 GLB/STL 格式。

---

## 2. 核心功能 (Core Features)

| 模块 | 功能点 | 详细描述 | 状态 |
| :--- | :--- | :--- | :--- |
| **多模态生成** | **Image-to-3D** | 上传 JPG/PNG/WEBP 图片，AI 自动推断深度与结构，生成 3D 模型。 | ✅ 已实现 |
| | **Text-to-3D** | 输入提示词（Prompt），选择艺术风格（真实/卡通/低多边形），生成 3D 模型。 | ✅ 已实现 |
| **交互体验** | **实时预览** | 基于 Google `<model-viewer>` 组件，支持 360° 旋转、缩放、平移查看。 | ✅ 已实现 |
| | **AR 预览** | 支持移动端 WebXR，可将模型投射到现实环境中查看尺寸比例。 | ✅ 已实现 |
| **下载输出** | **多格式支持** | 支持下载 GLB（含材质贴图）和 STL（几何网格）格式。 | ✅ 已实现 |
| **系统反馈** | **智能进度条** | 实时显示生成阶段（Mesh 生成 -> 纹理烘焙），缓解等待焦虑。 | ✅ 已实现 |
| | **错误处理** | 针对 API 超时、额度不足等异常情况的友好提示与重试机制。 | ✅ 已实现 |

---

## 3. 用户工作流 (User Workflow)

    A[用户进入 Snap3D] --> B{选择模式}
    B -->|图片转 3D| C[上传图片 (Drag & Drop)]
    B -->|文字转 3D| D[输入提示词 + 选择风格]
    
    C --> E[点击生成]
    D --> E
    
    E --> F[任务提交 API]
    F --> G{轮询状态 (Polling)}
    
    G -->|Processing| G
    G -->|Failed| H[显示错误提示]
    G -->|Success| I[加载 3D 预览器]
    
    I --> J[交互查看 (旋转/缩放/AR)]
    I --> K[下载模型 (GLB/STL)]
    K --> L[导入切片软件打印]


## 4. 技术架构 (Technical Architecture)

### 4.1 技术栈
*   **前端框架**：Streamlit (Python Web Framework)
    *   *理由*：快速构建数据驱动的 Web 应用，便于集成 Python 后端逻辑。
*   **UI/UX 定制**：CSS3 Injection + Custom HTML
    *   *风格*：Cyberpunk Neon (深色模式 + 霓虹光效)，提升科技感。
    *   *组件*：自定义上传控件、Tab 切换动效、渐变按钮。
*   **3D 渲染引擎**：Google `<model-viewer>` (Web Component)
    *   *特性*：轻量级 WebGL 渲染，原生支持 glTF/GLB，内置 AR Core/AR Kit 支持。
*   **AI 核心层**：
    *   **Meshy API**：主生成引擎，提供高质量的 Mesh 生成与 PBR 纹理烘焙。
    *   **Tripo API**：备用生成引擎（代码已集成适配器），保障服务高可用。
*   **数据处理**：
    *   `Requests`：处理 HTTP/HTTPS 异步请求与轮询。
    *   `Base64/BytesIO`：内存级图片流处理，无需频繁读写磁盘。

### 4.2 目录结构 (Current Project Structure)
```
d:\AI Model\3D product\
├── app.py                  # 应用主入口 (UI布局 + 业务逻辑控制)
├── requirements.txt        # 项目依赖清单
├── Snap3D_PRD.md           # 项目需求文档
├── utils/
│   ├── image_processor.py  # 图片预处理 (压缩/格式校验)
│   ├── meshy_api.py        # Meshy 大模型接口封装
│   ├── tripo_api.py        # Tripo 大模型接口封装
│   └── mock_generator.py   # 测试用 Mock 数据生成器
├── assets/                 # 静态资源 (Logo, Demo Models)
├── temp/                   # 临时文件缓存区
└── output/                 # 生成结果输出区
```

---

## 5. 交互设计细节 (UI/UX Details)

### 5.1 视觉风格
*   **主色调**：深空黑 (`#070b14`)
*   **强调色**：赛博青 (`#00d1d6`) & 电光紫 (`#7c3aed`)
*   **字体**：Inter / JetBrains Mono (代码感)

### 5.2 关键交互
1.  **上传区**：采用大尺寸拖拽区域，支持悬停高亮反馈，增强沉浸感。
2.  **加载态**：摒弃枯燥的 Loading 转圈，使用“生成进度条”+“趣味文案”（如“AI 正在构建拓扑结构...”），提升用户耐受度。
3.  **预览区**：默认开启自动旋转（Auto-rotate），并在右下角提供全屏与 AR 按钮。

---

## 6. 后续迭代规划 (Roadmap)

### V1.1 体验优化 (即将进行)
- [ ] **模型转换器**：集成 `trimesh` 或 `blender-script`，实现 GLB -> STL 的自动流形修复（Manifold Repair），确保 100% 打印成功率。
- [ ] **参数微调**：开放 API 的高级参数（如 `poly_count` 面数控制），让用户在“精细度”与“打印速度”间做权衡。

### V1.2 社区与资产 (规划中)
- [ ] **模型库 (Gallery)**：展示用户生成的精选模型，支持一键 Fork 生成参数。
- [ ] **历史记录**：利用 LocalStorage 或简单的 SQLite 记录用户最近生成的 10 个模型。

### V2.0 商业化探索 (远期)
- [ ] **用户账户体系**：接入 Supabase/Firebase。
- [ ] **高级编辑**：集成简易的 3D 编辑器（如 Three.js Editor），支持模型切割、打孔。

---

> **开发者注**：本项目采用 "Vibe Coding" 模式开发，强调快速原型验证与 AI 能力的深度整合。代码结构模块化，易于扩展新的 AI 模型接口。
