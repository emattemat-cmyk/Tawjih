from flask import Flask, render_template, request

app = Flask(__name__, template_folder="templates")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    level = request.form.get("level")
    sec_type = request.form.get("sec_type")

    # التوجيه حسب المستوى
    if level == "middle":
        suggestion = "التخصصات المقترحة: علوم تجريبية - تقني رياضي - رياضيات"
    else:
        if sec_type == "science":
            suggestion = "التوجيه المحتمل: علوم تجريبية / رياضيات / تقني رياضي / تسيير واقتصاد"
        else:
            suggestion = "التوجيه المحتمل: آداب وفلسفة / لغات أجنبية"

    return render_template("result.html", suggestion=suggestion)
    
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))

    app.run(host="0.0.0.0", port=port, debug=True)
