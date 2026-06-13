from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import fitz
import requests

from data_manager import Question

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"

_SYSTEM_PROMPT = """你是一个题库导入助手。请从提供的材料中提取所有**选择题**和**填空题**。

规则：
1. 只提取选择题（单选/多选）和填空题，忽略判断题、解答题等
2. 题目类型 qtype 只能是 "单选" 或 "填空"
3. 选择题的选项以 A. B. C. D. 形式列出
4. 从参考答案中确定正确答案
5. 每道题分值 score 默认 10
6. **必须**为每道题生成一段简短的解析（analysis 字段），即使是填空题也要写解析：
   - 优先使用参考答案中的解析内容
   - 如果参考答案中没有解析，你必须结合题目内容和正确答案，用AI能力自行分析并撰写一段简短的解析
   - 解析要说明为什么这个答案是正确的，简要解释涉及的知识点
   - 解析字数控制在 30-80 字左右，简洁明了

请严格按以下 JSON 格式输出（不要输出其他内容）：
{
  "questions": [
    {
      "qtype": "单选",
      "text": "题目文本",
      "options": ["A. 选项A", "B. 选项B"],
      "answer": "A",
      "analysis": "解析内容（必填，30-80字）"
    },
    {
      "qtype": "填空",
      "text": "题目文本，用 ____ 表示填空处",
      "options": [],
      "answer": "正确答案",
      "analysis": "解析内容（必填，30-80字）"
    }
  ]
}"""

def extract_pdf_text(filepath: str) -> str:
    doc = fitz.open(filepath)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text.strip()

def _extract_week_number(filename: str) -> Optional[int]:
    match = re.search(r"第\s*(\d+)\s*周", filename)
    if match:
        return int(match.group(1))
    return None

def match_files(pdf_paths: List[str]) -> List[Tuple[str, Optional[str]]]:

    week_map: Dict[int, Dict[str, Optional[str]]] = {}
    orphans: List[str] = []

    for path in pdf_paths:
        name = Path(path).stem
        week = _extract_week_number(name)
        is_answer = "答案" in name or "参考" in name or "answer" in name.lower()
        if week is not None:
            week_map.setdefault(week, {"assignment": None, "answer": None})
            key = "answer" if is_answer else "assignment"
            week_map[week][key] = path
        else:
            orphans.append(path)

    pairs: List[Tuple[str, Optional[str]]] = []
    for week in sorted(week_map.keys()):
        entry = week_map[week]
        assignment = entry.get("assignment")
        answer = entry.get("answer")
        if assignment:
            pairs.append((assignment, answer))
    for path in orphans:
        pairs.append((path, None))
    return pairs

def _call_deepseek(api_key: str, prompt: str) -> str:
    resp = requests.post(
        DEEPSEEK_API_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": DEEPSEEK_MODEL,
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
        },
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]

def _parse_ai_response(response_text: str) -> List[Question]:

    text = response_text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*\n", "", text)
        text = re.sub(r"\n```\s*$", "", text)

    try:
        data = json.loads(text)
    except json.JSONDecodeError:

        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            data = json.loads(match.group())
        else:
            return []

    questions: List[Question] = []
    for item in data.get("questions", []):
        qtype = item.get("qtype", "单选")
        if qtype not in ("单选", "填空"):
            continue
        text_q = item.get("text", "").strip()
        if not text_q:
            continue
        options = item.get("options", [])
        answer = item.get("answer", "").strip()
        analysis = item.get("analysis", "").strip()
        score = int(item.get("score", 10))
        questions.append(Question(
            id=0,
            qtype=qtype,
            text=text_q,
            options=options,
            answer=answer,
            analysis=analysis,
            score=score,
        ))
    return questions

def import_pdfs(api_key: str, pdf_paths: List[str]) -> List[Question]:
    if not api_key.strip():
        raise ValueError("请先在设置中输入 DeepSeek API Key")

    pairs = match_files(pdf_paths)
    all_questions: List[Question] = []

    for assign_path, answer_path in pairs:
        assign_text = extract_pdf_text(assign_path)
        assign_name = Path(assign_path).stem

        answer_text = ""
        if answer_path:
            answer_text = extract_pdf_text(answer_path)

        prompt = f"【作业文件名】{assign_name}\n\n【作业内容】\n{assign_text}"
        if answer_text:
            prompt += f"\n\n【参考答案】\n{answer_text}"
        prompt += "\n\n请提取其中的选择题和填空题。"

        try:
            response = _call_deepseek(api_key, prompt)
            questions = _parse_ai_response(response)
            all_questions.extend(questions)
        except Exception as exc:

            print(f"[PDF导入] 处理 {assign_name} 失败: {exc}")

    return all_questions