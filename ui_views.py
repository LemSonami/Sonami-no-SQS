from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Dict, List, Optional

from data_manager import Question

BG = "#f4f7fb"
PANEL = "#ffffff"
TEXT = "#1f2937"
MUTED = "#64748b"
PRIMARY = "#2563eb"
SUCCESS = "#16a34a"
DANGER = "#dc2626"
BORDER = "#d8dee9"

def _set_bg_image(frame, opacity: float = 0.35) -> None:
    from pathlib import Path
    from io import BytesIO
    from PIL import Image, ImageTk

    bg_path = Path(__file__).resolve().parent / "assets" / "bg.png"
    if not bg_path.exists():
        return
    try:
        img = Image.open(bg_path).convert("RGBA")

        bg_rgb = (0xF4, 0xF7, 0xFB, 255)
        overlay = Image.new("RGBA", img.size, bg_rgb)
        blended = Image.blend(overlay, img, opacity)

        blended = blended.resize((1, 1), Image.LANCZOS)

        blended = Image.open(bg_path).convert("RGBA")
        blended = Image.blend(
            Image.new("RGBA", blended.size, bg_rgb), blended, opacity
        )
        photo = ImageTk.PhotoImage(blended)
        lbl = tk.Label(frame, image=photo, bg=BG, bd=0)
        lbl.image = photo
        lbl.place(relwidth=1, relheight=1, x=0, y=0)
        lbl.lower()
    except Exception:
        pass

FONT_FAMILY = "Lolita"

class RoundedButton(tk.Label):

    _img_cache: dict = {}
    _instances: list = []

    @classmethod
    def update_all_fonts(cls, font_family: str) -> None:
        for btn in cls._instances:
            try:
                btn.configure(font=(font_family, btn._font_size))
            except Exception:
                pass

    def __init__(self, parent, text: str, command=None, width=120, height=36,
                 bg="#e5e7eb", fg="#1f2937", radius=8, font=None):
        self._bg_color = bg
        self._fg = fg
        self._r = radius
        self._btn_w = width
        self._btn_h = height
        self._cmd = command
        self._font_size = font[1] if font else 11
        self._font = font or (FONT_FAMILY, self._font_size)

        RoundedButton._instances.append(self)

        img = self._make_img(bg)
        super().__init__(parent, image=img, text=text, compound="center",
                         fg=fg, font=self._font, bd=0, bg=BG)
        self.image = img

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)

    def _make_img(self, color: str):
        from PIL import Image, ImageDraw, ImageTk

        key = (color, self._btn_w, self._btn_h, self._r)
        if key in RoundedButton._img_cache:
            return RoundedButton._img_cache[key]

        border_c = _darken(color, 0.75)
        img = Image.new("RGBA", (self._btn_w, self._btn_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        draw.rounded_rectangle([(0, 0), (self._btn_w - 1, self._btn_h - 1)],
                               radius=self._r, fill=border_c)

        draw.rounded_rectangle([(2, 2), (self._btn_w - 3, self._btn_h - 3)],
                               radius=self._r - 1, fill=color)
        photo = ImageTk.PhotoImage(img)
        RoundedButton._img_cache[key] = photo
        return photo

    def _set_img(self, color: str):
        img = self._make_img(color)
        self.configure(image=img)
        self.image = img

    def _on_enter(self, _event):
        self.config(cursor="hand2")
        self._set_img(_darken(self._bg_color, 0.88))

    def _on_leave(self, _event):
        self.config(cursor="")
        self._set_img(self._bg_color)

    def _on_click(self, _event):
        if self._cmd:
            self._cmd()

class BaseFrame(ttk.Frame):
    def __init__(self, master, controller) -> None:
        super().__init__(master, padding=18)
        self.controller = controller
        self.configure(style="App.TFrame")

    def title(self, text: str, subtitle: str = "") -> None:
        ttk.Label(self, text=text, style="Title.TLabel").pack(anchor="w")
        if subtitle:
            ttk.Label(self, text=subtitle, style="Muted.TLabel").pack(anchor="w", pady=(4, 16))

    def make_button_row(self, parent=None):
        row = ttk.Frame(parent or self, style="App.TFrame")
        row.pack(fill="x", pady=12)
        return row

class LoginWindow(BaseFrame):
    def __init__(self, master, controller) -> None:
        super().__init__(master, controller)
        self.title("Sonami×智测系统 V0.1.0", "请使用学号、姓名、密码登录")

        ttk.Button(self, text="⚙ 设置", command=controller.show_settings).place(relx=1.0, y=0, anchor="ne")

        card = ttk.Frame(self, style="Card.TFrame", padding=24)
        card.pack(fill="x", padx=120, pady=28)

        import json
        from data_manager import LOGIN_CACHE_FILE
        cached = {"student_id": "", "name": "", "password": ""}
        try:
            if LOGIN_CACHE_FILE.exists():
                cached = json.loads(LOGIN_CACHE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

        ttk.Label(card, text="学号").grid(row=0, column=0, sticky="w", pady=8)
        self.student_id_var = tk.StringVar(value=cached.get("student_id", ""))
        ttk.Entry(card, textvariable=self.student_id_var).grid(row=0, column=1, sticky="ew", pady=8)

        ttk.Label(card, text="姓名").grid(row=1, column=0, sticky="w", pady=8)
        self.name_var = tk.StringVar(value=cached.get("name", ""))
        ttk.Entry(card, textvariable=self.name_var).grid(row=1, column=1, sticky="ew", pady=8)

        ttk.Label(card, text="密码").grid(row=2, column=0, sticky="w", pady=8)
        self.password_var = tk.StringVar(value=cached.get("password", ""))
        ttk.Entry(card, textvariable=self.password_var, show="*").grid(
            row=2, column=1, sticky="ew", pady=8
        )

        card.columnconfigure(1, weight=1)
        buttons = ttk.Frame(card, style="Card.TFrame")
        buttons.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(18, 0))
        RoundedButton(buttons, text="登录", command=self.handle_login,
                      width=100).pack(side="left")

    def handle_login(self) -> None:
        student_id = self.student_id_var.get().strip()
        name = self.name_var.get().strip()
        password = self.password_var.get()
        if not student_id or not name or not password:
            messagebox.showwarning("无人在意", "请输入学号、姓名和密码")
            return
        if not self.controller.login(student_id, name, password):
            messagebox.showerror("登录失败", "学号、姓名或密码错误")

class RegisterDialog(tk.Toplevel):
    def __init__(self, parent, controller) -> None:
        super().__init__(parent)
        self.controller = controller
        self.title("注册账号")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.transient(parent)
        self.grab_set()

        body = ttk.Frame(self, padding=18, style="App.TFrame")
        body.pack(fill="both", expand=True)

        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.student_id_var = tk.StringVar()
        self.role_var = tk.StringVar(value="student")

        fields = [
            ("账号", self.username_var, False),
            ("密码", self.password_var, True),
            ("姓名", self.name_var, False),
            ("学号", self.student_id_var, False),
        ]
        for row, (label, var, secret) in enumerate(fields):
            ttk.Label(body, text=label).grid(row=row, column=0, sticky="w", pady=6)
            ttk.Entry(body, textvariable=var, show="*" if secret else "").grid(
                row=row, column=1, sticky="ew", pady=6
            )

        ttk.Label(body, text="角色").grid(row=4, column=0, sticky="w", pady=6)
        role_box = ttk.Frame(body, style="App.TFrame")
        role_box.grid(row=4, column=1, sticky="w", pady=6)
        ttk.Radiobutton(role_box, text="学生", value="student", variable=self.role_var).pack(
            side="left", padx=(0, 12)
        )
        ttk.Radiobutton(role_box, text="教师", value="teacher", variable=self.role_var).pack(
            side="left"
        )

        body.columnconfigure(1, weight=1)
        ttk.Button(body, text="提交注册", style="Primary.TButton", command=self.submit).grid(
            row=5, column=0, columnspan=2, sticky="ew", pady=(14, 0)
        )

    def submit(self) -> None:
        try:
            self.controller.register_user(
                self.username_var.get(),
                self.password_var.get(),
                self.role_var.get(),
                self.name_var.get(),
                self.student_id_var.get(),
            )
        except ValueError as exc:
            messagebox.showwarning("注册失败", str(exc))
            return
        messagebox.showinfo("注册成功", "账号已创建，请返回登录")
        self.destroy()

class StudentDashboard(BaseFrame):
    def __init__(self, master, controller) -> None:
        super().__init__(master, controller)
        _set_bg_image(self, 0.60)
        user = controller.current_user or {}
        student_id = user.get("student_id", "")
        best = controller.score_manager.best_score(user.get("username", student_id))

        title_frame = ttk.Frame(self, style="App.TFrame")
        title_frame.pack(fill="x")

        self._avatar_photo = None
        avatar_b64 = user.get("avatar_base64", "")
        if not avatar_b64:
            from data_manager import load_avatar
            avatar_b64 = load_avatar(student_id)
        if avatar_b64:
            try:
                from data_manager import avatar_to_tk_image
                self._avatar_photo = avatar_to_tk_image(avatar_b64, 56)
                tk.Label(title_frame, image=self._avatar_photo, bg=BG, bd=0).pack(side="left", padx=(0, 10))
            except Exception:
                pass

        title_text = f"欢迎，{user.get('name', user.get('username', '学生'))}"
        ttk.Label(title_frame, text=title_text, style="Title.TLabel").pack(side="left")
        ttk.Label(self, text=f"历史最高分：{best}", style="Muted.TLabel").pack(anchor="w", pady=(4, 16))

        top = ttk.Frame(self, style="App.TFrame")
        top.pack(fill="x")
        RoundedButton(top, text="开始考试", command=self._start_exam_with_file,
                      width=110).pack(side="left", padx=(0, 10))
        RoundedButton(top, text="東方PY鄉", command=self._play_game, width=100).pack(side="left", padx=(0, 10))
        RoundedButton(top, text="错题本", command=controller.show_wrong_book, width=90).pack(side="left", padx=(0, 10))
        RoundedButton(top, text="退出登录", command=controller.show_login, width=90).pack(side="right")

        ttk.Button(self, text="导入头像", command=self._import_avatar).place(relx=1.0, x=-150, y=4, anchor="ne")
        ttk.Button(self, text="⚙ 设置", command=controller.show_settings).place(relx=1.0, y=4, anchor="ne")

        content = ttk.Frame(self, style="App.TFrame")
        content.pack(fill="both", expand=True, pady=18)

        left = ttk.Frame(content, style="Card.TFrame", padding=16)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        ttk.Label(left, text="近 5 次成绩走势", style="Section.TLabel").pack(anchor="w")
        self.chart = tk.Canvas(left, height=260, bg=PANEL, highlightthickness=0)
        self.chart.pack(fill="both", expand=True, pady=(12, 0))
        self.draw_score_chart(controller.score_manager.recent_scores(user.get("username", "")))

        right = ttk.Frame(content, style="Card.TFrame", padding=16)
        right.pack(side="left", fill="both", expand=True, padx=(10, 0))
        ttk.Label(right, text="最近成绩", style="Section.TLabel").pack(anchor="w")
        columns = ("time", "score", "total")
        table = ttk.Treeview(right, columns=columns, show="headings", height=8)
        table.heading("time", text="考试时间")
        table.heading("score", text="得分")
        table.heading("total", text="总分")
        table.column("time", width=150)
        table.column("score", width=70, anchor="center")
        table.column("total", width=70, anchor="center")
        table.pack(fill="both", expand=True, pady=(12, 0))
        for record in reversed(controller.score_manager.recent_scores(user.get("username", ""), 8)):
            table.insert("", "end", values=(record["exam_time"], record["score"], record["total"]))

    def draw_score_chart(self, records: List[Dict[str, object]]) -> None:
        self.chart.update_idletasks()
        width = max(420, self.chart.winfo_width())
        height = 240
        pad = 32
        self.chart.delete("all")
        self.chart.create_line(pad, height - pad, width - pad, height - pad, fill=BORDER)
        self.chart.create_line(pad, pad, pad, height - pad, fill=BORDER)
        if not records:
            self.chart.create_text(width / 2, height / 2, text="暂无成绩", fill=MUTED, font=("Microsoft YaHei", 14))
            return

        max_total = max(int(item["total"]) for item in records) or 100
        points = []
        for index, record in enumerate(records):
            x = pad + index * ((width - pad * 2) / max(1, len(records) - 1))
            y = height - pad - (int(record["score"]) / max_total) * (height - pad * 2)
            points.append((x, y))
        for start, end in zip(points, points[1:]):
            self.chart.create_line(*start, *end, fill=PRIMARY, width=3)
        for index, (x, y) in enumerate(points, start=1):
            self.chart.create_oval(x - 5, y - 5, x + 5, y + 5, fill=PRIMARY, outline="")
            self.chart.create_text(x, height - 12, text=str(index), fill=MUTED)
            self.chart.create_text(x, y - 16, text=str(records[index - 1]["score"]), fill=TEXT)

    def _start_exam_with_file(self) -> None:
        from tkinter import filedialog, simpledialog

        path = filedialog.askopenfilename(
            parent=self, title="选择试卷文件（.sudasqs）",
            filetypes=[("加密试卷文件", "*.sudasqs"), ("所有文件", "*.*")],
        )
        if not path:
            return
        password = simpledialog.askstring("输入试卷密钥", "请输入该试卷的密钥（密码）：", parent=self)
        if not password:
            return
        try:
            exam_uuid, duration, distribution, _, questions = \
                self.controller.import_question_bank_for_exam(path, password.strip())
        except ValueError:
            messagebox.showerror("密钥错误", "密钥不正确或试卷文件已损坏，请重试。")
            return
        except Exception as exc:
            messagebox.showerror("导入失败", f"无法读取试卷文件：{exc}")
            return

        username = self.controller.current_user.get("username", "")
        if exam_uuid and self.controller.exam_tracker.is_completed(username, exam_uuid):
            messagebox.showwarning(
                "⚠ 重复作答",
                "⚠ 你已作答完毕，请提交之前导出的答题情况文件！⚠",
            )
            return

        selected = self.controller._pick_exam_questions(questions, distribution)
        self.controller.start_exam(selected, exam_uuid, duration * 60)

    def _play_game(self) -> None:
        import json
        import subprocess
        import tempfile
        from pathlib import Path
        from tkinter import filedialog, simpledialog

        path = filedialog.askopenfilename(
            parent=self, title="选择游戏文件（.sudasqs）",
            filetypes=[("加密题库文件", "*.sudasqs"), ("所有文件", "*.*")],
        )
        if not path:
            return
        password = simpledialog.askstring("输入密钥", "请输入该题库的密钥（密码）：", parent=self)
        if not password:
            return
        try:
            exam_uuid, duration, _, exam_type, questions = \
                self.controller.import_question_bank_for_exam(path, password.strip())
        except ValueError:
            messagebox.showerror("密钥错误", "密钥不正确或文件已损坏，请重试。")
            return
        if exam_type != "game":
            messagebox.showwarning("类型错误", "此题库类型为「试卷」，不是「游戏」，请使用「开始考试」按钮。")
            return

        mc_questions = [q for q in questions if q.qtype == "单选" and q.options]
        if not mc_questions:
            messagebox.showwarning("题目不足", "该题库中没有选择题，无法开始游戏。")
            return

        q_data = {
            "duration_minutes": duration,
            "questions": [
                {"text": q.text, "options": q.options, "answer": q.answer}
                for q in mc_questions
            ],
        }
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8")
        json.dump(q_data, tmp, ensure_ascii=False)
        tmp.close()

        game_dir = Path(__file__).resolve().parent / "Toho-mpsdream"
        main_py = game_dir / "main.py"
        if not main_py.exists():
            messagebox.showerror("游戏缺失", "未找到小游戏文件 Toho-mpsdream/main.py")
            return
        try:
            subprocess.Popen(
                ["python", str(main_py), "--quiz-file", tmp.name],
                cwd=str(game_dir),
            )
        except Exception as exc:
            messagebox.showerror("启动失败", f"无法启动游戏：{exc}")

    def _import_avatar(self) -> None:
        from tkinter import filedialog

        path = filedialog.askopenfilename(
            parent=self, title="选择头像图片",
            filetypes=[("图片文件", "*.jpg *.jpeg *.png"), ("所有文件", "*.*")],
        )
        if not path:
            return
        try:
            from data_manager import process_avatar_file

            b64 = process_avatar_file(path)
            sid = self.controller.current_user.get("student_id", "")
            self.controller.save_avatar(sid, b64)
            self.controller.current_user["avatar_base64"] = b64
            messagebox.showinfo("导入成功", "头像已设置。")
            self.controller.show_student_dashboard()
        except Exception as exc:
            messagebox.showerror("导入失败", f"无法处理图片：{exc}")

class QuizWindow(BaseFrame):
    def __init__(self, master, controller, duration_seconds: int = 600) -> None:
        super().__init__(master, controller)
        self.question_index = 0
        self.remaining_seconds = duration_seconds
        self.after_id = None
        self.answer_var = tk.StringVar()
        self.option_widgets: List[ttk.Radiobutton] = []

        header = ttk.Frame(self, style="App.TFrame")
        header.pack(fill="x")
        self.progress_var = tk.StringVar()
        self.timer_var = tk.StringVar()
        ttk.Label(header, textvariable=self.progress_var, style="Section.TLabel").pack(side="left")
        ttk.Label(header, textvariable=self.timer_var, style="Timer.TLabel").pack(side="right")

        self.progress = ttk.Progressbar(self, maximum=len(controller.quiz_engine.questions))
        self.progress.pack(fill="x", pady=(8, 18))

        self.body = ttk.Frame(self, style="Card.TFrame", padding=20)
        self.body.pack(fill="both", expand=True)
        self.question_label = ttk.Label(
            self.body,
            text="",
            style="Question.TLabel",
            wraplength=760,
            justify="left",
        )
        self.question_label.pack(anchor="w", fill="x")

        self.answer_area = ttk.Frame(self.body, style="Card.TFrame")
        self.answer_area.pack(fill="x", pady=24)

        footer = ttk.Frame(self, style="App.TFrame")
        footer.pack(fill="x", pady=(16, 0))
        ttk.Button(footer, text="上一题", command=self.previous_question).pack(side="left")
        self._next_btn = ttk.Button(footer, text="下一题", command=self.next_question)
        self._next_btn.pack(side="left", padx=10)
        RoundedButton(footer, text="交卷", command=self.confirm_submit,
                      width=90).pack(side="right")

        self.render_question()
        self.tick()

    def destroy(self) -> None:
        if self.after_id:
            self.after_cancel(self.after_id)
        super().destroy()

    def tick(self) -> None:
        minutes, seconds = divmod(self.remaining_seconds, 60)
        self.timer_var.set(f"倒计时 {minutes:02d}:{seconds:02d}")
        if self.remaining_seconds <= 0:
            messagebox.showinfo("时间到", "考试时间已结束，系统将自动交卷")
            self.submit(force=True)
            return
        self.remaining_seconds -= 1
        self.after_id = self.after(1000, self.tick)

    def current_question(self) -> Question:
        return self.controller.quiz_engine.questions[self.question_index]

    def render_question(self) -> None:
        question = self.current_question()
        total = len(self.controller.quiz_engine.questions)
        self.progress_var.set(f"第 {self.question_index + 1} / {total} 题　{question.qtype}")
        self.progress["value"] = self.question_index + 1
        self.question_label.config(text=f"{question.text}（{question.score} 分）")

        if self.question_index >= total - 1:
            self._next_btn.pack_forget()
        else:
            self._next_btn.pack(side="left", padx=10)

        for child in self.answer_area.winfo_children():
            child.destroy()

        saved = self.controller.quiz_engine.answers.get(question.id, "")
        self.answer_var.set(saved)

        if question.qtype in {"单选", "判断"}:
            options = question.options if question.options else ["正确", "错误"]
            for option in options:
                value = self._option_value(option, question.qtype)
                rb = ttk.Radiobutton(
                    self.answer_area,
                    text=option,
                    value=value,
                    variable=self.answer_var,
                    command=self.save_current_answer,
                    style="Exam.TRadiobutton",
                )
                rb.pack(anchor="w", pady=8)
        else:
            entry = ttk.Entry(self.answer_area, textvariable=self.answer_var, font=(FONT_FAMILY, 17))
            entry.pack(fill="x")
            entry.bind("<KeyRelease>", lambda _event: self.save_current_answer())
            entry.focus_set()

    def _option_value(self, option: str, qtype: str) -> str:
        if qtype == "判断":
            return option
        return option.split(".", 1)[0].strip().upper()

    def save_current_answer(self) -> None:
        question = self.current_question()
        self.controller.quiz_engine.record_answer(question.id, self.answer_var.get())

    def previous_question(self) -> None:
        self.save_current_answer()
        if self.question_index > 0:
            self.question_index -= 1
            self.render_question()

    def next_question(self) -> None:
        self.save_current_answer()
        if self.question_index < len(self.controller.quiz_engine.questions) - 1:
            self.question_index += 1
            self.render_question()

    def confirm_submit(self) -> None:
        self.save_current_answer()
        missing = self.controller.quiz_engine.unanswered_count()
        if missing:
            ok = messagebox.askyesno("确认交卷", f"您还有 {missing} 道题未作答，确认交卷吗？")
            if not ok:
                return
        self.submit()

    def submit(self, force: bool = False) -> None:
        self.save_current_answer()
        result = self.controller.submit_exam()
        self.controller.show_result(result)

class ResultWindow(BaseFrame):
    def __init__(self, master, controller, result: Optional[Dict[str, object]]) -> None:
        super().__init__(master, controller)
        self.result = result or {"score": 0, "total": 0, "details": []}
        self._score = self.result["score"]
        self._total = self.result["total"]
        self._revealed = False

        ttk.Label(self, text="考试结果", style="Title.TLabel").pack(anchor="w")
        self._subtitle_label = ttk.Label(
            self, text="本次得分：0 → ???",
            style="Muted.TLabel",
        )
        self._subtitle_label.pack(anchor="w", pady=(4, 16))

        self.actions = ttk.Frame(self, style="App.TFrame")
        self.actions.pack(fill="x")
        ttk.Button(self.actions, text="导出答题情况",
                   command=self._export_result).pack(side="left")

        self._hidden_area = ttk.Frame(self, style="App.TFrame")
        self._hidden_area.pack(fill="both", expand=True, pady=16)
        tease_card = ttk.Frame(self._hidden_area, style="Card.TFrame", padding=40)
        tease_card.pack(expand=True)
        ttk.Label(
            tease_card,
            text="我才不告诉你做得怎么样呢\n(〜￣▽￣)〜",
            font=("Microsoft YaHei", 26, "bold"),
            foreground=MUTED,
            background=PANEL,
        ).pack()
        ttk.Label(
            tease_card,
            text="导出答题情况后即可查看详细结果",
            style="Muted.TLabel",
        ).pack(pady=(16, 0))

        self._real_content = ttk.Frame(self, style="App.TFrame")

        left = ttk.Frame(self._real_content, style="Card.TFrame", padding=16)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        ttk.Label(left, text="题型正确率", style="Section.TLabel").pack(anchor="w")
        self._type_canvas = tk.Canvas(left, height=240, bg=PANEL, highlightthickness=0)
        self._type_canvas.pack(fill="both", expand=True, pady=(12, 0))

        right = ttk.Frame(self._real_content, style="Card.TFrame", padding=16)
        right.pack(side="left", fill="both", expand=True, padx=(10, 0))
        ttk.Label(right, text="答题明细", style="Section.TLabel").pack(anchor="w")
        self._detail_text = tk.Text(right, height=12, wrap="word", font=("Microsoft YaHei", 10), bd=0)
        self._detail_text.pack(fill="both", expand=True, pady=(12, 0))

    def _reveal(self) -> None:
        if self._revealed:
            return
        self._revealed = True

        self._subtitle_label.config(text=f"本次得分：{self._score} / {self._total}")

        self._hidden_area.destroy()

        self._real_content.pack(fill="both", expand=True, pady=16)

        self.draw_type_bars(self._type_canvas, self.result.get("type_stats", {}))

        for item in self.result.get("details", []):
            question = item["question"]
            status = "正确" if item["correct"] else "错误"
            self._detail_text.insert("end", f"[{status}] {question.text}\n")
            self._detail_text.insert("end", f"你的答案：{item['user_answer']}　正确答案：{question.answer}\n")
            self._detail_text.insert("end", f"解析：{question.analysis}\n\n")
        self._detail_text.config(state="disabled")

        ttk.Button(self.actions, text="查看错题本",
                   command=self.controller.show_wrong_book).pack(side="left", padx=(10, 0))
        ttk.Button(self.actions, text="返回主页",
                   command=self.controller.show_student_dashboard).pack(side="left", padx=(10, 0))

    def draw_type_bars(self, canvas: tk.Canvas, stats: Dict[str, Dict[str, int]]) -> None:
        canvas.update_idletasks()
        width = max(360, canvas.winfo_width())
        height = 220
        canvas.delete("all")
        if not stats:
            canvas.create_text(width / 2, height / 2, text="暂无统计", fill=MUTED)
            return
        names = list(stats.keys())
        bar_width = 52
        gap = (width - 80) / max(1, len(names))
        for index, name in enumerate(names):
            item = stats[name]
            rate = item["right"] / max(1, item["total"])
            x = 55 + index * gap
            bar_height = rate * 150
            canvas.create_rectangle(
                x,
                height - 40 - bar_height,
                x + bar_width,
                height - 40,
                fill=SUCCESS if rate >= 0.6 else DANGER,
                outline="",
            )
            canvas.create_text(x + bar_width / 2, height - 18, text=name, fill=TEXT)
            canvas.create_text(x + bar_width / 2, height - 50 - bar_height, text=f"{rate:.0%}", fill=TEXT)

    def _export_result(self) -> None:
        from datetime import datetime
        from tkinter import filedialog

        default_name = f"答题情况_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ilovesuda"
        path = filedialog.asksaveasfilename(
            parent=self,
            title="导出答题情况（加密 .ilovesuda）",
            defaultextension=".ilovesuda",
            filetypes=[("加密答题文件", "*.ilovesuda"), ("所有文件", "*.*")],
            initialfile=default_name,
        )
        if not path:
            return
        try:
            self.controller.export_current_result(path)
            messagebox.showinfo("导出成功", f"答题情况已加密导出到：\n{path}\n\n该文件无法用普通软件打开，需教师端导入。")
            self._reveal()
        except Exception as exc:
            messagebox.showerror("导出失败", str(exc))

class WrongBookWindow(BaseFrame):
    def __init__(self, master, controller) -> None:
        super().__init__(master, controller)
        _set_bg_image(self, 0.60)
        self.title("智能错题本", "自动汇总历史考试中答错的题目，并展示答案与解析")

        top_row = ttk.Frame(self, style="App.TFrame")
        top_row.pack(fill="x")
        RoundedButton(top_row, text="返回主页", command=controller.show_student_dashboard, width=90).pack(side="left")
        user = controller.current_user or {}
        self._questions = controller.get_wrong_questions_for_current_user()
        if user.get("role") == "student" and self._questions:
            RoundedButton(top_row, text="下载错题本 (.md)",
                          command=self._export_markdown, width=140).pack(side="left", padx=(10, 0))

        if not self._questions:
            ttk.Label(self, text="暂无错题，完成考试后会自动生成错题本。", style="Muted.TLabel").pack(
                anchor="w", pady=28
            )
            return

        canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        list_frame = ttk.Frame(canvas, style="App.TFrame")
        list_frame.bind(
            "<Configure>", lambda _event: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=list_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True, pady=16)
        scrollbar.pack(side="right", fill="y")

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _bind_wheel_recursive(widget):
            widget.bind("<MouseWheel>", _on_mousewheel)
            for child in widget.winfo_children():
                _bind_wheel_recursive(child)

        canvas.bind("<MouseWheel>", _on_mousewheel)
        scrollbar.bind("<MouseWheel>", _on_mousewheel)

        for question in self._questions:
            card = ttk.Frame(list_frame, style="Card.TFrame", padding=14)
            card.pack(fill="x", padx=4, pady=8)
            ttk.Label(
                card,
                text=f"#{question.id} [{question.qtype}] {question.text}",
                style="QuestionSmall.TLabel",
                wraplength=780,
            ).pack(anchor="w")
            if question.options:
                ttk.Label(card, text="　".join(question.options), style="Muted.TLabel", wraplength=780).pack(
                    anchor="w", pady=(8, 0)
                )
            ttk.Label(card, text=f"正确答案：{question.answer}", foreground=SUCCESS).pack(anchor="w", pady=(8, 0))
            ttk.Label(card, text=f"解析：{question.analysis}", style="Muted.TLabel", wraplength=780).pack(
                anchor="w", pady=(4, 0)
            )

            def _bind_right_click(widget, qid=question.id):
                widget.bind("<Button-3>",
                            lambda e, q=qid: self._on_wrong_card_right_click(e, q))
                for child in widget.winfo_children():
                    _bind_right_click(child, qid)
            _bind_right_click(card)

        _bind_wheel_recursive(list_frame)

    def _on_wrong_card_right_click(self, event, question_id: int) -> None:
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(
            label="删除此错题",
            command=lambda qid=question_id: self._delete_wrong_question(qid),
        )
        menu.post(event.x_root, event.y_root)

    def _delete_wrong_question(self, question_id: int) -> None:
        if not messagebox.askyesno("确认删除", f"确认从错题本中移除 #{question_id} 吗？\n将从你的所有历史成绩记录中清除此题。"):
            return
        user = self.controller.current_user or {}
        self.controller.score_manager.remove_wrong_id(user.get("username", ""), question_id)
        self.controller.show_wrong_book()

    def _export_markdown(self) -> None:
        from datetime import datetime
        from tkinter import filedialog

        default_name = f"错题本_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        path = filedialog.asksaveasfilename(
            parent=self,
            title="保存错题本",
            defaultextension=".md",
            filetypes=[("Markdown 文件", "*.md"), ("所有文件", "*.*")],
            initialfile=default_name,
        )
        if not path:
            return

        user = self.controller.current_user or {}
        lines = [
            f"# {user.get('name', '学生')}的错题本",
            "",
            f"> 学生：{user.get('name', '')}　学号：{user.get('student_id', '')}",
            f"> 错题数量：{len(self._questions)} 道",
            "",
            "---",
            "",
        ]

        for q in self._questions:
            lines.append(f"## {q.id} [{q.qtype}] {q.text}")
            lines.append("")
            if q.options:
                lines.append(f"- **选项**：{'　'.join(q.options)}")
            lines.append(f"- **正确答案**：{q.answer}")
            if q.analysis:
                lines.append(f"- **解析**：{q.analysis}")
            lines.append("")
            lines.append("---")
            lines.append("")

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            messagebox.showinfo("导出成功", f"错题本已保存到：\n{path}")
        except OSError as exc:
            messagebox.showerror("导出失败", f"无法写入文件：{exc}")

class ExamDetailDialog(tk.Toplevel):

    def __init__(self, parent, controller, record: Dict[str, object]) -> None:
        super().__init__(parent)
        self.controller = controller
        self.record = record
        self.title(f"答题详情 — {record.get('student_name', '')}")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.transient(parent)
        self.grab_set()

        body = ttk.Frame(self, padding=20, style="App.TFrame")
        body.pack(fill="both", expand=True)

        header = ttk.Frame(body, style="Card.TFrame", padding=16)
        header.pack(fill="x", pady=(0, 14))

        name = record.get("student_name", "")
        sid = record.get("student_id", "")
        exam_time = record.get("exam_time", "")
        score = record.get("score", 0)
        total = record.get("total", 0)
        rate = f"{score}/{total}（{score / max(1, int(total)):.0%}）"

        ttk.Label(header, text=f"学生：{name}　学号：{sid}", style="Section.TLabel").pack(anchor="w")
        ttk.Label(header, text=f"考试时间：{exam_time}", style="Muted.TLabel").pack(anchor="w", pady=(4, 0))
        ttk.Label(header, text=f"得分：{rate}", font=("Microsoft YaHei", 14, "bold"),
                  foreground=SUCCESS if int(score) / max(1, int(total)) >= 0.6 else DANGER).pack(
            anchor="w", pady=(6, 0))

        type_stats: Dict[str, Dict[str, int]] = record.get("type_stats", {})
        if type_stats:
            stats_frame = ttk.Frame(body, style="Card.TFrame", padding=14)
            stats_frame.pack(fill="x", pady=(0, 14))
            ttk.Label(stats_frame, text="各题型正确率", style="Section.TLabel").pack(anchor="w")
            for qtype, stats in type_stats.items():
                right = stats.get("right", 0)
                qtotal = stats.get("total", 0)
                pct = f"{right}/{qtotal}（{right / max(1, qtotal):.0%}）"
                color = SUCCESS if right / max(1, qtotal) >= 0.6 else DANGER
                row_frame = ttk.Frame(stats_frame, style="Card.TFrame")
                row_frame.pack(fill="x", pady=(4, 0))
                ttk.Label(row_frame, text=f"• {qtype}：{pct}", foreground=color).pack(side="left")

        wrong_ids: List[int] = record.get("wrong_ids", [])
        wrong_answers: Dict[str, str] = record.get("wrong_answers", {})
        all_questions = {q.id: q for q in self.controller.question_bank.load_questions()}
        wrong_questions = [all_questions[qid] for qid in wrong_ids if qid in all_questions]

        ttk.Label(body, text=f"错题详情（共 {len(wrong_questions)} 道）", style="Section.TLabel").pack(anchor="w", pady=(0, 8))

        if not wrong_questions:
            ttk.Label(body, text="该次考试全部正确，无错题记录。", style="Muted.TLabel").pack(anchor="w", pady=12)
        else:

            canvas = tk.Canvas(body, bg=BG, highlightthickness=0, height=min(380, 120 * len(wrong_questions)))
            scrollbar = ttk.Scrollbar(body, orient="vertical", command=canvas.yview)
            inner = ttk.Frame(canvas, style="App.TFrame")
            inner.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
            canvas.create_window((0, 0), window=inner, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")

            def _wheel(event):
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

            def _bind_wheel(widget):
                widget.bind("<MouseWheel>", _wheel)
                for child in widget.winfo_children():
                    _bind_wheel(child)

            for q in wrong_questions:
                card = ttk.Frame(inner, style="Card.TFrame", padding=12)
                card.pack(fill="x", padx=2, pady=6)
                ttk.Label(card, text=f"#{q.id} [{q.qtype}] {q.text}（{q.score} 分）",
                          style="QuestionSmall.TLabel", wraplength=680).pack(anchor="w")
                if q.options:
                    ttk.Label(card, text="　".join(q.options), style="Muted.TLabel", wraplength=680).pack(
                        anchor="w", pady=(4, 0))

                user_ans = wrong_answers.get(str(q.id), "")
                if user_ans:
                    ttk.Label(card, text=f"学生作答：{user_ans}", foreground=DANGER).pack(anchor="w", pady=(4, 0))
                else:
                    ttk.Label(card, text="学生作答：未作答", foreground=DANGER).pack(anchor="w", pady=(4, 0))
                ttk.Label(card, text=f"正确答案：{q.answer}", foreground=SUCCESS).pack(anchor="w", pady=(2, 0))
                if q.analysis:
                    ttk.Label(card, text=f"解析：{q.analysis}", style="Muted.TLabel", wraplength=680).pack(
                        anchor="w", pady=(2, 0))

            _bind_wheel(inner)
            canvas.bind("<MouseWheel>", _wheel)
            scrollbar.bind("<MouseWheel>", _wheel)

class EditQuestionDialog(tk.Toplevel):

    def __init__(self, parent, controller, question: Question) -> None:
        super().__init__(parent)
        self.controller = controller
        self.question = question
        self.title(f"编辑题目 #{question.id}")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.transient(parent)
        self.grab_set()

        body = ttk.Frame(self, padding=20, style="App.TFrame")
        body.pack(fill="both", expand=True)

        ttk.Label(body, text="题型").grid(row=0, column=0, sticky="w", padx=(0, 10), pady=6)
        self.qtype_var = tk.StringVar(value=question.qtype)
        ttk.Combobox(body, textvariable=self.qtype_var, values=["单选", "填空", "判断"],
                     width=8, state="readonly").grid(row=0, column=1, sticky="ew", pady=6)

        ttk.Label(body, text="题目").grid(row=1, column=0, sticky="w", padx=(0, 10), pady=6)
        self.text_var = tk.StringVar(value=question.text)
        ttk.Entry(body, textvariable=self.text_var, width=55).grid(row=1, column=1, sticky="ew", pady=6)

        ttk.Label(body, text="选项（;分隔）").grid(row=2, column=0, sticky="w", padx=(0, 10), pady=6)
        self.options_var = tk.StringVar(value=";".join(question.options) if question.options else "")
        ttk.Entry(body, textvariable=self.options_var, width=55).grid(row=2, column=1, sticky="ew", pady=6)

        ttk.Label(body, text="答案").grid(row=3, column=0, sticky="w", padx=(0, 10), pady=6)
        self.answer_var = tk.StringVar(value=question.answer)
        ttk.Entry(body, textvariable=self.answer_var, width=55).grid(row=3, column=1, sticky="ew", pady=6)

        ttk.Label(body, text="解析").grid(row=4, column=0, sticky="w", padx=(0, 10), pady=6)
        self.analysis_var = tk.StringVar(value=question.analysis)
        ttk.Entry(body, textvariable=self.analysis_var, width=55).grid(row=4, column=1, sticky="ew", pady=6)

        ttk.Label(body, text="分值").grid(row=5, column=0, sticky="w", padx=(0, 10), pady=6)
        self.score_var = tk.StringVar(value=str(question.score))
        ttk.Entry(body, textvariable=self.score_var, width=8).grid(row=5, column=1, sticky="w", pady=6)

        body.columnconfigure(1, weight=1)

        ttk.Label(body, text="选项用英文分号 ; 分隔。单选答案填 A/B/C/D，判断填 正确/错误。",
                  style="Muted.TLabel").grid(row=6, column=0, columnspan=2, sticky="w", pady=(8, 0))

        btn_row = ttk.Frame(body, style="App.TFrame")
        btn_row.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(14, 0))
        RoundedButton(btn_row, text="取消", command=self.destroy, width=80).pack(side="right", padx=(10, 0))
        RoundedButton(btn_row, text="保存修改", command=self._save, width=100).pack(side="right")

    def _save(self) -> None:
        try:
            score = int(self.score_var.get())
            options = [item.strip() for item in self.options_var.get().split(";") if item.strip()]
            updated = Question(
                id=self.question.id,
                qtype=self.qtype_var.get(),
                text=self.text_var.get(),
                options=options,
                answer=self.answer_var.get(),
                analysis=self.analysis_var.get(),
                score=score,
            )
            self.controller.question_bank.update_question(updated)
        except ValueError as exc:
            messagebox.showwarning("无人在意", str(exc) or "分值必须为整数")
            return
        except RuntimeError as exc:
            messagebox.showerror("保存失败", str(exc))
            return
        messagebox.showinfo("保存成功", f"题目 #{self.question.id} 已更新")

        parent = self.master
        while parent and not isinstance(parent, TeacherDashboard):
            parent = parent.master
        if isinstance(parent, TeacherDashboard):
            parent.refresh_questions()
        self.destroy()

class ExportExamDialog(tk.Toplevel):

    def __init__(self, parent, controller) -> None:
        super().__init__(parent)
        self.controller = controller
        self.result: Optional[Dict] = None
        self.title("导出试卷设置")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.transient(parent)
        self.grab_set()

        body = ttk.Frame(self, padding=20, style="App.TFrame")
        body.pack(fill="both", expand=True)

        ttk.Label(body, text="试卷密钥（密码）", style="Section.TLabel").grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 4))
        self.pwd_var = tk.StringVar()
        ttk.Entry(body, textvariable=self.pwd_var, width=30).grid(
            row=1, column=0, columnspan=3, sticky="ew", pady=(0, 12))
        ttk.Label(body, text="学生凭此密码参加考试，至少 3 位。",
                  style="Muted.TLabel").grid(row=2, column=0, columnspan=3, sticky="w", pady=(0, 14))

        ttk.Label(body, text="答题时长（分钟）", style="Section.TLabel").grid(
            row=3, column=0, columnspan=2, sticky="w", pady=(0, 4))
        self.duration_var = tk.StringVar(value="30")
        ttk.Spinbox(body, textvariable=self.duration_var, from_=1, to=300, width=6).grid(
            row=4, column=0, sticky="w", pady=(0, 14))
        ttk.Label(body, text="学生考试倒计时，必须设置。",
                  style="Muted.TLabel").grid(row=5, column=0, columnspan=3, sticky="w", pady=(0, 14))

        ttk.Label(body, text="题库类型", style="Section.TLabel").grid(
            row=6, column=0, columnspan=2, sticky="w", pady=(0, 4))
        self.type_var = tk.StringVar(value="exam")
        type_frame = ttk.Frame(body, style="App.TFrame")
        type_frame.grid(row=7, column=0, columnspan=2, sticky="w", pady=(0, 14))
        ttk.Radiobutton(type_frame, text="试卷（学生考试用）", value="exam",
                        variable=self.type_var).pack(side="left", padx=(0, 20))
        ttk.Radiobutton(type_frame, text="游戏（学生娱乐用）", value="game",
                        variable=self.type_var).pack(side="left")

        self.dist_enabled = tk.BooleanVar(value=False)
        ttk.Checkbutton(body, text="自定义题型分布（不启用则随机抽 10 题）",
                        variable=self.dist_enabled,
                        command=self._toggle_dist).grid(
            row=8, column=0, columnspan=3, sticky="w", pady=(0, 8))

        dist_frame = ttk.Frame(body, style="App.TFrame")
        dist_frame.grid(row=9, column=0, columnspan=3, sticky="w", pady=(0, 4))
        ttk.Label(dist_frame, text="单选题数量：").pack(side="left")
        self.choice_count_var = tk.StringVar(value="5")
        self._choice_spin = ttk.Spinbox(dist_frame, textvariable=self.choice_count_var,
                                        from_=0, to=50, width=5)
        self._choice_spin.pack(side="left", padx=(4, 20))
        ttk.Label(dist_frame, text="填空题数量：").pack(side="left")
        self.fill_count_var = tk.StringVar(value="5")
        self._fill_spin = ttk.Spinbox(dist_frame, textvariable=self.fill_count_var,
                                      from_=0, to=50, width=5)
        self._fill_spin.pack(side="left", padx=(4, 0))
        self._toggle_dist()

        btn_row = ttk.Frame(body, style="App.TFrame")
        btn_row.grid(row=10, column=0, columnspan=3, sticky="ew", pady=(20, 0))
        RoundedButton(btn_row, text="取消", command=self.destroy, width=80).pack(side="right", padx=(10, 0))
        RoundedButton(btn_row, text="导出", command=self._confirm, width=80).pack(side="right")

    def _toggle_dist(self) -> None:
        state = "normal" if self.dist_enabled.get() else "disabled"
        self._choice_spin.configure(state=state)
        self._fill_spin.configure(state=state)

    def _confirm(self) -> None:
        pwd = self.pwd_var.get().strip()
        if len(pwd) < 3:
            messagebox.showwarning("密钥太短", "密钥至少需要 3 位。")
            return
        try:
            duration = int(self.duration_var.get())
            if duration < 1:
                raise ValueError
        except ValueError:
            messagebox.showwarning("时长错误", "答题时长必须是一个正整数（分钟）。")
            return

        distribution = None
        if self.dist_enabled.get():
            try:
                cc = int(self.choice_count_var.get())
                fc = int(self.fill_count_var.get())
                if cc < 0 or fc < 0 or cc + fc == 0:
                    raise ValueError
                distribution = {"单选": cc, "填空": fc}
            except ValueError:
                messagebox.showwarning("分布错误", "题型数量必须为非负整数，且至少一题。")
                return

        self.result = {
            "password": pwd,
            "duration_minutes": duration,
            "distribution": distribution,
            "exam_type": self.type_var.get(),
        }
        self.destroy()

class TeacherDashboard(BaseFrame):
    def __init__(self, master, controller) -> None:
        super().__init__(master, controller)
        self.title("教师端管理", "题库增删查、班级成绩报表与题型正确率分析")

        actions = ttk.Frame(self, style="App.TFrame")
        actions.pack(fill="x")
        self._import_btn = ttk.Button(actions, text="导入答题情况", command=self._import_result)
        self._import_btn.pack(side="left", padx=(0, 10))
        self._import_btn.pack_forget()
        self._import_q_btn = ttk.Button(actions, text="导入题库", command=self._import_question_bank)
        self._import_q_btn.pack(side="left", padx=(0, 8))
        self._import_q_btn.pack_forget()
        self._export_q_btn = ttk.Button(actions, text="导出题库", command=self._export_question_bank)
        self._export_q_btn.pack(side="left", padx=(0, 8))
        self._export_q_btn.pack_forget()
        self._import_pdf_btn = ttk.Button(actions, text="导入PDF", command=self._import_pdf)
        self._import_pdf_btn.pack(side="left", padx=(0, 8))
        self._import_pdf_btn.pack_forget()
        self._refresh_btn = ttk.Button(actions, text="刷新", command=self.refresh_all)
        self._refresh_btn.pack(side="left", padx=(0, 10))
        ttk.Button(actions, text="退出登录", command=controller.show_login).pack(side="right", padx=(4, 0))
        self._batch_btn = ttk.Button(actions, text="批量管理", command=self._toggle_batch_mode)
        self._batch_btn.pack(side="right")
        self._batch_btn.pack_forget()

        ttk.Button(self, text="⚙ 设置", command=controller.show_settings).place(relx=1.0, y=0, anchor="ne")

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, pady=16)
        self.question_tab = ttk.Frame(notebook, style="App.TFrame", padding=10)
        self.score_tab = ttk.Frame(notebook, style="App.TFrame", padding=10)
        self.stats_tab = ttk.Frame(notebook, style="App.TFrame", padding=10)
        notebook.add(self.question_tab, text="题库管理")
        notebook.add(self.score_tab, text="答题情况汇总")
        notebook.add(self.stats_tab, text="题目情况汇总")
        self.leaderboard_tab = ttk.Frame(notebook, style="App.TFrame", padding=10)
        notebook.add(self.leaderboard_tab, text="排行榜")
        notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        self._import_q_btn.pack(side="left", padx=(0, 8), before=self._refresh_btn)
        self._export_q_btn.pack(side="left", padx=(0, 8), before=self._refresh_btn)
        self._import_pdf_btn.pack(side="left", padx=(0, 8), before=self._refresh_btn)

        self.build_question_tab()
        self.build_score_tab()
        self.build_stats_tab()
        self.build_leaderboard_tab()
        self.refresh_all()

    def build_question_tab(self) -> None:
        columns = ("id", "type", "question", "answer", "score")
        self.question_table = ttk.Treeview(self.question_tab, columns=columns, show="headings", height=10)
        for col, text, width in [
            ("id", "ID", 50),
            ("type", "题型", 70),
            ("question", "题目", 430),
            ("answer", "答案", 90),
            ("score", "分值", 60),
        ]:
            self.question_table.heading(col, text=text)
            self.question_table.column(col, width=width, anchor="center" if col != "question" else "w")
        self.question_table.pack(fill="both", expand=True)

        self.question_table.bind("<Double-1>", self._on_question_double_click)
        self.question_table.bind("<ButtonPress-1>", self._on_question_press)
        self.question_table.bind("<B1-Motion>", self._on_question_motion)
        self.question_table.bind("<ButtonRelease-1>", self._on_question_release)

        self.question_table.tag_configure("drag_ghost", background="#dbeafe")
        self.question_table.tag_configure("drop_target", background="#fef3c7")
        self._drag_item: Optional[str] = None
        self._drag_active: bool = False
        self._drag_start_y: int = 0
        self._drag_threshold: int = 8
        self._prev_target: Optional[str] = None

        q_actions = ttk.Frame(self.question_tab, style="App.TFrame")
        q_actions.pack(fill="x", pady=(8, 0))
        ttk.Button(q_actions, text="删除选中题", style="Danger.TButton",
                   command=self.delete_selected).pack(side="left")
        ttk.Button(q_actions, text="批量管理", command=self._toggle_q_batch_mode).pack(side="left", padx=(10, 0))

        self._q_batch_bar = ttk.Frame(self.question_tab, style="Card.TFrame", padding=8)
        ttk.Label(self._q_batch_bar, text="批量模式 — 按住 Ctrl 或 Shift 多选",
                  style="Section.TLabel").pack(side="left", padx=(4, 12))
        ttk.Button(self._q_batch_bar, text="全选", command=self._q_batch_select_all).pack(side="left", padx=(0, 6))
        ttk.Button(self._q_batch_bar, text="反选", command=self._q_batch_invert).pack(side="left", padx=(0, 6))
        self._q_batch_del_btn = ttk.Button(
            self._q_batch_bar, text="删除选中 (0)", style="Danger.TButton",
            command=self._q_batch_delete,
        )
        self._q_batch_del_btn.pack(side="left", padx=(0, 6))
        ttk.Button(self._q_batch_bar, text="退出批量管理", command=self._toggle_q_batch_mode).pack(side="right")
        self._q_batch_mode = False
        self.question_table.bind("<<TreeviewSelect>>", self._on_q_batch_selection_change, add="+")

        form = ttk.Frame(self.question_tab, style="Card.TFrame", padding=14)
        form.pack(fill="x", pady=(14, 0))
        self.qtype_var = tk.StringVar(value="单选")
        self.text_var = tk.StringVar()
        self.options_var = tk.StringVar()
        self.answer_var = tk.StringVar()
        self.analysis_var = tk.StringVar()
        self.score_var = tk.StringVar(value="10")

        labels = ["题型", "题目", "选项", "答案", "解析", "分值"]
        widgets = [
            ttk.Combobox(form, textvariable=self.qtype_var, values=["单选", "填空", "判断"], width=8, state="readonly"),
            ttk.Entry(form, textvariable=self.text_var),
            ttk.Entry(form, textvariable=self.options_var),
            ttk.Entry(form, textvariable=self.answer_var),
            ttk.Entry(form, textvariable=self.analysis_var),
            ttk.Entry(form, textvariable=self.score_var, width=8),
        ]
        for index, label in enumerate(labels):
            ttk.Label(form, text=label).grid(row=0, column=index, sticky="w", padx=4)
            widgets[index].grid(row=1, column=index, sticky="ew", padx=4, pady=(4, 0))
            form.columnconfigure(index, weight=2 if label in {"题目", "解析"} else 1)
        ttk.Button(form, text="新增题目", style="Primary.TButton", command=self.add_question).grid(
            row=1, column=6, padx=(10, 0)
        )
        ttk.Label(
            form,
            text="选项用英文分号 ; 分隔。单选答案填 A/B/C/D，判断答案填 正确/错误。",
            style="Muted.TLabel",
        ).grid(row=2, column=0, columnspan=7, sticky="w", pady=(8, 0))

    def build_score_tab(self) -> None:
        columns = ("name", "student_id", "score", "total", "time")
        self.score_table = ttk.Treeview(self.score_tab, columns=columns, show="headings", height=10)
        for col, text, width in [
            ("name", "姓名", 100),
            ("student_id", "学号", 120),
            ("score", "得分", 80),
            ("total", "总分", 80),
            ("time", "考试时间", 170),
        ]:
            self.score_table.heading(col, text=text)
            self.score_table.column(col, width=width, anchor="center")
        self.score_table.pack(fill="both", expand=True)
        self.score_table.bind("<Double-1>", self._on_score_double_click)
        self.score_table.bind("<Button-3>", self._on_score_right_click)
        self._score_records: Dict[str, Dict[str, object]] = {}

        self.report_canvas = tk.Canvas(self.score_tab, height=210, bg=PANEL, highlightthickness=0)
        self.report_canvas.pack(fill="x", pady=(14, 0))

        self._batch_bar = ttk.Frame(self.score_tab, style="Card.TFrame", padding=8)
        ttk.Label(self._batch_bar, text="批量模式 — 按住 Ctrl 或 Shift 多选",
                  style="Section.TLabel").pack(side="left", padx=(4, 12))
        ttk.Button(self._batch_bar, text="全选", command=self._batch_select_all).pack(side="left", padx=(0, 6))
        ttk.Button(self._batch_bar, text="反选", command=self._batch_invert).pack(side="left", padx=(0, 6))
        self._batch_del_btn = ttk.Button(
            self._batch_bar, text="删除选中 (0)", style="Danger.TButton",
            command=self._batch_delete,
        )
        self._batch_del_btn.pack(side="left", padx=(0, 6))
        ttk.Button(self._batch_bar, text="退出批量管理", command=self._toggle_batch_mode).pack(side="right")

        self._batch_mode = False

        self.score_table.bind("<<TreeviewSelect>>", self._on_batch_selection_change, add="+")

    def refresh_all(self) -> None:
        self.refresh_questions()
        self.refresh_scores()
        self.refresh_stats()
        self.refresh_leaderboard()

    def _on_tab_changed(self, event) -> None:
        notebook = event.widget
        current_tab = notebook.index(notebook.select())

        if current_tab == 0:
            self._import_q_btn.pack(side="left", padx=(0, 8), before=self._refresh_btn)
            self._export_q_btn.pack(side="left", padx=(0, 8), before=self._refresh_btn)
            self._import_pdf_btn.pack(side="left", padx=(0, 8), before=self._refresh_btn)
        else:
            self._import_q_btn.pack_forget()
            self._export_q_btn.pack_forget()
            self._import_pdf_btn.pack_forget()

        if current_tab == 1:
            self._batch_btn.pack(side="right")
            self._import_btn.pack(side="left", padx=(0, 10), before=self._refresh_btn)
        else:
            if self._batch_mode:
                self._toggle_batch_mode()
            self._batch_btn.pack_forget()
            self._import_btn.pack_forget()

        if current_tab == 3:
            self._start_leaderboard_music()
        else:
            self._stop_leaderboard_music()

    def _start_leaderboard_music(self) -> None:
        from pathlib import Path

        assets = Path(__file__).resolve().parent / "assets"
        dj = assets / "dj.mp3"
        if not dj.exists():
            return
        try:
            import pygame
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            if not pygame.mixer.music.get_busy():
                pygame.mixer.music.load(str(dj))
                pygame.mixer.music.play(-1)

            if not hasattr(self, "_lb_sfx_files"):
                self._lb_sfx_files = []
                self._lb_sfx_idx = 0
                for i in range(1, 4):
                    p = assets / f"correct_0{i}.mp3"
                    if p.exists():
                        self._lb_sfx_files.append(pygame.mixer.Sound(str(p)))
            if self._lb_sfx_files:
                self._lb_sfx_files[self._lb_sfx_idx % len(self._lb_sfx_files)].play()
                self._lb_sfx_idx += 1
        except Exception:
            pass

    def _stop_leaderboard_music(self) -> None:
        try:
            import pygame
            if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
        except Exception:
            pass

    def _import_result(self) -> None:
        from tkinter import filedialog

        paths = filedialog.askopenfilenames(
            parent=self,
            title="导入学生答题情况（可多选 .ilovesuda 文件）",
            filetypes=[("加密答题文件", "*.ilovesuda"), ("所有文件", "*.*")],
        )
        if not paths:
            return
        success = 0
        errors: list[str] = []
        for path in paths:
            try:
                self.controller.import_result_file(path)
                success += 1
            except Exception as exc:
                errors.append(f"{path}\n  → {exc}")
        self.refresh_scores()
        self.refresh_stats()
        msg = f"成功导入 {success} 份答题情况。"
        if errors:
            msg += f"\n\n{len(errors)} 份导入失败：\n" + "\n".join(errors[:5])
            if len(errors) > 5:
                msg += f"\n  …等 {len(errors) - 5} 项"
        messagebox.showinfo("导入完成", msg)

    def refresh_questions(self) -> None:
        self.question_table.delete(*self.question_table.get_children())
        try:
            questions = self.controller.question_bank.load_questions()
        except RuntimeError as exc:
            messagebox.showerror("题库错误", str(exc))
            return
        for question in questions:
            text_preview = question.text.split("\n")[0]
            self.question_table.insert(
                "",
                "end",
                iid=str(question.id),
                values=(question.id, question.qtype, text_preview, question.answer, question.score),
            )

    def refresh_scores(self) -> None:
        self.score_table.delete(*self.score_table.get_children())
        self._score_records.clear()
        records = self.controller.score_manager.list_scores()
        for idx, record in enumerate(reversed(records)):
            iid = self.score_table.insert(
                "",
                "end",
                values=(
                    record["student_name"],
                    record["student_id"],
                    record["score"],
                    record["total"],
                    record["exam_time"],
                ),
            )
            self._score_records[iid] = record
        self.draw_teacher_report(records)

    def _on_score_double_click(self, _event) -> None:
        selection = self.score_table.selection()
        if not selection:
            return
        record = self._score_records.get(selection[0])
        if record is None:
            return
        ExamDetailDialog(self, self.controller, record)

    def _on_score_right_click(self, event) -> None:
        row = self.score_table.identify_row(event.y)
        if not row:
            return
        self.score_table.selection_set(row)
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="删除此记录", command=lambda: self._delete_score_record(row))
        menu.post(event.x_root, event.y_root)

    def _delete_score_record(self, iid: str) -> None:
        record = self._score_records.get(iid)
        if record is None:
            return
        name = record.get("student_name", "")
        exam_time = str(record.get("exam_time", ""))
        if not messagebox.askyesno("确认删除", f"确认删除 {name} 在 {exam_time} 的考试记录吗？"):
            return
        username = str(record.get("username", ""))
        self.controller.score_manager.delete_record(username, exam_time)
        self.refresh_scores()
        self.refresh_stats()

    def _toggle_batch_mode(self) -> None:
        self._batch_mode = not self._batch_mode
        if self._batch_mode:
            self._batch_btn.config(text="退出批量管理")
            self.score_table.configure(selectmode="extended")
            self._batch_bar.pack(fill="x", pady=(0, 12), before=self.report_canvas)
            self._update_batch_count()
        else:
            self._batch_btn.config(text="批量管理")
            self.score_table.configure(selectmode="browse")
            self._batch_bar.pack_forget()
            self.score_table.selection_remove(*self.score_table.selection())

    def _on_batch_selection_change(self, _event) -> None:
        if self._batch_mode:
            self._update_batch_count()

    def _update_batch_count(self) -> None:
        count = len(self.score_table.selection())
        self._batch_del_btn.config(text=f"删除选中 ({count})")

    def _batch_select_all(self) -> None:
        for iid in self.score_table.get_children():
            self.score_table.selection_add(iid)
        self._update_batch_count()

    def _batch_invert(self) -> None:
        all_items = set(self.score_table.get_children())
        selected = set(self.score_table.selection())
        to_select = all_items - selected
        self.score_table.selection_remove(*selected)
        for iid in to_select:
            self.score_table.selection_add(iid)
        self._update_batch_count()

    def _batch_delete(self) -> None:
        selected = self.score_table.selection()
        if not selected:
            return
        count = len(selected)
        if not messagebox.askyesno("批量删除", f"确认删除选中的 {count} 条答题记录吗？\n此操作不可恢复。"):
            return
        deleted = 0
        for iid in selected:
            record = self._score_records.get(iid)
            if record:
                username = str(record.get("username", ""))
                exam_time = str(record.get("exam_time", ""))
                self.controller.score_manager.delete_record(username, exam_time)
                deleted += 1
        self._toggle_batch_mode()
        self.refresh_scores()
        self.refresh_stats()
        messagebox.showinfo("删除完成", f"已删除 {deleted} 条记录。")

    def draw_teacher_report(self, records: List[Dict[str, object]]) -> None:
        canvas = self.report_canvas
        canvas.update_idletasks()
        width = max(600, canvas.winfo_width())
        height = 190
        canvas.delete("all")
        if not records:
            canvas.create_text(width / 2, height / 2, text="暂无班级成绩数据", fill=MUTED)
            return
        latest = records[-10:]
        max_total = max(int(record["total"]) for record in latest) or 100
        gap = (width - 80) / max(1, len(latest))
        for index, record in enumerate(latest):
            score = int(record["score"])
            x = 45 + index * gap
            bar_height = (score / max_total) * 120
            canvas.create_rectangle(
                x,
                height - 36 - bar_height,
                x + 34,
                height - 36,
                fill=PRIMARY,
                outline="",
            )
            canvas.create_text(x + 17, height - 18, text=str(index + 1), fill=MUTED)
            canvas.create_text(x + 17, height - 46 - bar_height, text=str(score), fill=TEXT)
        canvas.create_text(12, 14, text="最近 10 次考试得分", anchor="w", fill=TEXT)

    def build_stats_tab(self) -> None:

        ctrl = ttk.Frame(self.stats_tab, style="App.TFrame")
        ctrl.pack(fill="x", pady=(0, 12))
        ttk.Label(ctrl, text="选择题目：").pack(side="left")
        self.stats_question_var = tk.StringVar(value="全部")
        self.stats_combo = ttk.Combobox(
            ctrl, textvariable=self.stats_question_var, width=22, state="readonly"
        )
        self.stats_combo.pack(side="left", padx=(6, 0))
        self.stats_combo.bind("<<ComboboxSelected>>", lambda _e: self.refresh_stats())

        content = ttk.Frame(self.stats_tab, style="App.TFrame")
        content.pack(fill="both", expand=True)
        content.columnconfigure(0, weight=1)
        content.columnconfigure(1, weight=1)
        content.rowconfigure(0, weight=1)

        left_card = ttk.Frame(content, style="Card.TFrame", padding=12)
        left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        ttk.Label(left_card, text="各题错误人数", style="Section.TLabel").pack(anchor="w")
        self.stats_bar_canvas = tk.Canvas(left_card, height=340, bg=PANEL, highlightthickness=0)
        self.stats_bar_canvas.pack(fill="both", expand=True, pady=(8, 0))

        right_card = ttk.Frame(content, style="Card.TFrame", padding=12)
        right_card.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        ttk.Label(right_card, text="错误答案分布", style="Section.TLabel").pack(anchor="w")
        self.stats_pie_canvas = tk.Canvas(right_card, height=340, bg=PANEL, highlightthickness=0)
        self.stats_pie_canvas.pack(fill="both", expand=True, pady=(8, 0))

        detail_card = ttk.Frame(self.stats_tab, style="Card.TFrame", padding=10)
        detail_card.pack(fill="x", pady=(12, 0))
        ttk.Label(detail_card, text="错误答案详情", style="Section.TLabel").pack(anchor="w")
        columns = ("question", "student", "answer")
        self.stats_detail_table = ttk.Treeview(
            detail_card, columns=columns, show="headings", height=5
        )
        self.stats_detail_table.heading("question", text="题目")
        self.stats_detail_table.heading("student", text="学生")
        self.stats_detail_table.heading("answer", text="学生作答")
        self.stats_detail_table.column("question", width=320)
        self.stats_detail_table.column("student", width=120)
        self.stats_detail_table.column("answer", width=120, anchor="center")
        self.stats_detail_table.pack(fill="x", pady=(6, 0))

    def refresh_stats(self) -> None:
        records = self.controller.score_manager.list_scores()
        questions = self.controller.question_bank.load_questions()

        combo_values = ["全部"] + [f"#{q.id} [{q.qtype}] {q.text[:18]}…" for q in questions]
        self.stats_combo["values"] = combo_values
        if self.stats_question_var.get() not in combo_values:
            self.stats_question_var.set("全部")

        stats: Dict[int, Dict] = {}
        for q in questions:
            stats[q.id] = {"question": q, "wrong_count": 0, "wrong_answers": {}}

        for record in records:
            wrong_ids = record.get("wrong_ids", [])
            wrong_answers = record.get("wrong_answers", {})
            student_name = str(record.get("student_name", ""))
            for qid in wrong_ids:
                qid_int = int(qid) if not isinstance(qid, int) else qid
                if qid_int in stats:
                    stats[qid_int]["wrong_count"] += 1
                    ans = str(wrong_answers.get(str(qid), wrong_answers.get(qid, "未作答")))
                    if ans not in stats[qid_int]["wrong_answers"]:
                        stats[qid_int]["wrong_answers"][ans] = {"count": 0, "students": []}
                    stats[qid_int]["wrong_answers"][ans]["count"] += 1
                    stats[qid_int]["wrong_answers"][ans]["students"].append(student_name)

        selected = self.stats_question_var.get()
        self._draw_wrong_count_bars(stats, selected)
        self._draw_wrong_answer_pie(stats, selected)
        self._fill_detail_table(stats, selected)

    def _draw_wrong_count_bars(self, stats, selected: str) -> None:
        canvas = self.stats_bar_canvas
        canvas.update_idletasks()
        w = max(300, canvas.winfo_width())
        h = 320
        canvas.delete("all")

        items = [(qid, s) for qid, s in stats.items()]
        if selected != "全部":
            sel_id = int(selected.split(" [")[0].lstrip("#"))
            items = [(qid, s) for qid, s in items if qid == sel_id]

        if not items or all(s["wrong_count"] == 0 for _, s in items):
            canvas.create_text(w / 2, h / 2, text="暂无数据", fill=MUTED, font=("Microsoft YaHei", 12))
            return

        max_count = max(s["wrong_count"] for _, s in items) or 1
        bar_area_w = w - 80
        bar_gap = min(28, bar_area_w / max(1, len(items)))
        bar_w = max(14, bar_gap - 8)
        baseline = h - 40

        canvas.create_line(50, baseline, w - 20, baseline, fill=BORDER)

        colors_palette = ["#2563eb", "#16a34a", "#dc2626", "#ea580c", "#8b5cf6",
                           "#0891b2", "#ca8a04", "#be185d", "#4f46e5", "#0d9488"]
        for idx, (qid, s) in enumerate(sorted(items, key=lambda x: -x[1]["wrong_count"])):
            x = 58 + idx * bar_gap
            bar_h = (s["wrong_count"] / max_count) * (baseline - 30)
            color = colors_palette[idx % len(colors_palette)]
            canvas.create_rectangle(x, baseline - bar_h, x + bar_w, baseline, fill=color, outline="")

            canvas.create_text(x + bar_w / 2, baseline - bar_h - 12,
                               text=str(s["wrong_count"]), fill=TEXT, font=("Microsoft YaHei", 9, "bold"))

            canvas.create_text(x + bar_w / 2, baseline + 14,
                               text=f"#{qid}", fill=MUTED, font=("Microsoft YaHei", 8))

    def _draw_wrong_answer_pie(self, stats, selected: str) -> None:
        canvas = self.stats_pie_canvas
        canvas.update_idletasks()
        w = max(300, canvas.winfo_width())
        h = 320
        canvas.delete("all")

        answers_agg: Dict[str, Dict] = {}
        if selected == "全部":

            for qid, s in stats.items():
                for ans, data in s["wrong_answers"].items():
                    if ans not in answers_agg:
                        answers_agg[ans] = {"count": 0, "students": []}
                    answers_agg[ans]["count"] += data["count"]
                    answers_agg[ans]["students"].extend(data["students"])
        else:
            sel_id = int(selected.split(" [")[0].lstrip("#"))
            if sel_id in stats:
                answers_agg = stats[sel_id]["wrong_answers"]

        if not answers_agg:
            canvas.create_text(w / 2, h / 2, text="该题无人答错", fill=MUTED, font=("Microsoft YaHei", 12))
            return

        total = sum(d["count"] for d in answers_agg.values())
        cx, cy = w // 2 - 30, h // 2
        radius = min(cx - 20, cy - 30, 100)
        start_angle = 0
        pie_colors = ["#2563eb", "#dc2626", "#16a34a", "#ea580c", "#8b5cf6",
                       "#0891b2", "#ca8a04", "#be185d", "#4f46e5", "#0d9488"]

        sorted_answers = sorted(answers_agg.items(), key=lambda x: -x[1]["count"])

        if len(sorted_answers) == 1:
            ans, data = sorted_answers[0]
            color = pie_colors[0]
            canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius,
                               fill=color, outline=PANEL, width=2)

            canvas.create_text(cx + radius + 44, cy, text=f"{ans} (100%)",
                               fill=TEXT, font=("Microsoft YaHei", 9, "bold"))
        else:
            import math
            for idx, (ans, data) in enumerate(sorted_answers):
                extent = (data["count"] / total) * 360
                color = pie_colors[idx % len(pie_colors)]
                canvas.create_arc(cx - radius, cy - radius, cx + radius, cy + radius,
                                  start=start_angle, extent=extent, fill=color, outline=PANEL, width=2)

                mid_angle = start_angle + extent / 2
                rad = math.radians(mid_angle)
                lx = cx + (radius + 44) * math.cos(rad)
                ly = cy - (radius + 44) * math.sin(rad)
                pct = data["count"] / total
                label_text = f"{ans} ({pct:.0%})" if len(ans) <= 6 else f"{ans[:5]}… ({pct:.0%})"
                canvas.create_text(lx, ly, text=label_text,
                                   fill=TEXT, font=("Microsoft YaHei", 9, "bold"))
                start_angle += extent

        canvas.create_text(cx, cy, text=f"共{total}次", fill=TEXT, font=("Microsoft YaHei", 10, "bold"))

    def _fill_detail_table(self, stats, selected: str) -> None:
        table = self.stats_detail_table
        table.delete(*table.get_children())
        items = [(qid, s) for qid, s in stats.items()]
        if selected != "全部":
            sel_id = int(selected.split(" [")[0].lstrip("#"))
            items = [(qid, s) for qid, s in items if qid == sel_id]

        for qid, s in sorted(items, key=lambda x: x[0]):
            q_text = f"#{qid} {s['question'].text[:30]}…" if len(s["question"].text) > 30 else f"#{qid} {s['question'].text}"
            for ans, data in sorted(s["wrong_answers"].items(), key=lambda x: -x[1]["count"]):
                for student in data["students"]:
                    table.insert("", "end", values=(q_text, student, ans))

    def build_leaderboard_tab(self) -> None:
        self._lb_avatars: list = []
        self.leaderboard_canvas = tk.Canvas(
            self.leaderboard_tab, bg=BG, highlightthickness=0,
        )
        self.leaderboard_canvas.pack(fill="both", expand=True)
        self._lb_redraw_after: Optional[str] = None
        self.leaderboard_canvas.bind("<Configure>", self._on_leaderboard_resize)

    def _on_leaderboard_resize(self, _event) -> None:
        if self._lb_redraw_after:
            self.after_cancel(self._lb_redraw_after)
        self._lb_redraw_after = self.after(80, self.refresh_leaderboard)

    def refresh_leaderboard(self) -> None:
        self._lb_redraw_after = None
        canvas = self.leaderboard_canvas
        canvas.update_idletasks()
        w = canvas.winfo_width()
        h = canvas.winfo_height()
        if w < 100 or h < 100:
            return
        canvas.delete("all")

        from data_manager import load_avatar, avatar_to_tk_image

        records = self.controller.score_manager.list_scores()
        student_totals: Dict[str, Dict] = {}
        for r in records:
            key = r.get("student_id", r.get("username", ""))
            if not key:
                continue
            if key not in student_totals:
                student_totals[key] = {"sid": key, "name": str(r.get("student_name", key)), "total": 0}
            student_totals[key]["total"] += int(r.get("score", 0))

        ranked = sorted(student_totals.values(), key=lambda x: -x["total"])[:3]

        if not ranked:
            canvas.create_text(w / 2, h / 2, text="暂无数据", fill=MUTED,
                               font=("Microsoft YaHei", 14))
            return

        cx_center = w / 2
        ground_y = h - 50
        gap = min(180, w / 5)

        slots = [
            (cx_center,          0, "🥇", 160, 100, "#FFD700"),
            (cx_center - gap,    1, "🥈", 130,  72, "#C0C0C0"),
            (cx_center + gap,    2, "🥉", 110,  48, "#CD7F32"),
        ]

        canvas.create_text(cx_center, 38, text="🏆 排行榜", fill=TEXT,
                           font=("Microsoft YaHei", 24, "bold"))

        self._lb_avatars: list = []

        for cx, ridx, medal, pw, ph, color in slots:
            if ridx >= len(ranked):
                continue
            student = ranked[ridx]
            px = cx - pw / 2
            py = ground_y - ph

            canvas.create_rectangle(px, py, px + pw, ground_y, fill=color, outline="")

            avatar_b64 = load_avatar(student["sid"])
            avatar_cy = py - 165
            if avatar_b64:
                try:
                    avatar_img = avatar_to_tk_image(avatar_b64, 72)
                    self._lb_avatars.append(avatar_img)
                    canvas.create_image(cx, avatar_cy, image=avatar_img)
                except Exception:
                    pass

            medal_y = py - 60
            canvas.create_text(cx, medal_y, text=medal, font=("Segoe UI Emoji", 32))

            name_y = medal_y + 30
            canvas.create_text(cx, name_y, text=student["name"],
                               fill=TEXT, font=("Microsoft YaHei", 12, "bold"))

            canvas.create_text(cx, py + ph / 2, text=f"{student['total']} 分",
                               fill="white", font=("Microsoft YaHei", 14, "bold"))

        margin = 40
        canvas.create_line(margin, ground_y, w - margin, ground_y, fill=BORDER, width=2)

    def add_question(self) -> None:
        try:
            score = int(self.score_var.get())
            options = [item.strip() for item in self.options_var.get().split(";") if item.strip()]
            self.controller.add_question(
                self.qtype_var.get(),
                self.text_var.get(),
                options,
                self.answer_var.get(),
                self.analysis_var.get(),
                score,
            )
        except ValueError as exc:
            messagebox.showwarning("无人在意", str(exc))
            return
        except RuntimeError as exc:
            messagebox.showerror("题库错误", str(exc))
            return
        self.text_var.set("")
        self.options_var.set("")
        self.answer_var.set("")
        self.analysis_var.set("")
        self.score_var.set("10")
        self.refresh_questions()
        messagebox.showinfo("新增成功", "题目已写入 questions.xlsx")

    def delete_selected(self) -> None:
        selected = self.question_table.selection()
        if not selected:
            messagebox.showwarning("删除题目", "请先选择一道题")
            return
        question_id = int(selected[0])
        if not messagebox.askyesno("确认删除", f"确认删除 ID 为 {question_id} 的题目吗？"):
            return
        if self.controller.delete_question(question_id):
            self.refresh_questions()
        else:
            messagebox.showerror("删除失败", "未找到该题目")

    def _export_question_bank(self) -> None:
        from tkinter import filedialog

        dlg = ExportExamDialog(self, self.controller)
        self.wait_window(dlg)
        if not dlg.result:
            return

        from datetime import datetime
        default_name = f"题库_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sudasqs"
        path = filedialog.asksaveasfilename(
            parent=self, title="导出题库", defaultextension=".sudasqs",
            filetypes=[("加密题库文件", "*.sudasqs"), ("所有文件", "*.*")],
            initialfile=default_name,
        )
        if not path:
            return
        try:
            exam_uuid = self.controller.export_question_bank(
                path, dlg.result["password"],
                dlg.result["duration_minutes"], dlg.result.get("distribution"),
                dlg.result.get("exam_type", "exam"),
            )
            dur = dlg.result["duration_minutes"]
            dist = dlg.result.get("distribution")
            extra = ""
            if dist:
                extra = f"\n题型分布：单选 {dist['单选']} 题 / 填空 {dist['填空']} 题"
            messagebox.showinfo(
                "导出成功",
                f"题库已导出。\n\n试卷 ID：{exam_uuid}\n答题时长：{dur} 分钟{extra}\n\n请将密码告知学生。",
            )
        except Exception as exc:
            messagebox.showerror("导出失败", str(exc))

    def _import_question_bank(self) -> None:
        from tkinter import filedialog

        path = filedialog.askopenfilename(
            parent=self, title="导入题库（.sudasqs 文件）",
            filetypes=[("加密题库文件", "*.sudasqs"), ("所有文件", "*.*")],
        )
        if not path:
            return
        try:
            exam_uuid, _, _, _, questions = self.controller.import_question_bank_as_teacher(path)

            self.controller.question_bank.reorder_questions([])
            for q in questions:
                self.controller.question_bank.save_question(
                    q.qtype, q.text, q.options, q.answer, q.analysis, q.score
                )
            self.refresh_questions()
            messagebox.showinfo("导入成功", f"题库已导入，共 {len(questions)} 道题。\n试卷 ID：{exam_uuid}")
        except Exception as exc:
            messagebox.showerror("导入失败", str(exc))

    def _import_pdf(self) -> None:
        from tkinter import filedialog

        api_key = self.controller.settings_manager.load_settings().get("api_key", "").strip()
        if not api_key:
            messagebox.showwarning("缺少 API Key",
                                   "请先在设置（⚙ 设置）中输入 DeepSeek API Key。")
            return

        paths = filedialog.askopenfilenames(
            parent=self, title="选择 PDF 文件（作业 + 参考答案，可多选）",
            filetypes=[("PDF 文件", "*.pdf"), ("所有文件", "*.*")],
        )
        if not paths:
            return

        from pdf_importer import import_pdfs
        try:
            questions = import_pdfs(api_key, list(paths))
        except Exception as exc:
            messagebox.showerror("导入失败", f"PDF 处理出错：{exc}")
            return

        if not questions:
            messagebox.showinfo("导入完成", "AI 未识别到选择题或填空题，没有新题目被导入。")
            return

        for q in questions:
            self.controller.question_bank.save_question(
                q.qtype, q.text, q.options, q.answer, q.analysis, q.score
            )
        self.refresh_questions()
        messagebox.showinfo("导入完成",
                            f"AI 识别并导入 {len(questions)} 道题（选择题 + 填空题）。\n请检查并编辑题目内容。")

    def _toggle_q_batch_mode(self) -> None:
        self._q_batch_mode = not self._q_batch_mode
        if self._q_batch_mode:
            self.question_table.configure(selectmode="extended")
            self._q_batch_bar.pack(fill="x", pady=(8, 0))
            self._update_q_batch_count()
        else:
            self.question_table.configure(selectmode="browse")
            self._q_batch_bar.pack_forget()
            self.question_table.selection_remove(*self.question_table.selection())

    def _on_q_batch_selection_change(self, _event) -> None:
        if self._q_batch_mode:
            self._update_q_batch_count()

    def _update_q_batch_count(self) -> None:
        count = len(self.question_table.selection())
        self._q_batch_del_btn.config(text=f"删除选中 ({count})")

    def _q_batch_select_all(self) -> None:
        for iid in self.question_table.get_children():
            self.question_table.selection_add(iid)
        self._update_q_batch_count()

    def _q_batch_invert(self) -> None:
        all_items = set(self.question_table.get_children())
        selected = set(self.question_table.selection())
        self.question_table.selection_remove(*selected)
        for iid in all_items - selected:
            self.question_table.selection_add(iid)
        self._update_q_batch_count()

    def _q_batch_delete(self) -> None:
        selected = self.question_table.selection()
        if not selected:
            return
        count = len(selected)
        if not messagebox.askyesno("批量删除", f"确认删除选中的 {count} 道题目吗？\n此操作不可恢复。"):
            return
        for iid in selected:
            self.controller.delete_question(int(iid))
        self._toggle_q_batch_mode()
        self.refresh_questions()
        messagebox.showinfo("删除完成", f"已删除 {count} 道题目。")

    def _on_question_double_click(self, _event) -> None:
        if self._drag_active:
            return
        selection = self.question_table.selection()
        if not selection:
            return
        question_id = int(selection[0])
        questions = self.controller.question_bank.load_questions()
        match = next((q for q in questions if q.id == question_id), None)
        if match is None:
            return
        EditQuestionDialog(self, self.controller, match)

    def _on_question_press(self, event) -> None:
        row = self.question_table.identify_row(event.y)
        if row:
            self._drag_item = row
            self._drag_start_y = event.y
            self._drag_active = False

    def _on_question_motion(self, event) -> None:
        if not self._drag_item:
            return
        if not self._drag_active and abs(event.y - self._drag_start_y) > self._drag_threshold:
            self._drag_active = True
            self.question_table.configure(cursor="fleur")

            self.question_table.item(self._drag_item, tags=("drag_ghost",))
            self._fade_tag_in("drag_ghost", self._drag_item)

        if self._drag_active:

            bbox = self.question_table.bbox(self.question_table.get_children()[0])
            row_h = (bbox[3] if bbox else 28) or 28
            if event.y < row_h:
                self._auto_scroll(-1)
            elif event.y > self.question_table.winfo_height() - row_h:
                self._auto_scroll(1)

            target = self.question_table.identify_row(event.y)

            if self._prev_target and self._prev_target != target and self._prev_target != self._drag_item:
                self.question_table.item(self._prev_target, tags=())
            if target and target != self._drag_item:

                self.question_table.item(target, tags=("drop_target",))
                target_idx = self.question_table.index(target)
                self.question_table.move(self._drag_item, "", target_idx)
                self._prev_target = target

    def _auto_scroll(self, direction: int) -> None:
        children = self.question_table.get_children()
        if not children:
            return
        first_visible = children[0]
        current_idx = self.question_table.index(first_visible)
        new_idx = max(0, current_idx + direction)
        if new_idx < len(children):
            self.question_table.yview_moveto(new_idx / max(1, len(children)))

    def _on_question_release(self, event) -> None:
        if self._drag_active:
            self.question_table.configure(cursor="")

            for iid in self.question_table.get_children():
                self.question_table.item(iid, tags=())
            self._prev_target = None
            self._apply_reorder()

            self._animate_reorder_flash()
        self._drag_item = None
        self._drag_active = False

    def _fade_tag_in(self, tag_name: str, iid: str, step: int = 0, max_steps: int = 5) -> None:
        if self._drag_item != iid:
            return
        colors = ["#eff6ff", "#dbeafe", "#bfdbfe", "#93c5fd", "#dbeafe"]
        idx = min(step, len(colors) - 1)
        self.question_table.tag_configure(tag_name, background=colors[idx])
        if step < max_steps:
            self.after(40, lambda: self._fade_tag_in(tag_name, iid, step + 1, max_steps))

    def _animate_reorder_flash(self) -> None:
        colors = ["#fef9c3", "#fef3c7", "#fefce8", "#fffbeb", "#ffffff"]
        children = list(self.question_table.get_children())

        def _step(s: int) -> None:
            if s >= len(colors):

                for iid in self.question_table.get_children():
                    self.question_table.item(iid, tags=())
                return
            for iid in children:
                self.question_table.tag_configure(f"flash_{s}", background=colors[s])
                self.question_table.item(iid, tags=(f"flash_{s}",))
            self.after(60, lambda: _step(s + 1))

        _step(0)

    def _apply_reorder(self) -> None:
        ordered_ids: List[int] = []
        for iid in self.question_table.get_children():
            ordered_ids.append(int(iid))
        try:
            self.controller.question_bank.reorder_questions(ordered_ids)
        except RuntimeError as exc:
            messagebox.showerror("排序失败", str(exc))
            return
        self.refresh_questions()

class SettingsDialog(tk.Toplevel):

    COLOR_KEYS = ["BG", "PANEL", "TEXT", "MUTED", "PRIMARY", "SUCCESS", "DANGER", "BORDER"]
    COLOR_LABELS = {
        "BG": "页面背景色", "PANEL": "卡片底色", "TEXT": "标题文字",
        "MUTED": "辅助说明", "PRIMARY": "主题色（按钮/图表）",
        "SUCCESS": "成功色（正确/及格）", "DANGER": "危险色（错误/不及格）",
        "BORDER": "边框线色",
    }
    FONT_OPTIONS = [
        "Lolita", "Microsoft YaHei", "SimSun", "SimHei", "KaiTi", "FangSong",
        "Arial", "Consolas", "Segoe UI", "Times New Roman", "Courier New",
    ]

    def __init__(self, parent, controller) -> None:
        super().__init__(parent)
        self.controller = controller
        _set_bg_image(self, 0.60)
        self.title("设置 — 自定义外观")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.transient(parent)
        self.grab_set()

        settings = controller.settings_manager.load_settings()
        self.colors: Dict[str, str] = dict(settings["colors"])
        self.font_family: str = settings.get("font_family", "Microsoft YaHei")
        self.api_key: str = settings.get("api_key", "")
        self._color_swatches: Dict[str, tk.Frame] = {}
        self._preview_labels: list = []

        self._build_ui()
        self._update_preview()
        self.geometry("")

    def _build_ui(self) -> None:
        body = ttk.Frame(self, padding=20, style="App.TFrame")
        body.pack(fill="both", expand=True)

        font_row = 0
        ttk.Label(body, text="字体设置", style="Section.TLabel").grid(
            row=font_row, column=0, columnspan=4, sticky="w", pady=(0, 8)
        )
        ttk.Label(body, text="全局字体").grid(row=font_row + 1, column=0, sticky="w", padx=(10, 10))
        self.font_var = tk.StringVar(value=self.font_family)
        font_combo = ttk.Combobox(
            body, textvariable=self.font_var, values=self.FONT_OPTIONS, width=22, state="readonly"
        )
        font_combo.grid(row=font_row + 1, column=1, sticky="w")
        font_combo.bind("<<ComboboxSelected>>", lambda _e: self._update_preview())

        color_start = font_row + 2
        ttk.Label(body, text="颜色设置", style="Section.TLabel").grid(
            row=color_start, column=0, columnspan=4, sticky="w", pady=(18, 8)
        )

        self._color_vars: Dict[str, tk.StringVar] = {}
        self._color_entries: Dict[str, ttk.Entry] = {}
        for idx, key in enumerate(self.COLOR_KEYS):
            row = color_start + 1 + idx
            ttk.Label(body, text=self.COLOR_LABELS[key]).grid(
                row=row, column=0, sticky="w", padx=(10, 10), pady=3
            )
            var = tk.StringVar(value=self.colors[key])
            entry = ttk.Entry(body, textvariable=var, width=10)
            entry.grid(row=row, column=1, sticky="w", pady=3)
            entry.bind("<KeyRelease>", lambda _e, k=key: self._on_color_entry(k))
            self._color_vars[key] = var
            self._color_entries[key] = entry

            swatch = tk.Frame(body, width=22, height=22, relief="ridge", bd=1)
            swatch.grid(row=row, column=2, padx=(8, 4), pady=3)
            self._color_swatches[key] = swatch

            ttk.Button(
                body, text="选色",
                command=lambda k=key: self._pick_color(k),
            ).grid(row=row, column=3, padx=(4, 0), pady=3)

        for key in self.COLOR_KEYS:
            self._update_swatch(key)

        preview_row = color_start + 1 + len(self.COLOR_KEYS)
        ttk.Label(body, text="实时预览", style="Section.TLabel").grid(
            row=preview_row, column=0, columnspan=4, sticky="w", pady=(18, 6)
        )

        preview_frame = tk.Frame(body, bg=self.colors["BG"], highlightthickness=1, highlightbackground=self.colors["BORDER"])
        preview_frame.grid(row=preview_row + 1, column=0, columnspan=4, sticky="ew", pady=(0, 14))
        body.columnconfigure(0, weight=1)

        self._preview_title = tk.Label(
            preview_frame, text="标题文字 Title",
            font=(self.font_family, 16, "bold"), fg=self.colors["TEXT"], bg=self.colors["BG"],
        )
        self._preview_title.pack(anchor="w", padx=14, pady=(10, 2))

        self._preview_body = tk.Label(
            preview_frame, text="正文内容 Body Text — 辅助说明文字 muted text",
            font=(self.font_family, 10), fg=self.colors["TEXT"], bg=self.colors["BG"],
        )
        self._preview_body.pack(anchor="w", padx=14, pady=2)

        tags_frame = tk.Frame(preview_frame, bg=self.colors["BG"])
        tags_frame.pack(anchor="w", padx=14, pady=6)
        self._preview_success = tk.Label(
            tags_frame, text="✓ 正确/通过", font=(self.font_family, 10, "bold"),
            fg=self.colors["SUCCESS"], bg=self.colors["BG"],
        )
        self._preview_success.pack(side="left", padx=(0, 16))
        self._preview_danger = tk.Label(
            tags_frame, text="✗ 错误/失败", font=(self.font_family, 10, "bold"),
            fg=self.colors["DANGER"], bg=self.colors["BG"],
        )
        self._preview_danger.pack(side="left", padx=(0, 16))
        self._preview_muted = tk.Label(
            tags_frame, text="辅助说明", font=(self.font_family, 10),
            fg=self.colors["MUTED"], bg=self.colors["BG"],
        )
        self._preview_muted.pack(side="left")

        mock_btn = tk.Frame(preview_frame, bg=self.colors["PRIMARY"], width=90, height=32)
        mock_btn.pack_propagate(False)
        mock_btn.pack(anchor="w", padx=14, pady=(4, 10))
        self._preview_btn = tk.Label(
            mock_btn, text="按钮样例", font=(self.font_family, 10),
            fg="white", bg=self.colors["PRIMARY"],
        )
        self._preview_btn.pack(expand=True)

        api_row = preview_row + 2
        ttk.Label(body, text="在此处输入 API Keys", style="Section.TLabel").grid(
            row=api_row, column=0, columnspan=4, sticky="w", pady=(18, 8)
        )
        self.api_key_var = tk.StringVar(value=self.api_key)
        ttk.Entry(body, textvariable=self.api_key_var, width=50, show="*").grid(
            row=api_row + 1, column=0, columnspan=4, sticky="ew", pady=(0, 4), padx=(10, 0))
        ttk.Label(body, text="支持 DeepSeek API Key，用于 PDF 智能导入题库。",
                  style="Muted.TLabel").grid(
            row=api_row + 2, column=0, columnspan=4, sticky="w", padx=(10, 0), pady=(0, 12))

        btn_row = ttk.Frame(body, style="App.TFrame")
        btn_row.grid(row=api_row + 3, column=0, columnspan=4, sticky="ew", pady=(4, 0))
        RoundedButton(btn_row, text="恢复默认", command=self._reset_defaults, width=90).pack(side="left")
        RoundedButton(btn_row, text="取消", command=self.destroy, width=80).pack(side="right", padx=(10, 0))
        RoundedButton(btn_row, text="保存设置", command=self._save, width=90).pack(side="right")

    def _on_color_entry(self, key: str) -> None:
        value = self._color_vars[key].get().strip()
        if value.startswith("#") and len(value) == 7:
            self.colors[key] = value
        self._update_swatch(key)
        self._update_preview()

    def _pick_color(self, key: str) -> None:
        try:
            from tkinter.colorchooser import askcolor
        except ImportError:
            messagebox.showinfo("提示", "当前环境不支持系统取色器，请直接输入十六进制颜色码。")
            return
        result = askcolor(color=self.colors[key], title=f"选择 {self.COLOR_LABELS[key]}")
        if result and result[1]:
            self.colors[key] = result[1]
            self._color_vars[key].set(result[1])
            self._update_swatch(key)
            self._update_preview()

    def _update_swatch(self, key: str) -> None:
        swatch = self._color_swatches.get(key)
        if swatch:
            try:
                swatch.configure(bg=self.colors[key])
            except tk.TclError:
                pass

    def _update_preview(self) -> None:
        font = self.font_var.get()
        c = self.colors
        self.configure(bg=c["BG"])

        if hasattr(self, "_preview_title"):
            self._preview_title.configure(font=(font, 16, "bold"), fg=c["TEXT"], bg=c["BG"])
            self._preview_body.configure(font=(font, 10), fg=c["TEXT"], bg=c["BG"])
            self._preview_success.configure(font=(font, 10, "bold"), fg=c["SUCCESS"], bg=c["BG"])
            self._preview_danger.configure(font=(font, 10, "bold"), fg=c["DANGER"], bg=c["BG"])
            self._preview_muted.configure(font=(font, 10), fg=c["MUTED"], bg=c["BG"])
            self._preview_btn.configure(font=(font, 10), bg=c["PRIMARY"])
            self._preview_btn.master.configure(bg=c["PRIMARY"])

            self._preview_title.master.configure(bg=c["BG"])
            self._preview_success.master.configure(bg=c["BG"])

    def _save(self) -> None:
        font = self.font_var.get()
        colors = {}
        for key in self.COLOR_KEYS:
            value = self._color_vars[key].get().strip()
            if value.startswith("#") and len(value) == 7:
                colors[key] = value
            else:
                messagebox.showwarning("格式错误", f"{self.COLOR_LABELS[key]} 格式不正确，请输入 #RRGGBB 格式。")
                return
        settings = {"font_family": font, "colors": colors, "api_key": self.api_key_var.get().strip()}
        self.controller.apply_settings(settings)
        messagebox.showinfo("设置已保存", "外观设置已生效并持久化保存。")
        self.destroy()

    def _reset_defaults(self) -> None:
        if not messagebox.askyesno("恢复默认", "确认将所有外观设置恢复为默认值？"):
            return
        defaults = self.controller.settings_manager.reset_defaults()
        self.colors = dict(defaults["colors"])
        self.font_family = defaults["font_family"]
        self.font_var.set(self.font_family)
        for key, var in self._color_vars.items():
            var.set(self.colors[key])
            self._update_swatch(key)
        self._update_preview()

def _register_font(font_path: str) -> str:
    import ctypes
    from pathlib import Path

    path = str(Path(font_path).resolve())
    try:

        ctypes.windll.gdi32.AddFontResourceW(path)

        HWND_BROADCAST = 0xFFFF
        WM_FONTCHANGE = 0x001D
        ctypes.windll.user32.PostMessageW(HWND_BROADCAST, WM_FONTCHANGE, 0, 0)
    except Exception:
        pass

    try:
        from PIL import ImageFont
        f = ImageFont.truetype(path, 12)

        names = f.getname()
        for name_tuple in names:
            for n in name_tuple:
                if n and isinstance(n, str) and n.strip():

                    if n.lower() not in ("regular", "bold", "italic", "bold italic"):
                        return n

        if names and names[0]:
            return str(names[0][0])
    except Exception:
        pass
    return Path(font_path).stem

def configure_styles(root: tk.Tk, settings: dict | None = None) -> None:
    global BG, PANEL, TEXT, MUTED, PRIMARY, SUCCESS, DANGER, BORDER, FONT_FAMILY

    from pathlib import Path
    loli_path = Path(__file__).resolve().parent / "assets" / "loli.ttf"
    loli_family = ""
    if loli_path.exists():
        loli_family = _register_font(str(loli_path))

    DEFAULT_FONT = loli_family or "Lolita"

    if settings:
        colors = settings.get("colors", {})
        BG = colors.get("BG", BG)
        PANEL = colors.get("PANEL", PANEL)
        TEXT = colors.get("TEXT", TEXT)
        MUTED = colors.get("MUTED", MUTED)
        PRIMARY = colors.get("PRIMARY", PRIMARY)
        SUCCESS = colors.get("SUCCESS", SUCCESS)
        DANGER = colors.get("DANGER", DANGER)
        BORDER = colors.get("BORDER", BORDER)
        font_family = settings.get("font_family", DEFAULT_FONT)
    else:
        font_family = DEFAULT_FONT

    FONT_FAMILY = font_family
    RoundedButton.update_all_fonts(font_family)

    style = ttk.Style(root)
    style.theme_use("clam")
    root.configure(bg=BG)

    style.configure("App.TFrame", background=BG)
    style.configure("Card.TFrame", background=PANEL, relief="solid", borderwidth=1)
    style.configure("TLabel", background=BG, foreground=TEXT, font=(font_family, 11))
    style.configure("Title.TLabel", background=BG, foreground=TEXT, font=(font_family, 24, "bold"))
    style.configure("Section.TLabel", background=BG, foreground=TEXT, font=(font_family, 14, "bold"))
    style.configure("Muted.TLabel", background=BG, foreground=MUTED, font=(font_family, 11))
    style.configure("Timer.TLabel", background=BG, foreground=DANGER, font=("Consolas", 16, "bold"))
    style.configure("Question.TLabel", background=PANEL, foreground=TEXT, font=(font_family, 16, "bold"))
    style.configure("QuestionSmall.TLabel", background=PANEL, foreground=TEXT, font=(font_family, 12, "bold"))

    style.configure("TButton", font=(font_family, 11), padding=(12, 7))
    style.configure("Primary.TButton", foreground="#ffffff", background=PRIMARY)
    style.map("Primary.TButton", background=[("active", _darken(PRIMARY))])
    style.configure("Danger.TButton", foreground="#ffffff", background=DANGER)
    style.map("Danger.TButton", background=[("active", _darken(DANGER))])

    style.configure("Treeview", font=(font_family, 11), rowheight=30)
    style.configure("Treeview.Heading", font=(font_family, 11, "bold"))
    style.configure("Exam.TRadiobutton", font=(font_family, 16), background=PANEL)

def _darken(hex_color: str, factor: float = 0.85) -> str:
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    r, g, b = int(r * factor), int(g * factor), int(b * factor)
    return f"#{r:02x}{g:02x}{b:02x}"