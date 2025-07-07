# Assets 资产文件夹说明

本文件夹包含VideoMaker项目的所有输入资源、示例文件和模板文件。

## 📁 目录结构

### input/ - 输入资源
存放用户的原始输入文件：
- `images/` - 源图片文件（PNG, JPG, WEBP等）
- `audio/` - 源音频文件（MP3, WAV, AAC等）  
- `videos/` - 源视频文件（MP4, MOV, AVI等）

### examples/ - 示例文件
包含完整的示例，帮助用户快速上手：
- `video_plan_example.json` - 完整的标准视频规划示例
- `video_plan.json` - 另一个视频规划示例
- `demo_script.txt` - 演示脚本文件

### templates/ - 模板文件
提供各种场景的模板，加速项目创建：
- `plans/` - 视频规划模板
  - `simple_template.json` - 简单项目模板
- `scripts/` - 脚本模板
  - `narration_template.txt` - 旁白脚本模板
- `configs/` - 配置模板
  - `development_config.yaml` - 开发环境配置模板

## 🚀 快速开始

### 1. 准备输入文件
将您的源图片放置到 `input/images/` 目录中：
```bash
cp your_image.jpg assets/input/images/
```

### 2. 使用模板创建项目
复制模板文件并根据需要修改：
```bash
cp assets/templates/plans/simple_template.json my_project.json
```

### 3. 运行VideoMaker
```bash
python main.py my_project.json
```

## 📋 文件规范

### 支持的文件格式
- **图片**: PNG, JPG, JPEG, WEBP, BMP
- **音频**: MP3, WAV, AAC, OGG
- **视频**: MP4, MOV, AVI, MKV

### 文件大小限制
- 图片: 最大 50MB
- 音频: 最大 100MB  
- 视频: 最大 500MB

### 文件命名建议
使用清晰的命名规范：
- `{项目名}_{用途}_{序号}.{扩展名}`
- 示例: `产品介绍_主图_01.png`

## 💡 使用提示

1. **从示例开始**: 新用户建议从 `examples/video_plan_example.json` 开始了解数据结构
2. **使用模板**: 利用 `templates/` 目录中的模板快速创建项目
3. **合理组织**: 按项目分类组织您的输入文件
4. **备份重要文件**: templates 和 examples 会纳入版本控制，input 目录建议用户自行备份

## 🔗 相关文档

- [系统设计文档](../docs/system_design.md) - 完整的系统架构说明
- [用户指南](../README.md) - 详细的使用说明
- [API参考](../docs/api_reference.md) - API接口文档 