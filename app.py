import os
from flask import Flask, render_template, request, jsonify, send_from_directory
from statistics import mean
import json

# اختياري: دعم OpenAI إن وُجد مفتاح (سيبقى اختيارياً)
USE_OPENAI = bool(os.getenv("OPENAI_API_KEY"))
if USE_OPENAI:
    try:
        import openai
        openai.api_key = os.getenv("OPENAI_API_KEY")
    except Exception as e:
        # لو لم تُثبّت الحزمة لن ينهار التطبيق — سنستخدم الخوارزمية المحلية
        USE_OPENAI = False

app = Flask(__name__, template_folder="templates", static_folder="static")


def safe_float(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def avg_of_semesters(values):
    nums = [safe_float(v) for v in values if safe_float(v) is not None]
    if not nums:
        return None
    # متوسط حسابي
    return round(mean(nums), 2)


def local_weighted_ranking(level, sec_type, subjects, annual_general):
    """
    خوارزمية محلية تعتمد أوزان لكل تخصص كما في المواصفات.
    subjects: dict of subject_key -> avg (or None)
    ترجع قائمة مرتبّة من التخصّصات مع درجات (0-20) أو None إذا لا بيانات.
    """
    suggestions = []
    if level == "middle":
        weights_map = {
            "علوم تجريبية": {
                "العلوم_الطبيعية": 0.4, "الفيزياء": 0.3, "الرياضيات": 0.2, "اللغة_العربية": 0.05, "الفرنسية": 0.05
            },
            "رياضيات": {
                "الرياضيات": 0.6, "الفيزياء": 0.25, "الفرنسية": 0.05, "اللغة_العربية": 0.1
            },
            "تقني رياضي": {
                "الرياضيات": 0.45, "الفيزياء": 0.35, "العلوم_الطبيعية": 0.15, "الفرنسية": 0.05
            }
        }
    else:  # secondary
        if sec_type == "science":
            weights_map = {
                "علوم تجريبية": {"العلوم_الطبيعية":0.45,"الفيزياء":0.3,"الرياضيات":0.15,"الفرنسية":0.05,"اللغة_العربية":0.05},
                "رياضيات": {"الرياضيات":0.6,"الفيزياء":0.25,"الفرنسية":0.05,"اللغة_العربية":0.1},
                "تقني رياضي": {"الرياضيات":0.5,"الفيزياء":0.3,"العلوم_الطبيعية":0.15,"الفرنسية":0.05},
                "تسيير واقتصاد": {"الرياضيات":0.35,"الفرنسية":0.2,"اللغة_العربية":0.25,"الانجليزية":0.2}
            }
        else:
            weights_map = {
                "آداب وفلسفة": {"اللغة_العربية":0.45,"الفلسفة":0.35,"الفرنسية":0.1,"الانجليزية":0.1},
                "لغات أجنبية": {"الفرنسية":0.45,"الانجليزية":0.45,"اللغة_العربية":0.1}
            }

    def score_specialty(weights):
        total_w = 0.0
        total_score = 0.0
        for sub, w in weights.items():
            val = subjects.get(sub)
            if val is None:
                continue
            total_w += w
            total_score += val * w
        if total_w == 0:
            return None
        return round(total_score / total_w, 2)

    for name, w in weights_map.items():
        sc = score_specialty(w)
        suggestions.append({"name": name, "score": sc})

    # ترتيب (None في الأسفل)
    suggestions_sorted = sorted(suggestions, key=lambda x: (x["score"] is None, -(x["score"] or 0)))
    return suggestions_sorted


def ai_ranking_prompt(level, sec_type, subjects, annual_general):
    """
    إن وُجد OpenAI API، نبني Prompt يطلب من النموذج تقييم كل تخصص (0-20) اعتمادًا على المعدلات.
    نرسل القيم ونطلب ترتيباً مع شرح مختصر لكل اختيار.
    """
    prompt = {
        "level": level,
        "sec_type": sec_type,
        "annual_general": annual_general,
        "subjects": subjects,
        "instruction": (
            "أنت مساعد لتوجيه تلاميذ المدارس في الجزائر. قيم مدى ملاءمة كل تخصص (0-20) "
            "بناءً على معدلات المواد المرسلة (كل مادة قيمة وسطية سنوية إن وُجدت، أو null). "
            "أعد ترتيب التخصصات من الأكثر ملاءمة إلى الأقل، وارجع JSON مع الحقول: "
            "[name, score (number or null), reason (brief in Arabic)]. لا تزيد التفسيرات عن جملة واحدة لكل تخصص."
        )
    }
    return prompt


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/result_page")
def result_page():
    # صفحة بديلة قد لا تُستخدم عادةً لأن SPA تعرض النتائج داخل الصفحة
    return render_template("result.html")


@app.route("/analyze/", methods=["POST"])
def analyze():
    # نتوقع JSON
    data = request.get_json(force=True, silent=True) or request.form or {}
    level = data.get("level", "").strip()
    sec_type = data.get("sec_type", "").strip()
    annual_general = safe_float(data.get("annual_general"))

    # قائمة المواد المحتملة
    candidate_subjects = [
        "اللغة_العربية","الرياضيات","الفرنسية","الفيزياء","العلوم_الطبيعية","الانجليزية","الفلسفة"
    ]
    subjects = {}
    for sub in candidate_subjects:
        s1 = data.get(f"{sub}_s1")
        s2 = data.get(f"{sub}_s2")
        s3 = data.get(f"{sub}_s3")
        subjects[sub] = avg_of_semesters([s1, s2, s3])

    # إذا توافر مفتاح OpenAI: استخدمه للحصول على ترتيب أذكى، وإلا استخدم التحليل المحلي
    ranking = None
    details = None
    if USE_OPENAI:
        try:
            prompt = ai_ranking_prompt(level, sec_type, subjects, annual_general)
            # استدعاء مبسط: نرسل prompt كنص. قد تحتاج تعديل حسب نسخة مكتبة openai المثبتة.
            completion = openai.ChatCompletion.create(
                model="gpt-4o-mini" if "gpt-4o-mini" in openai.Model.list() else "gpt-4o",
                messages=[{"role":"system","content":prompt["instruction"]},
                          {"role":"user","content":json.dumps({
                              "level":level,
                              "sec_type":sec_type,
                              "annual_general":annual_general,
                              "subjects":subjects
                          }, ensure_ascii=False)}],
                max_tokens=400,
                temperature=0.0
            )
            raw = completion.choices[0].message.content
            # نتوقع أن يعيد النموذج JSON؛ نحاول تحميله
            try:
                parsed = json.loads(raw)
                ranking = parsed.get("ranking") or parsed.get("results") or parsed
            except Exception:
                # لو لم يعد JSON واضحًا، نحتفظ بالنسخة النصية كـ details
                details = raw
        except Exception as e:
            # أي خطأ في استدعاء OpenAI -> fallback للتحليل المحلي
            ranking = local_weighted_ranking(level, sec_type, subjects, annual_general)
            details = f"OpenAI call failed: {str(e)}"
    else:
        ranking = local_weighted_ranking(level, sec_type, subjects, annual_general)

    response = {
        "level": level,
        "sec_type": sec_type,
        "annual_general": annual_general,
        "subjects": subjects,
        "ranking": ranking,
        "message": "أتمنى لك التوفيق والنجاح",
        "details": details
    }
    return jsonify(response)


# Static files (إن احتجت)
@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(app.static_folder, filename)
    
    
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))

    app.run(host="0.0.0.0", port=port, debug=True)

