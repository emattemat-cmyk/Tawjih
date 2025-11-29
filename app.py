from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # استلام البيانات من النموذج
        moyenne = float(request.form.get("moyenne", 0))
        matieres = {
            "math": float(request.form.get("math", 0)),
            "physique": float(request.form.get("physique", 0)),
            "biologie": float(request.form.get("biologie", 0)),
            "philosophie": float(request.form.get("philosophie", 0)),
            "francais": float(request.form.get("francais", 0)),
            "anglais": float(request.form.get("anglais", 0))
        }

        # خوارزمية اختيار الشعبة
        if moyenne >= 15 and matieres["math"] >= 14:
            filiere = "Mathématiques / Sciences"
        elif moyenne >= 12 and matieres["biologie"] >= 12:
            filiere = "Sciences expérimentales"
        else:
            filiere = "Littéraire / Philosophie"

        # حساب النسبة
        total_points = sum(matieres.values())
        max_points = len(matieres) * 20
        pourcentage = round((total_points / max_points) * 100, 2)

        return render_template("result.html", filiere=filiere, pourcentage=pourcentage)

    return render_template("index.html")

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
