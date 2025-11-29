from flask import Flask, render_template, request
app = Flask(__name__)

# ?????? ???????? ??? ????
filiere_subjects = {
    "????_???????": ["???????","??????","????_??????"],
    "???????": ["???????","??????"],
    "????_?????": ["???????","??????"],
    "????_??????": ["??????","????????","?????"],
    "????_??????": ["?????","??????","?????"]
}

def to_float(v):
    try:
        return float(v)
    except:
        return 0.0

def compute_subject_final(t1, t2, t3, annual):
    vals = [to_float(t1), to_float(t2), to_float(t3), to_float(annual)]
    if all(v==0 for v in vals):
        return 0.0
    return round(sum(vals)/4.0, 2)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    all_subjects = set()
    for subs in filiere_subjects.values():
        all_subjects.update(subs)
    finals = {}
    annuals = []
    for subj in list(all_subjects):
        key = subj
        t1 = request.form.get(f"{key}_t1", 0)
        t2 = request.form.get(f"{key}_t2", 0)
        t3 = request.form.get(f"{key}_t3", 0)
        annual = request.form.get(f"{key}_annual", 0)
        final = compute_subject_final(t1,t2,t3,annual)
        finals[key] = final
        if to_float(annual) > 0:
            annuals.append(to_float(annual))
    overall_avg = round(sum(annuals)/len(annuals),2) if annuals else 0

    results = {}
    for filiere, subs in filiere_subjects.items():
        total = 0
        count = 0
        for s in subs:
            candidates = [s, s.replace(" ","_")]
            found_val = 0
            for c in candidates:
                if c in finals:
                    found_val = finals[c]
                    break
            total += found_val
            count += 1
        if count == 0:
            percent = 0.0
        else:
            score = round(total/count,2)
            percent = round((score/20.0)*100.0,2)
            combined = round(0.7*percent + 0.3*((overall_avg/20.0)*100.0),2) if overall_avg>0 else percent
        results[filiere] = {"pourcentage": combined, "score": round((combined/100.0)*100,2)}

    sorted_results = dict(sorted(results.items(), key=lambda x: x[1]["pourcentage"], reverse=True))
    best_filiere = list(sorted_results.keys())[0] if sorted_results else "??? ????"
    best_percent = sorted_results[best_filiere]['pourcentage'] if sorted_results else 0.0
    score100 = round(best_percent,2)

    strengths = []
    for subj, val in finals.items():
        if val >= 14:
            strengths.append(f"{subj} : {val}")
    if not strengths:
        strengths.append("????? ??????? ???? ????? ?????? ???? ??????")

    return render_template("result.html",
                           best_filiere=best_filiere,
                           best_percent=best_percent,
                           score100=score100,
                           results=sorted_results,
                           strengths=strengths,
                           developer="par : taki aymen imadeddin")

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)