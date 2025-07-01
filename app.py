from flask import Flask, render_template, request
import pandas as pd
from pathlib import Path

DATA_FILE = "planilha_adubacao_milho_silagem.xlsx"

P_ADJUST = {"Muito Baixo": 50, "Baixo": 25, "Médio": 0,
            "Alto": -15, "Muito Alto": -30}
K_ADJUST = {"Muito Baixo": 60, "Baixo": 30, "Médio": 0,
            "Alto": -20, "Muito Alto": -40}
IRRIGATION_FACTOR = 1.20

app = Flask(__name__)
df = pd.read_excel(Path(DATA_FILE))
ESTADOS = sorted(df["Estado"].unique())
CLASSES_PK = list(P_ADJUST.keys())

def faixa_altitude(alt):
    if alt < 300:
        return "< 300"
    if alt < 600:
        return "300-600"
    if alt < 900:
        return "600-900"
    return "> 900"

def recomendar(estado, altitude, p_classe, k_classe, sistema):
    linha = df[(df["Estado"] == estado) &
               (df["Altitude (m)"] == faixa_altitude(altitude))]
    if linha.empty:
        raise ValueError("Estado + altitude não encontrados")
    linha = linha.iloc[0]

    n = linha["N (kg ha⁻¹)"]
    p2o5 = linha["P₂O₅ (kg ha⁻¹)"] + P_ADJUST[p_classe]
    k2o = linha["K₂O (kg ha⁻¹)"] + K_ADJUST[k_classe]

    if sistema == "Irrigado":
        n *= IRRIGATION_FACTOR
        p2o5 *= IRRIGATION_FACTOR
        k2o *= IRRIGATION_FACTOR

    return dict(
        estado=estado, altitude=altitude, sistema=sistema,
        prod_meta=linha["Produtividade-meta (t FM ha⁻¹)"],
        n=int(round(n)), p2o5=int(round(p2o5)), k2o=int(round(k2o))
    )

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            dados = recomendar(
                request.form["estado"],
                int(request.form["altitude"]),
                request.form["p_classe"],
                request.form["k_classe"],
                request.form["sistema"],
            )
            return render_template("resultado.html", **dados)
        except Exception as e:
            return render_template("index.html", estados=ESTADOS,
                                   classes=CLASSES_PK, erro=str(e))
    return render_template("index.html", estados=ESTADOS, classes=CLASSES_PK)

if __name__ == "__main__":
    app.run(debug=True)
