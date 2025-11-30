import os
from flask import Flask, request, jsonify, render_template
from statistics import mean

app = Flask(__name__, template_folder="templates", static_folder="static")

def safe_float(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0

def avg_of_semesters(values):
    nums = [safe_float(v) for v in values if safe_float(v) is not None]
    if not nums:
        return 0.0
    return round(mean(nums), 2)

def get_weights(level, sec_type):
    if level == "متوسط":
        return {
            "علوم تجريبية": {"العلوم الطبيعية":0.4,"الفيزياء":0.3,"الرياضيات":0.2,"اللغة العربية":0.05,"الفرنسية":0.05},
            "رياضيات": {"الرياضيات":0.6,"الفيزياء":0.25,"الفرنسية":0.05,"اللغة العربية":0.1},
            "تقني رياضي": {"الرياضيات":0.45,"الفيزياء":0.35,"العلوم الطبيعية":0.15,"الفرنسية":0.05}
        }
    elif level=="ثانوي":
        if sec_type=="science":
            return {
                "علوم تجريبية": {"العلوم الطبيعية":0.45,"الفيزياء":0.3,"الرياضيات":0.15},
                "رياضيات": {"الرياضيات":0.6,"الفيزياء":0.25},
                "تقني رياضي": {"الرياضيات":0.5,"الفيزياء":0.3,"العلوم الطبيعية":0.15},
                "تسيير واقتصاد": {"الرياضيات":0.35}
            }
        else:
            return {
                "آداب وفلسفة": {"اللغة العربية":0.45,"الفلسفة":0.35,"الفرنسية":0.1,"الانجليزية":0.1},
                "لغات أجنبية": {"الفرنسية":0.45,"الانجليزية":0.45,"اللغة العربية":0.1}
            }
    else:
        return {}

def compute_scores(subjects, weights_map):
    results=[]
    for name, weights in weights_map.items():
        total_w=sum(weights.values())
        score=0.0
        for sub, w in weights.items():
            val=subjects.get(sub,0.0)
            score += val*w
        percent=round((score/total_w)*100,2) if total_w>0 else 0.0
        results.append({"name":name,"match_percent":percent})
    results_sorted=sorted(results, key=lambda x: x["match_percent"], reverse=True)
    return results_sorted

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze/", methods=["POST"])
def analyze():
    data=request.get_json(force=True)
    level=data.get("level","")
    sec_type=data.get("sec_type","")

    subjects={}
    for key in data:
        if key.endswith("_s1") or key.endswith("_s2") or key.endswith("_s3"):
            sub_name=key.rsplit("_",1)[0]
            if sub_name not in subjects:
                subjects[sub_name]=[]
            subjects[sub_name].append(safe_float(data[key]))

    for sub in subjects:
        subjects[sub]=avg_of_semesters(subjects[sub])

    weights_map=get_weights(level, sec_type)
    final_ranking=compute_scores(subjects, weights_map)

    response={"final_ranking":final_ranking}
    return jsonify(response)
    
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))

    app.run(host="0.0.0.0", port=port, debug=True)





