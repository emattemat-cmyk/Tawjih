import os
from flask import Flask, render_template, request, jsonify
from statistics import mean

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
    return round(mean(nums),2)

def score_specialty_from_subjects(subjects, weights):
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
    return round(total_score / total_w,2)

def local_weighted_ranking(level, sec_type, subjects):
    if level == "متوسط":
        weights_map = {
            "علوم تجريبية":{"العلوم الطبيعية":0.4,"الفيزياء":0.3,"الرياضيات":0.2,"اللغة العربية":0.05,"الفرنسية":0.05},
            "رياضيات":{"الرياضيات":0.6,"الفيزياء":0.25,"الفرنسية":0.05,"اللغة العربية":0.1},
            "تقني رياضي":{"الرياضيات":0.45,"الفيزياء":0.35,"العلوم الطبيعية":0.15,"الفرنسية":0.05}
        }
    else:
        if sec_type=="علمي":
            weights_map = {
                "علوم تجريبية":{"العلوم الطبيعية":0.45,"الفيزياء":0.3,"الرياضيات":0.25},
                "رياضيات":{"الرياضيات":0.6,"الفيزياء":0.4},
                "تقني رياضي":{"الرياضيات":0.5,"الفيزياء":0.3,"العلوم الطبيعية":0.2},
                "تسيير واقتصاد":{"الرياضيات":0.5,"الفيزياء":0.3,"العلوم الطبيعية":0.2}
            }
        else: # أدبي
            weights_map = {
                "آداب وفلسفة":{"اللغة العربية":0.45,"الفلسفة":0.35,"الفرنسية":0.1,"الإنجليزية":0.1},
                "لغات أجنبية":{"الفرنسية":0.45,"الإنجليزية":0.45,"اللغة العربية":0.1}
            }

    suggestions=[]
    for name, w in weights_map.items():
        sc = score_specialty_from_subjects(subjects, w)
        suggestions.append({"name":name,"score":sc})
    suggestions_sorted=sorted(suggestions,key=lambda x:(x["score"] is None, -(x["score"] or 0)))
    return suggestions_sorted

@app.route("/")
def index():
    return render_template("index.html", developer="taki aymen imadeddin")

@app.route("/analyze/", methods=["POST"])
def analyze():
    data = request.get_json(force=True, silent=True) or {}
    level = data.get("level") or ""
    sec_type = data.get("sec_type") or ""

    candidate_subjects=["الرياضيات","الفيزياء","العلوم الطبيعية","اللغة العربية","الفرنسية","الإنجليزية","الفلسفة"]
    subjects={}
    for sub in candidate_subjects:
        s1 = data.get(f"{sub}_s1")
        s2 = data.get(f"{sub}_s2")
        s3 = data.get(f"{sub}_s3")
        subjects[sub]=avg_of_semesters([s1,s2,s3])

    ranking = local_weighted_ranking(level, sec_type, subjects)

    # حساب نسبة الملائمة (score/max*100)
    max_score = max([r['score'] for r in ranking if r['score'] is not None] or [1])
    for r in ranking:
        if r['score'] is not None:
            r['match_percent']=round(r['score']/max_score*100,2)
        else:
            r['match_percent']=0

    # النتيجة: أفضل شعبة
    best = ranking[0] if ranking else None

    return jsonify({
        "best": best,
        "all": ranking,
        "message":"أتمنى لك التوفيق والنجاح"
    })

if __name__=="__main__":
    port=int(os.getenv("PORT",5000))
    app.run(host="0.0.0.0",port=port)
    
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))

    app.run(host="0.0.0.0", port=port, debug=True)



