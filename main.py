from flask import Flask, render_template, request, send_file
import matplotlib.pyplot as plt
import matplotlib
import os
import uuid
from weasyprint import HTML

matplotlib.rcParams['font.family'] = 'IPAGothic'

app = Flask(__name__)
UPLOAD_FOLDER = "static/output"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def save_chart(x, y, s, title, xlabel, ylabel, filename):
    fig, ax = plt.subplots()
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.scatter(x,
               y,
               s=s,
               alpha=0.5,
               color='mediumseagreen',
               edgecolors='black')
    fig.savefig(os.path.join(UPLOAD_FOLDER, filename), bbox_inches="tight")
    plt.close(fig)


@app.route("/", methods=["GET", "POST"])
def index():
    charts, input_text, pdf_title, error = [], "", "", ""

    if request.method == "POST":
        input_text = request.form.get("input_text", "")
        pdf_title = request.form.get("pdf_title", "").strip()

        lines = input_text.strip().split("\n")
        x1_list, y1_list, s1_list = [], [], []
        x2_list, y2_list, s2_list = [], [], []

        for line in lines:
            try:
                values = list(map(int, line.replace("\t", " ").split()))
                if len(values) != 12:
                    continue
                k1 = (values[6] * 10 + values[5]) / 440 * 100
                k2 = (values[9] * 20 + values[10] * 10 + values[7] +
                      values[11]) / 1280 * 100
                k3 = (values[3] + values[1]) / 80 * 100
                b1 = values[6] / 40 * 100
                b2 = (values[9] * 10 + values[10]) / 440 * 100
                b3 = values[3] / 40 * 100
                x1_list.append(k2)
                y1_list.append(k1)
                s1_list.append(k3)
                x2_list.append(b2)
                y2_list.append(b1)
                s2_list.append(b3)
            except:
                continue

        if not x1_list or not x2_list:
            error = "⚠️ 入力が正しくありません。"
            return render_template("index.html",
                                   charts=[],
                                   pdf_title=pdf_title,
                                   input_text=input_text,
                                   error=error)

        chart1 = f"{uuid.uuid4()}.png"
        chart2 = f"{uuid.uuid4()}.png"
        save_chart(x1_list, y1_list, s1_list, "上司タイプ分布図", "指示傾向", "信頼傾向",
                   chart1)
        save_chart(x2_list, y2_list, s2_list, "部下タイプ分布図", "主体性", "柔軟性", chart2)
        charts = [f"{UPLOAD_FOLDER}/{chart1}", f"{UPLOAD_FOLDER}/{chart2}"]

        # タイトルが未入力なら初期値
        if not pdf_title:
            pdf_title = "タイプ診断グラフ"

        with open("static/last_info.txt", "w", encoding="utf-8") as f:
            f.write(f"{charts[0]}\n{charts[1]}\n{pdf_title}")

    return render_template("index.html",
                           charts=charts,
                           pdf_title=pdf_title,
                           input_text=input_text,
                           error=error)


@app.route("/download_pdf", methods=["POST"])
def download_pdf():
    try:
        with open("static/last_info.txt", "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
        chart1, chart2 = lines[0], lines[1]
        title = lines[2] if len(lines) > 2 and lines[2].strip() else "タイプ診断グラフ"
    except Exception:
        chart1, chart2, title = "", "", "タイプ診断グラフ"

    html = render_template("pdf_template.html",
                           chart1=chart1,
                           chart2=chart2,
                           pdf_title=title)
    pdf_path = os.path.join(UPLOAD_FOLDER, "output.pdf")
    HTML(string=html, base_url=".").write_pdf(pdf_path)
    return send_file(pdf_path, as_attachment=True, download_name="診断結果.pdf")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
