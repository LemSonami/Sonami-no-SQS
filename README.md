# Sonami×智测系统

基于Python+tkinter的智能测验系统nya~

支持教师题库管理、学生在线考试、自动判分、错题本、成绩分析，并内置"東方PY鄉"弹幕战小游戏_~~（车万厨狂喜）~~

## 功能概览

### 通用功能
- 🎨 可自定义主题配色（在主界面点击 ⚙ 设置）
- 🔐 所有敏感数据（用户、题库、成绩）均采用 RSA + AES 混合加密存储
- 🖼 学生可导入自定义头像

### 学生端
- 📝 使用加密试卷文件（`.sudasqs`）参加考试，支持密钥验证
- ⏱ 考试倒计时，时间到自动交卷
- 📊 自动判分，展示得分、各题型正确率、逐题解析
- 📁 导出加密答题情况文件（`.ilovesuda`）供教师汇总
- 📖 智能错题本：自动汇总历史错题，支持导出 Markdown 格式
- 📈 近 5 次成绩走势折线图
- 🎮 **東方PY鄉**：将选择题题库转换为弹幕战游戏，答对回血、答错扣血

### 教师端
- 📋 题库管理：新增、编辑、删除、拖拽排序、批量管理题目
- 📄 支持单选、填空、判断三种题型
- 📤 导出加密题库（`.sudasqs`），可设为"试卷"或"游戏"类型，支持自定义题型分布
- 📥 导入学生答题情况（`.ilovesuda`），自动汇总班级成绩
- 🤖 **AI 智能导入 PDF**：通过 DeepSeek API 自动从 PDF 作业中提取选择题和填空题
- 📊 班级成绩报表：最近考试柱状图、学生成绩明细
- 📈 题目情况汇总：各题错误人数、错误答案饼图分布
- 🏆 排行榜：学生总分排名（带头像），切换到此标签页自动播放 BGM

## 运行方式

### 前置要求

- Python 3.10+
- Windows 操作系统（tkinter 主题依赖）

### 安装与启动

```bash
pip install -r requirements.txt
python app.py
```

### 首次运行

系统会自动在 `data/` 目录下初始化：
- 生成 RSA 密钥对（`teacher_private.pem` / `teacher_public.pem`）
- 创建加密的题库文件（`questions.sudasqs`）
- 创建加密的成绩文件（`scores.ilovesuda`）
- 创建设置文件（`settings.json`）

> **注意**：用户账号需要通过 `data/users.xlsx` 预先导入。Excel 格式：`学号 | 姓名 | 密码 | 角色`（角色列填 `S` 或 `T`）。首次导入后会自动加密为 `users.sudausers`。

## 依赖包

| 包 | 用途 |
|---|---|
| `openpyxl` | Excel 格式题库与成绩的读写 |
| `cryptography` | RSA + AES 混合加密，保障数据安全 |
| `pymupdf` (fitz) | PDF 题目导入 |
| `requests` | 调用 DeepSeek API 进行 AI 题目解析 |
| `pygame-ce` | 東方PY鄉小游戏引擎 + 排行榜 BGM |
| `Pillow` | 头像处理、圆角按钮渲染、背景图合成 |

## 项目结构

```text
app.py                 # 程序入口
main_controller.py     # Controller 层：业务逻辑、答题引擎、路由控制
ui_views.py            # View 层：所有 tkinter 界面（登录、考试、结果、错题本等）
data_manager.py        # Model 层：用户、题库、成绩、设置的数据持久化
crypto_utils.py        # 加密工具：RSA + AES 混合加密，密码派生加解密
pdf_importer.py        # PDF 导入：调用 DeepSeek API 智能提取题目
requirements.txt       # Python 依赖

Toho-mpsdream/         # 東方PY鄉 弹幕射击小游戏（pygame）
  main.py              #   游戏主入口，集成答题系统
  boss.py / player.py  #   Boss 与玩家
  bullet.py / sprite.py #  子弹与精灵
  game_functions.py    #   游戏流程控制
  settings.py          #   游戏设置
  ...

assets/                # 静态资源
  ICO.ico              #   应用图标
  bg.png               #   背景图
  loli.ttf             #   界面字体
  dj.mp3               #   排行榜 BGM
  correct_01~03.mp3    #   音效
  out.mp3              #   游戏结束音效

data/                  # 运行时数据（自动生成，加密存储）
  teacher_private.pem  #   RSA 私钥（勿泄露）
  teacher_public.pem   #   RSA 公钥
  questions.sudasqs    #   加密题库
  scores.ilovesuda     #   加密成绩
  users.sudausers      #   加密用户数据
  settings.json        #   用户设置
  avatars.json         #   头像数据
```

## 加密体系

系统采用双层加密保护：

1. **静态数据加密**（题库、成绩、用户文件）：RSA 公钥加密随机 AES 密钥 → AES-CBC 加密数据。只有持有 `teacher_private.pem` 的教师端能解密。
2. **试卷分发加密**：教师设置密码 → PBKDF2（600,000 次迭代）派生密钥 → AES-CBC 加密题库。密码哈希用于学生端验证。
3. **答题情况导出**：学生考试结果经 RSA 公钥加密，仅教师端可解密导入。

## 使用流程

### 教师出卷
1. 登录教师账号 → 在"题库管理"标签页添加/导入题目
2. 点击"导出题库" → 设置密钥（密码）、答题时长、题型分布、题库类型
3. 将生成的 `.sudasqs` 文件分发给学生

### 学生考试
1. 登录学生账号 → 点击"开始考试"
2. 选择 `.sudasqs` 试卷文件，输入教师提供的密钥
3. 在倒计时内完成答题 → 交卷
4. 查看结果 → **导出答题情况**（必须导出后才能看到详细得分）
5. 将 `.ilovesuda` 文件发送给教师

### 教师汇总
1. 在"答题情况汇总"标签页点击"导入答题情况"
2. 批量选择学生的 `.ilovesuda` 文件
3. 查看班级成绩报表、题目正确率统计、排行榜

### AI PDF 导入
1. 在设置中填入 DeepSeek API Key
2. 在"题库管理"标签页点击"导入 PDF"
3. 选择作业 PDF（支持自动匹配参考答案 PDF）
4. AI 自动提取选择题和填空题，插入题库

## 技术亮点

- **MVC 架构**：`data_manager`（Model）、`ui_views`（View）、`main_controller`（Controller）职责清晰分离
- **QuizEngine**：独立的答题引擎，支持随机抽题、按题型分布抽题、缓存答案、自动判分
- **加密文件格式**：`.sudasqs`（题库）、`.ilovesuda`（答题情况）、`.sudausers`（用户）均为自定义加密格式
- **游戏化学习**：Pygame 弹幕射击游戏中嵌入答题机制，答对回血、答错扣血
- **Pillow 渲染圆角按钮**：自绘圆角按钮组件，支持 hover 变暗效果
- **自适应图表**：Canvas 手绘成绩折线图、柱状图、饼图，控件尺寸变化时自动重绘

## 许可

本项目可用于非商用的教育用途或私用。
