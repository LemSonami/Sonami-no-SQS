# 智能测验系统

这是一个按 MVC 架构实现的 Python 大作业项目，使用 `tkinter` 构建 GUI，使用 `openpyxl` 读写 Excel 题库和成绩文件。

## 运行方式

```powershell
pip install -r requirements.txt
python app.py
```

首次运行会自动创建：

- `data/users.json`：用户账号
- `data/questions.xlsx`：题库
- `data/scores.xlsx`：成绩记录

## 默认账号

| 角色 | 账号 | 密码 |
| --- | --- | --- |
| 教师 | `teacher` | `123456` |
| 学生 | `student` | `123456` |

## 项目结构

```text
app.py                # 程序启动入口
data_manager.py       # Model 层：用户、题库、成绩持久化
ui_views.py           # View 层：所有 tkinter 界面
main_controller.py    # Controller 层：路由、答题和判分逻辑
requirements.txt      # Python 依赖
```

## 已实现功能

- 学生/教师双角色登录与注册
- 教师端题库新增、删除、查看
- 学生端随机抽题考试
- 单选、填空、判断题支持
- 倒计时与时间到自动交卷
- 未作答提交确认
- 自动判分、错题汇总、答案解析
- 学生成绩历史和近 5 次折线图
- 教师端班级成绩报表
- 文件缺失自动初始化与读取异常提示

## 答辩演示建议

1. 使用 `teacher/123456` 登录教师端，新增一道题目。
2. 退出后使用 `student/123456` 登录学生端。
3. 点击开始考试，完成几道题并故意答错一道。
4. 交卷后展示得分、解析、题型正确率。
5. 返回主页查看成绩走势，再进入错题本展示错题解析。

## 技术亮点

- `QuestionBank` 封装了 `openpyxl.load_workbook`、行遍历、题目新增和删除。
- `ScoreManager` 将成绩、错题 ID、题型统计写入 `scores.xlsx`。
- `QuizEngine` 独立负责随机抽题、缓存答案、判分和生成错题集。
- GUI 与业务逻辑分离，界面切换统一由 `AppController` 管理。
