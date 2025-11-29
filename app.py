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
    return round(mean(nums), 2)

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
    return round(total_score / total_w, 2)

def local_weighted_ranking(level, sec_type, subjects):
    if level == "middle":
        weights_map = {
            "علوم تجريبية": {"العلوم_الطبيعية":0.4,"الفيزياء":0.3,"الرياضيات":0.2,"اللغة_العربية":0.05,"الفرنسية":0.05},
            "رياضيات": {"الرياضيات":0.6,"الفيزياء":0.25,"الفرنسية":0.05,"اللغة_العربية":0.1},
            "تقني رياضي": {"الرياضيات":0.45,"الفيزياء":0.35,"العلوم_الطبيعية":0.15,"الفرنسية":0.05}
        }
    else:
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

    suggestions = []
    for name, w in weights_map.items():
        sc = score_specialty_from_subjects(subjects, w)
        suggestions.append({"name": name, "score": sc})
    suggestions_sorted = sorted(suggestions, key=lambda x: (x["score"] is None, -(x["score"] or 0)))
    return suggestions_sorted

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze/", methods=["POST"])
def analyze():
    data = request.get_json(force=True, silent=True) or {}
    level = (data.get("level") or "").strip()
    sec_type = (data.get("sec_type") or "").strip()
    annual_general = safe_float(data.get("annual_general"))

    candidate_subjects = ["اللغة_العربية","الرياضيات","الفرنسية","الفيزياء","العلوم_الطبيعية","الانجليزية","الفلسفة"]
    subjects = {}
    for sub in candidate_subjects:
        s1 = data.get(f"{sub}_s1")
        s2 = data.get(f"{sub}_s2")
        s3 = data.get(f"{sub}_s3")
        subjects[sub] = avg_of_semesters([s1, s2, s3])

    client_ranking = data.get("client_ranking")
    if not client_ranking:
        client_ranking = local_weighted_ranking(level, sec_type, subjects)

    server_ranking = local_weighted_ranking(level, sec_type, subjects)

    weight_client = 0.631
    weight_server = 0.369

    def build_map(ranking_list):
        d = {}
        for item in ranking_list:
            name = item.get("name")
            sc = item.get("score")
            d[name] = sc
        return d

    client_map = build_map(client_ranking)
    server_map = build_map(server_ranking)

    all_names = set(list(client_map.keys()) + list(server_map.keys()))
    final_list = []
    for name in all_names:
        cs = client_map.get(name)
        ss = server_map.get(name)
        if cs is None and ss is None:
            final = None
        else:
            c_val = cs if cs is not None else ss
            s_val = ss if ss is not None else cs
            final = round(( (c_val or 0) * weight_client + (s_val or 0) * weight_server ), 2)
        final_list.append({"name": name, "score": final})

    final_sorted = sorted(final_list, key=lambda x: (x["score"] is None, -(x["score"] or 0)))

    response = {
        "level": level,
        "sec_type": sec_type,
        "annual_general": annual_general,
        "subjects": subjects,
        "client_ranking": client_ranking,
        "server_ranking": server_ranking,
        "final_ranking": final_sorted,
        "message": "أتمنى لك التوفيق والنجاح"
    }
    return jsonify(response)
    
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))

    app.run(host="0.0.0.0", port=port, debug=True)


