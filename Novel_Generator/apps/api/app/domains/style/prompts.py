MACRO_PROMPT = """分析以下小说采样片段，输出 JSON：
{{
  "pov": "叙事视角",
  "sentence_rhythm": "句式节奏特点",
  "dialogue_ratio": "对话占比估计",
  "pacing": "叙事节奏",
  "emotional_tone": "情感基调"
}}
作者：{author}
作品：《{title}》
总字数约：{word_count}
采样：
{samples}
"""


TECHNIQUE_PROMPT = """分析以下小说采样片段的写作手法，输出 JSON：
{{
  "techniques": ["手法1", "手法2"],
  "hooks": ["开篇/章末钩子习惯"],
  "vocabulary": {{"register": "语体/register", "taboo": ["应避免的写法"]}}
}}
作者：{author}
采样：
{samples}
"""


SYNTHESIS_PROMPT = """根据宏观与手法分析，为作者 {author}（《{title}》） synthesize 文风画像。
输出 JSON：
{{
  "voice_summary": "一句话文风概括",
  "profile_json": {{
    "pov": "",
    "sentence_rhythm": "",
    "dialogue_ratio": "",
    "pacing": "",
    "emotional_tone": "",
    "vocabulary": {{"register": "", "taboo": []}},
    "techniques": [],
    "hooks": [],
    "example_excerpts": ["摘录1", "摘录2"]
  }},
  "skill_markdown": "Markdown 正文（不含 frontmatter），含核心规则、禁止事项、参考摘录"
}}
宏观：{macro}
手法：{technique}
"""
