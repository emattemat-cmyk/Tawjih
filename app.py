
from flask import Flask, render_template, request

app = Flask(__name__)

streams = {
    "علوم تجريبية": {"math": 0.3, "science": 0.4, "physics": 0.2, "languages": 0.1},
    "رياضيات": {"math": 0.4, "science": 0.2, "physics": 0.1, "languages": 0.3},
    "تقني رياضي": {"math": 0.3, "science": 0.3, "physics": 0.3, "languages": 0.1},
    "لغات أجنبية": {"math": 0.1, "science": 0.1, "physics": 0.1, "languages": 0.7},
    "آداب وفلسفة": {"math": 0.1, "science": 0.1, "physics": 0.1, "languages": 0.7}
}

analysis_points = [
    "تفكير منطقي قوي حسب إجابات الاختبار",
    "مستوى جيد في الرياضيات والعلوم الطبيعية",
    "طريقة إجاباتك تظهر أنك تحلل قبل ما تجاوب",
    "اهتمامك بالعلوم يدل على أنك تحب التجارب والتطبيقات العملية",
    "المستوى الأدبي متوسط، لذلك شعبة آداب وفلسفة أقل توافقًا"
]

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        general_avg = float(request.form.get("avg", 0))
        math = float(request.form.get("math", 0))
        science = float(request.form.get("science", 0))
        physics = float(request.form.get("physics", 0))
        languages = float(request.form.get("languages", 0))
        
        results = []
        for stream, weights in streams.items():
            score = math*weights["math"] + science*weights["science"] + physics*weights["physics"] + languages*weights["languages"]
            score += general_avg * 2
            score = min(score, 100)
            results.append({"name": stream, "score": round(score), "percent": round(score)})
        
        results.sort(key=lambda x: x["percent"], reverse=True)
        return render_template("result.html", results=results, analysis_points=analysis_points)
    return render_template("index.html")

if __name__ == "__main__":
    import os

port = int(os.environ.get("PORT", 5000))
app.run(host="0.0.0.0", port=port, debug=True)
