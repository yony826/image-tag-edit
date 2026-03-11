# 图片标签处理工具 (Image Tag Editor)

一个基于本地大模型的图片标签自动生成和搜索工具。

## 功能特性

- **图片导入** - 支持选择文件夹批量导入图片，支持拖拽导入
- **AI 标签生成** - 调用本地 LM Studio (Qwen3.5:9B) 大模型自动识别图片内容并生成标签
- **标签搜索** - 支持 AND/OR 组合搜索，快速找到目标图片
- **图片浏览** - 网格形式展示图片，支持大图预览

## 环境要求

- Python 3.10+
- LM Studio (已下载 Qwen3.5:9B 模型)
- Windows/Mac/Linux

## 安装步骤

1. 克隆仓库：
```bash
git clone https://github.com/yony826/image-tag-edit.git
cd image-tag-edit
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 启动 LM Studio：
   - 下载 Qwen3.5:9B 模型
   - 在 LM Studio 中加载模型
   - 启动 API 服务（默认端口 1234）

4. 运行程序：
```bash
python main.py
```
或双击 `run.bat`

## 项目结构

```
├── main.py              # 程序入口
├── image_manager.py     # 图片管理
├── tag_generator.py     # 标签生成 (LM Studio API)
├── search_engine.py     # 搜索引擎
├── metadata_storage.py  # 元数据存储
├── ui_main.py           # UI界面
├── requirements.txt     # 依赖
└── run.bat             # Windows启动脚本
```

## 技术栈

| 技术 | 说明 |
|------|------|
| PyQt5 | 桌面GUI框架 |
| LM Studio API | 本地大模型调用 |
| Qwen3.5:9B | 图片内容识别 |
| JSON | 元数据存储 |

## 许可证

MIT License
