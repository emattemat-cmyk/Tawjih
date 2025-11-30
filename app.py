import os
from flask import Flask, render_template, request, jsonify

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
    return round(sum(nums)/len(nums), 2)

def compute_ranking(level, sec_type, subjects):
    # أوزان كل شعبة
    if level == "middle":
        weights_map = {
            "علوم تجريبية": {"العلوم_الطبيعية":0.4,"الفيزياء":0.3,"الرياضيات":0.2,"اللغة_العربية":0.05,"الفرنسية":0.05},
            "رياضيات": {"الرياضيات":0.6,"الفيزياء":0.25,"الفرنسية":0.05,"اللغة_العربية":0.1},
            "تقني رياضي": {"الرياضيات":0.45,"الفيزياء":0.35,"العلوم_الطبيعية":0.15,"الفرنسية":0.05}
        }
    else:
        if sec_type == "science":
            weights_map = {
                "علوم تجريبية":{"العلوم_الطبيعية":0.45,"الفيزياء":0.3,"الرياضيات":0.25},
                "رياضيات":{"الرياضيات":0.6,"الفيزياء":0.25,"العلوم_الطبيعية":0.15},
                "تقني رياضي":{"الرياضيات":0.5,"الفيزياء":0.3,"العلوم_الطبيعية":0.2},
                "تسيير واقتصاد":{"الرياضيات":0.35,"الفرنسية":0.2,"الانجليزية":0.25,"اللغة_العربية":0.2}
            }
        else:
            weights_map = {
                "آداب وفلسفة":{"اللغة_العربية":0.45,"الفلسفة":0.35,"الفرنسية":0.1,"الانجليزية":0.1},
                "لغات أجنبية":{"الفرنسية":0.45,"الانجليزية":0.45,"اللغة_العربية":0.1}
            }

    result = []
    for name, w in weights_map.items():
        total_w = 0
        total_score = 0
        for sub, weight in w.items():
            val = subjects.get(sub)
            if val is None:
                continue
            total_w += weight
            total_score += val*weight
        score = round((total_score/total_w)*100) if total_w>0 else None
        result.append({"name": name, "percentage": score})
    # ترتيب
    result.sort(key=lambda x: (x["percentage"] is None, -(x["percentage"] or 0)))
    return result

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze/", methods=["POST"])
def analyze():
    data = request.get_json(force=True)
    level = data.get("level")
    sec_type = data.get("sec_type")

    candidate_subjects = ["اللغة_العربية","الرياضيات","الفرنسية","الفيزياء","العلوم_الطبيعية","الانجليزية","الفلسفة"]
    subjects = {}
    for sub in candidate_subjects:
        s1 = data.get(f"{sub}_s1", 0)
        s2 = data.get(f"{sub}_s2", 0)
        s3 = data.get(f"{sub}_s3", 0)
        subjects[sub] = avg_of_semesters([s1,s2,s3])

    ranking = compute_ranking(level, sec_type, subjects)
    return jsonify({"ranking": ranking, "message":"أتمنى لك التوفيق والنجاح"})

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))

    app.run(host="0.0.0.0", port=port, debug=True)
