# NutriAI - AI Vision 修复记录

> 记录日期：2026-04-11  
> 修复者：Claude AI Assistant

---

## 问题描述

**AI Vision 功能无法正常工作**，尽管用户上传的图片非常清晰且提供了提示词，但 AI 仍然无法正确分析图片中的食物。

---

## 根本原因分析

经过对后端代码的全面检查，发现以下问题：

### 问题 1：GEMINI_VISION_MODEL 配置错误 ⚠️（主要原因）

**文件：** `.env`

**问题配置：**
```env
GEMINI_VISION_MODEL=gemini-2.5-flash-image
```

**问题说明：**
- `gemini-2.5-flash-image` 不是有效的 Gemini 模型名称
- 这导致 AI Service 在初始化时使用错误的模型，或者无法正确调用 Vision API

**正确配置：**
```env
GEMINI_VISION_MODEL=gemini-1.5-flash
```

**有效的 Gemini 模型名称：**
| 模型名称 | 状态 | 说明 |
|---------|------|------|
| `gemini-1.5-flash` | ✅ 有效 | 快速响应，适合日常使用 |
| `gemini-1.5-pro` | ✅ 有效 | 更强能力，适合复杂任务 |
| `gemini-2.0-flash` | ✅ 有效 | 最新版本，性能优化 |
| `gemini-2.5-flash-image` | ❌ 无效 | 不存在的模型名称 |

---

### 问题 2：Redis 连接配置硬编码 ⚠️（次要原因）

**文件：** `ai_services/app/services/vision_service.py`

**问题代码：**
```python
self.redis_client = redis.Redis(
    host='nutriai_redis',  # Docker service name
    ...
)
```

**问题说明：**
- 硬编码了 Redis 主机名为 `nutriai_redis`
- 但在 Docker Compose 网络中，Redis 服务名是 `redis`
- 这导致 AI Service 无法连接 Redis 进行缓存

**修复后代码：**
```python
def _initialize_redis(self) -> None:
    """Initialize Redis client for caching"""
    try:
        # 获取 Redis 连接配置 - 优先使用环境变量，否则使用 Docker 服务名 'redis'
        redis_host = os.environ.get('REDIS_HOST', 'redis')
        redis_port = int(os.environ.get('REDIS_PORT', '6379'))
        redis_db = int(os.environ.get('REDIS_DB', '0'))
        redis_password = os.environ.get('REDIS_PASSWORD') or None
        
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=redis_password,
            decode_responses=True,
            socket_connect_timeout=2
        )
```

---

## 已修复的文件

| 文件 | 修改内容 |
|------|----------|
| `.env` | `GEMINI_VISION_MODEL` 从 `gemini-2.5-flash-image` 改为 `gemini-1.5-flash` |
| `ai_services/.env.example` | `GEMINI_VISION_MODEL` 从 `gemini-flash-latest` 改为 `gemini-1.5-flash` |
| `docker-compose.yml` | 默认值从 `gemini-flash-latest` 改为 `gemini-1.5-flash` |
| `ai_services/app/services/vision_service.py` | Redis 连接改为从环境变量读取，不再硬编码 |

---

## 解决方案步骤

### 步骤 1：更新 .env 文件
确保 `GEMINI_VISION_MODEL` 设置为有效的模型名称：
```env
GEMINI_VISION_MODEL=gemini-1.5-flash
```

### 步骤 2：确保 Redis 环境变量配置正确
在 `docker-compose.yml` 中，AI Service 已经配置了 Redis 连接：
```yaml
- REDIS_URL=redis://redis:6379/1
```

### 步骤 3：重启服务
```bash
# 停止并重新启动 AI Service
docker-compose down ai_service
docker-compose up -d ai_service
```

### 步骤 4：验证修复
访问 AI Service 健康检查端点：
```
GET http://localhost:8001/vision/health
```

预期响应：
```json
{
  "status": "healthy",
  "message": "Vision service ready",
  "vision_enabled": true,
  "model": "gemini-1.5-flash"
}
```

---

## AI Vision 工作流程（参考）

```
┌─────────────────┐
│   用户上传图片   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│  1. 图片验证 & 压缩 (image_processing.py)           │
│     - 验证文件格式和大小                             │
│     - 压缩到 384x384 像素                           │
└─────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│  2. 调用 Gemini Vision API (vision_service.py)      │
│     - 使用 gemini-1.5-flash 模型                    │
│     - Prompt 优化识别越南食物                       │
│     - JSON 解析响应                                 │
└─────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│  3. 搜索数据库匹配 (backend API)                     │
│     - 搜索 recipes 表                               │
│     - 搜索 foods 表                                 │
│     - 获取 portion presets                          │
└─────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│  4. 返回结果给前端                                  │
│     - food_name: 识别出的食物名称                    │
│     - database_match: 数据库匹配信息                  │
│     - portion_presets: 份量选项                      │
└─────────────────────────────────────────────────────┘
```

---

## 常见问题排查

### Q1: AI 仍然无法识别食物
**检查项：**
1. ✅ `GEMINI_VISION_MODEL` 是否为 `gemini-1.5-flash`
2. ✅ `GOOGLE_API_KEY` 是否正确配置且有效
3. ✅ 图片格式是否为 JPG/PNG/WEBP
4. ✅ 图片大小是否小于 10MB

### Q2: 数据库匹配为 null
**检查项：**
1. ✅ Backend 服务是否运行在端口 8000
2. ✅ recipes 和 foods 表是否有数据
3. ✅ AI Service 是否能访问 `http://backend:8000`

### Q3: 部分选项为空
**说明：** 这是正常行为。当数据库中没有匹配的食谱或食物时，`alternatives` 和 `portion_presets` 可能为空。用户仍然可以选择自定义份量。

---

## 未来改进建议

1. **添加更详细的日志**：在 vision_service.py 中添加更详细的日志，便于排查问题
2. **增加模型选择配置**：允许用户选择不同的 Vision 模型
3. **优化 Prompt**：根据实际使用情况持续优化食物识别 Prompt
4. **添加 Fallback 机制**：当 Vision API 失败时，自动降级到基于文本的搜索

---

## 参考文档

- [Gemini API 文档](https://ai.google.dev/docs/gemini_api_overview)
- [Vision Service 源码](../ai_services/app/services/vision_service.py)
- [Vision Routes 源码](../ai_services/app/routes/vision.py)
