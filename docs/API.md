# 多Agent协作写小说系统 - API接口文档

## 基础信息

- **Base URL**: `http://localhost:8000/api/v1`
- **Content-Type**: `application/json`

## 项目管理

### 创建项目

```http
POST /projects
```

**请求参数**:
```json
{
  "title": "星际武侠传",
  "genre": "科幻武侠",
  "user_input": "故事描述...",
  "target_chapters": 20
}
```

**响应**:
```json
{
  "success": true,
  "project_id": "proj_001",
  "outline": {
    "story_summary": "故事概要...",
    "chapters": [...]
  }
}
```

### 获取项目列表

```http
GET /projects
```

**响应**:
```json
{
  "projects": [
    {
      "project_id": "proj_001",
      "title": "星际武侠传",
      "status": "in_progress",
      "progress": 30
    }
  ]
}
```

### 获取项目详情

```http
GET /projects/{project_id}
```

**响应**:
```json
{
  "project_id": "proj_001",
  "title": "星际武侠传",
  "genre": "科幻武侠",
  "outline": {...},
  "world": {...},
  "characters": {...},
  "chapters": {...},
  "status": "in_progress"
}
```

## 章节管理

### 撰写章节

```http
POST /projects/{project_id}/chapters/{chapter_num}/write
```

**请求参数**:
```json
{
  "writer_style": "金庸风格",
  "target_word_count": 3500
}
```

**响应**:
```json
{
  "success": true,
  "chapter_num": 1,
  "title": "第一章标题",
  "content": "章节内容...",
  "word_count": 3600,
  "agents_involved": ["planner", "writer", "editor"]
}
```

### 重写章节

```http
POST /projects/{project_id}/chapters/{chapter_num}/rewrite
```

**请求参数**:
```json
{
  "feedback": "需要加强场景描写...",
  "edit_level": "medium"
}
```

### 获取章节内容

```http
GET /projects/{project_id}/chapters/{chapter_num}
```

**响应**:
```json
{
  "chapter_num": 1,
  "title": "第一章标题",
  "content": "章节内容...",
  "word_count": 3600,
  "status": "completed",
  "versions": [...]
}
```

## 作家风格

### 创建风格

```http
POST /styles
```

**请求参数**:
```json
{
  "name": "金庸武侠风格",
  "description": "金庸武侠小说的经典风格",
  "sample_texts": [
    "文本片段1...",
    "文本片段2..."
  ]
}
```

**响应**:
```json
{
  "success": true,
  "style": {
    "name": "金庸武侠风格",
    "description": "金庸武侠小说的经典风格",
    "vocabulary_features": ["古典词汇", "意境深远"],
    "sentence_patterns": ["长短结合", "对仗工整"],
    "system_prompt": "系统提示词..."
  }
}
```

### 获取风格列表

```http
GET /styles
```

**响应**:
```json
{
  "styles": [
    {
      "name": "金庸武侠风格",
      "description": "金庸武侠小说的经典风格"
    },
    {
      "name": "刘慈欣科幻风格",
      "description": "硬科幻风格，宏大叙事"
    }
  ]
}
```

### 混合风格

```http
POST /styles/mix
```

**请求参数**:
```json
{
  "style_names": ["金庸武侠风格", "刘慈欣科幻风格"],
  "mix_name": "科幻武侠混合风格",
  "proportions": [0.6, 0.4]
}
```

**响应**:
```json
{
  "success": true,
  "mixed_style": {
    "name": "科幻武侠混合风格",
    "description": "混合风格: 金庸武侠风格, 刘慈欣科幻风格",
    "vocabulary_features": [...],
    "system_prompt": "..."
  }
}
```

## Agent管理

### 获取Agent列表

```http
GET /agents
```

**响应**:
```json
{
  "agents": [
    {
      "agent_id": "planner_001",
      "name": "首席规划师",
      "role": "planner",
      "status": "idle"
    },
    {
      "agent_id": "writer_001",
      "name": "主笔作家",
      "role": "writer",
      "status": "working"
    }
  ]
}
```

### 获取Agent状态

```http
GET /agents/{agent_id}/status
```

**响应**:
```json
{
  "agent_id": "writer_001",
  "name": "主笔作家",
  "role": "writer",
  "status": "working",
  "stats": {
    "tasks_completed": 5,
    "tokens_consumed": 15000,
    "total_time": 120.5
  }
}
```

## 工作流

### 执行工作流

```http
POST /workflows/execute
```

**请求参数**:
```json
{
  "workflow_type": "sequential",
  "tasks": [
    {
      "type": "create_outline",
      "agent_role": "planner",
      "params": {...}
    },
    {
      "type": "create_world",
      "agent_role": "world_builder",
      "params": {...},
      "dependencies": [0]
    }
  ]
}
```

**响应**:
```json
{
  "workflow_id": "wf_001",
  "status": "completed",
  "results": [...]
}
```

### 获取工作流状态

```http
GET /workflows/{workflow_id}
```

**响应**:
```json
{
  "workflow_id": "wf_001",
  "status": "running",
  "current_task": 2,
  "total_tasks": 5,
  "progress": 40
}
```

## 错误处理

### 错误响应格式

```json
{
  "success": false,
  "error": {
    "code": "INVALID_REQUEST",
    "message": "请求参数错误",
    "details": {
      "field": "title",
      "issue": "标题不能为空"
    }
  }
}
```

### 错误码列表

| 错误码 | 说明 |
|--------|------|
| INVALID_REQUEST | 请求参数错误 |
| NOT_FOUND | 资源不存在 |
| AGENT_ERROR | Agent执行错误 |
| LLM_ERROR | LLM调用错误 |
| RATE_LIMIT | 请求频率限制 |
| INTERNAL_ERROR | 内部服务器错误 |

## WebSocket接口

### 实时进度

```
WS /ws/progress/{project_id}
```

**消息格式**:
```json
{
  "type": "chapter_progress",
  "data": {
    "chapter_num": 1,
    "agent": "writer_001",
    "status": "writing",
    "progress": 45,
    "message": "正在撰写场景描写..."
  }
}
```

## 认证

### 获取Token

```http
POST /auth/token
```

**请求参数**:
```json
{
  "username": "user@example.com",
  "password": "password"
}
```

**响应**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### 使用Token

```http
GET /projects
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```
