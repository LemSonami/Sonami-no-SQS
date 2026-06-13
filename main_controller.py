from __future__ import annotations

import random
from pathlib import Path
from typing import Dict, List, Optional

from data_manager import (
    ExamTracker,
    Question,
    QuestionBank,
    ScoreManager,
    SettingsManager,
    UserDB,
    export_question_bank_to_bytes,
    import_question_bank_as_student,
    import_question_bank_as_teacher,
)

class QuizEngine:

    def __init__(self, question_bank: QuestionBank, exam_size: int = 5) -> None:
        self.question_bank = question_bank
        self.exam_size = exam_size
        self.questions: List[Question] = []
        self.answers: Dict[int, str] = {}

    def start_exam(self) -> List[Question]:
        all_questions = self.question_bank.load_questions()
        if not all_questions:
            raise RuntimeError("题库为空，请先由教师添加题目")
        count = min(self.exam_size, len(all_questions))
        self.questions = random.sample(all_questions, count)
        self.answers = {}
        return self.questions

    def record_answer(self, question_id: int, answer: str) -> None:
        self.answers[question_id] = answer.strip()

    def unanswered_count(self) -> int:
        return sum(1 for question in self.questions if not self.answers.get(question.id))

    def calculate_score(self) -> Dict[str, object]:
        score = 0
        total = sum(question.score for question in self.questions)
        wrong_questions: List[Question] = []
        details: List[Dict[str, object]] = []
        type_stats: Dict[str, Dict[str, int]] = {}

        for question in self.questions:
            user_answer = self.answers.get(question.id, "").strip()
            correct = self._is_correct(question, user_answer)
            stats = type_stats.setdefault(question.qtype, {"right": 0, "total": 0})
            stats["total"] += 1

            if correct:
                score += question.score
                stats["right"] += 1
            else:
                wrong_questions.append(question)

            details.append(
                {
                    "question": question,
                    "user_answer": user_answer or "未作答",
                    "correct": correct,
                }
            )

        return {
            "score": score,
            "total": total,
            "wrong_questions": wrong_questions,
            "wrong_ids": [question.id for question in wrong_questions],
            "details": details,
            "type_stats": type_stats,
        }

    def _is_correct(self, question: Question, user_answer: str) -> bool:
        if question.qtype == "填空":
            return user_answer.strip().lower() == question.answer.strip().lower()
        return user_answer.strip().upper() == question.answer.strip().upper()

class AppController:

    def __init__(self, root) -> None:
        self.root = root
        self.user_db = UserDB()
        self.user_db.load_users()
        self.question_bank = QuestionBank()
        self.score_manager = ScoreManager()
        self.settings_manager = SettingsManager()
        self.exam_tracker = ExamTracker()
        self.current_user: Optional[Dict[str, str]] = None
        self.current_view = None
        self.quiz_engine = QuizEngine(self.question_bank)
        self.last_result: Optional[Dict[str, object]] = None
        self.last_exam_time: str = ""
        self._current_exam_uuid: str = ""
        self._exam_duration: int = 600

    def set_view(self, view) -> None:
        if self.current_view is not None:
            self.current_view.destroy()
        self.current_view = view
        self.current_view.pack(fill="both", expand=True)

    def show_login(self) -> None:
        from ui_views import LoginWindow

        self.current_user = None
        self.set_view(LoginWindow(self.root, self))

    def login(self, student_id: str, name: str, password: str) -> bool:
        user = self.user_db.authenticate(student_id, name, password)
        if not user:
            return False
        self.current_user = user

        import json
        from data_manager import LOGIN_CACHE_FILE
        try:
            old = {}
            if LOGIN_CACHE_FILE.exists():
                old = json.loads(LOGIN_CACHE_FILE.read_text(encoding="utf-8"))
            cache = {"student_id": student_id, "name": name, "password": password,
                     "avatar_base64": old.get("avatar_base64", "")}
            LOGIN_CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass
        if user["role"] == "teacher":
            self.show_teacher_dashboard()
        else:
            self.show_student_dashboard()
        return True

    def show_student_dashboard(self) -> None:
        from ui_views import StudentDashboard

        if self.current_user and not self.current_user.get("avatar_base64"):
            from data_manager import load_avatar
            sid = self.current_user.get("student_id", "")
            avatar = load_avatar(sid)
            if avatar:
                self.current_user["avatar_base64"] = avatar
        self.set_view(StudentDashboard(self.root, self))

    def show_teacher_dashboard(self) -> None:
        from ui_views import TeacherDashboard

        self.set_view(TeacherDashboard(self.root, self))

    def start_exam(self, questions: List[Question] | None = None,
                   exam_uuid: str = "", duration_seconds: int = 600) -> None:
        from ui_views import QuizWindow

        if questions:
            self.quiz_engine.questions = questions
            self.quiz_engine.answers = {}
            self.quiz_engine.exam_size = len(questions)
        else:
            self.quiz_engine.start_exam()
        self._current_exam_uuid = exam_uuid
        self._exam_duration = duration_seconds
        self.last_result = None
        self.set_view(QuizWindow(self.root, self, duration_seconds))

    def export_question_bank(self, filepath: str, password: str,
                            duration_minutes: int = 30,
                            distribution: dict | None = None,
                            exam_type: str = "exam") -> str:
        questions = self.question_bank.load_questions()
        exam_uuid, data = export_question_bank_to_bytes(
            questions, password, duration_minutes, distribution, exam_type,
        )
        Path(filepath).write_bytes(data)
        return exam_uuid

    def import_question_bank_as_teacher(self, filepath: str) -> tuple:
        data = Path(filepath).read_bytes()
        return import_question_bank_as_teacher(data)

    def import_question_bank_for_exam(self, filepath: str, password: str) -> tuple:
        data = Path(filepath).read_bytes()
        return import_question_bank_as_student(data, password)

    def _pick_exam_questions(self, questions: List[Question],
                             distribution: dict | None = None) -> List[Question]:
        import random

        if distribution is None:
            count = min(10, len(questions))
            return random.sample(questions, count)

        selected: List[Question] = []
        remaining = list(questions)

        for qtype, count in distribution.items():
            pool = [q for q in remaining if q.qtype == qtype]
            n = min(count, len(pool))
            chosen = random.sample(pool, n) if n > 0 else []
            selected.extend(chosen)
            for c in chosen:
                remaining.remove(c)

        return selected

    def is_exam_completed(self, username: str, exam_uuid: str) -> bool:
        return self.exam_tracker.is_completed(username, exam_uuid)

    def mark_exam_completed(self, username: str, exam_uuid: str) -> None:
        self.exam_tracker.mark_completed(username, exam_uuid)

    def submit_exam(self) -> Dict[str, object]:
        if self.current_user is None:
            raise RuntimeError("请先登录")
        from datetime import datetime

        self.last_result = self.quiz_engine.calculate_score()

        wrong_answers: Dict[int, str] = {}
        for detail in self.last_result.get("details", []):
            if not detail["correct"]:
                wrong_answers[detail["question"].id] = detail["user_answer"]
        self.last_exam_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.score_manager.record_score(
            self.current_user,
            int(self.last_result["score"]),
            int(self.last_result["total"]),
            self.last_result["wrong_ids"],
            self.last_result["type_stats"],
            wrong_answers,
        )
        if self._current_exam_uuid:
            self.exam_tracker.mark_completed(
                self.current_user["student_id"], self._current_exam_uuid
            )
            self._current_exam_uuid = ""
        return self.last_result

    def show_result(self, result: Optional[Dict[str, object]] = None) -> None:
        from ui_views import ResultWindow

        self.set_view(ResultWindow(self.root, self, result or self.last_result))

    def show_wrong_book(self) -> None:
        from ui_views import WrongBookWindow

        self.set_view(WrongBookWindow(self.root, self))

    def add_question(
        self,
        qtype: str,
        text: str,
        options: List[str],
        answer: str,
        analysis: str,
        score: int,
    ) -> Question:
        return self.question_bank.save_question(qtype, text, options, answer, analysis, score)

    def delete_question(self, question_id: int) -> bool:
        return self.question_bank.delete_question(question_id)

    def show_settings(self) -> None:
        from ui_views import SettingsDialog

        SettingsDialog(self.root, self)

    def apply_settings(self, settings: dict) -> None:
        from ui_views import configure_styles

        self.settings_manager.save_settings(settings)
        configure_styles(self.root, settings)

    def save_avatar(self, student_id: str, avatar_b64: str) -> None:
        from data_manager import save_avatar as _save_avatar, LOGIN_CACHE_FILE
        import json

        _save_avatar(student_id, avatar_b64)

        try:
            cache = {}
            if LOGIN_CACHE_FILE.exists():
                cache = json.loads(LOGIN_CACHE_FILE.read_text(encoding="utf-8"))
            cache["avatar_base64"] = avatar_b64
            LOGIN_CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass

    def export_current_result(self, filepath: str) -> None:
        import json

        from crypto_utils import encrypt_bytes

        if self.last_result is None or self.current_user is None:
            raise RuntimeError("没有可导出的考试结果")
        wrong_answers: Dict[int, str] = {}
        for detail in self.last_result.get("details", []):
            if not detail["correct"]:
                wrong_answers[detail["question"].id] = detail["user_answer"]
        record = {
            "username": self.current_user.get("username", ""),
            "student_id": self.current_user.get("student_id", ""),
            "student_name": self.current_user.get("name", ""),
            "password": self.current_user.get("password", ""),
            "score": int(self.last_result["score"]),
            "total": int(self.last_result["total"]),
            "exam_time": self.last_exam_time,
            "wrong_ids": self.last_result.get("wrong_ids", []),
            "type_stats": self.last_result.get("type_stats", {}),
            "wrong_answers": {str(k): v for k, v in wrong_answers.items()},
            "avatar_base64": self.current_user.get("avatar_base64", ""),
        }
        payload = json.dumps(record, ensure_ascii=False).encode("utf-8")
        Path(filepath).write_bytes(encrypt_bytes(payload))

    def import_result_file(self, filepath: str) -> None:
        import json

        from crypto_utils import decrypt_bytes

        raw = decrypt_bytes(Path(filepath).read_bytes())
        record = json.loads(raw.decode("utf-8"))

        if not record.get("exam_time"):
            from datetime import datetime

            record["exam_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        student_name = str(record.get("student_name", ""))
        student_id = str(record.get("student_id", ""))
        if not self.user_db.is_registered(student_id):
            raise ValueError(f"{student_name} 学生不在学生名单中")

        self.score_manager.import_record(record)

        avatar = record.get("avatar_base64", "")
        if avatar:
            from data_manager import save_avatar as _save_avatar
            _save_avatar(student_id, avatar)

    def get_wrong_questions_for_current_user(self) -> List[Question]:
        if self.current_user is None:
            return []
        wrong_ids = set(self.score_manager.all_wrong_ids(self.current_user.get("username", self.current_user.get("student_id", ""))))
        return [
            question
            for question in self.question_bank.load_questions()
            if question.id in wrong_ids
        ]