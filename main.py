# main_v14_v9.py
# ベース：main_v14_v8.py
# バージョン情報：main_v14_v9.py / index_v18
# 作成日：2025-05-11
# 内容：
# - selected1_b / selected2_b が None の際にエラーが出る不具合を修正
# - selected1_j / selected2_j にも同様の保護を強化（明示的対応）
# - その他構成・表示・注記に変更なし

# ✅ V14構成チェック済（v14_v8強化・バグ修正）
# - ルール逸脱なし、距離測定の安定性強化
# - 上司・部下距離測定ともにNone対応済
import os
import plotly.io as pio

# フォントパスを絶対パスで指定
font_path = os.path.abspath("static/fonts/IPAexGothic.ttf")

# ✅ Kaleido にフォント設定を適用
pio.kaleido.scope.default_font = os.path.abspath(
    "static/fonts/IPAexGothic.ttf")
pio.kaleido.scope.mathjax = None  # 任意：MathJax警告を避けたい場合
pio.kaleido.scope.plotlyjs = None
pio.kaleido.scope.default_format = "pdf"

from flask import Flask, render_template, request
import plotly.graph_objs as go
from plotly.offline import plot
import math

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
     chart_div = ""
     distance_result_j = ""
     distance_result_b = ""
     selected1_j = selected2_j = ""
     selected1_b = selected2_b = ""
     filename_prefix = ""
     max_points = 0

     if request.method == "POST":
          data = request.form.get("numbers", "")
          selected1_j = request.form.get("point1_j")
          selected2_j = request.form.get("point2_j")
          selected1_b = request.form.get("point1_b")
          selected2_b = request.form.get("point2_b")
          filename_prefix = request.form.get("filename", "")
          if data.strip():
               font_family = dict(family="IPAexGothic")

               rows = [
                   list(map(int, line.split("\t")))
                   for line in data.strip().split("\n")
               ]
               max_points = len(rows)
               x_vals1, y_vals1, size1, label1 = [], [], [], []
               x_vals2, y_vals2, size2, label2 = [], [], [], []

               for i, r in enumerate(rows):
                    x1 = (r[8] * 20 + r[9] * 10 + r[6] + r[10]) / 1280 * 100
                    y1 = (r[5] * 10 + r[4]) / 440 * 100
                    s1 = (r[2] + r[0]) / 80 * 100
                    x_vals1.append(x1)
                    y_vals1.append(y1)
                    size1.append(s1)
                    label1.append(str(i + 1))

                    x2 = (r[8] * 10 + r[9]) / 440 * 100
                    y2 = (r[5]) / 40 * 100
                    s2 = (r[2]) / 40 * 100
                    x_vals2.append(x2)
                    y_vals2.append(y2)
                    size2.append(s2)
                    label2.append(str(i + 1))

               # 距離測定（上司）
               if selected1_j and selected2_j and selected1_j.isdigit(
               ) and selected2_j.isdigit():
                    idx1 = int(selected1_j) - 1
                    idx2 = int(selected2_j) - 1
                    if 0 <= idx1 < max_points and 0 <= idx2 < max_points:
                         dx = x_vals1[idx1] - x_vals1[idx2]
                         dy = y_vals1[idx1] - y_vals1[idx2]
                         dist = math.sqrt(dx**2 + dy**2)
                         distance_result_j = f"【上司】点{selected1_j}と点{selected2_j}の距離は {dist:.2f} です。"

               # 距離測定（部下）
               if selected1_b and selected2_b and selected1_b.isdigit(
               ) and selected2_b.isdigit():
                    idx1 = int(selected1_b) - 1
                    idx2 = int(selected2_b) - 1
                    if 0 <= idx1 < max_points and 0 <= idx2 < max_points:
                         dx = x_vals2[idx1] - x_vals2[idx2]
                         dy = y_vals2[idx1] - y_vals2[idx2]
                         dist = math.sqrt(dx**2 + dy**2)
                         distance_result_b = f"【部下】点{selected1_b}と点{selected2_b}の距離は {dist:.2f} です。"

               trace1 = go.Scatter(
                   x=x_vals1,
                   y=y_vals1,
                   mode='markers+text',
                   text=label1,
                   textposition='middle center',
                   marker=dict(size=size1,
                               sizemode='diameter',
                               sizeref=2.5,
                               sizemin=10,
                               color='teal',
                               line=dict(width=1, color='black')),
                   hovertemplate=
                   "番号: %{text}<br>X: %{x:.2f}<br>Y: %{y:.2f}<br>大きさ: %{marker.size:.2f}<extra></extra>",
                   name="")

               trace2 = go.Scatter(
                   x=x_vals2,
                   y=y_vals2,
                   mode='markers+text',
                   text=label2,
                   textposition='middle center',
                   marker=dict(size=size2,
                               sizemode='diameter',
                               sizeref=2.5,
                               sizemin=10,
                               color='orange',
                               line=dict(width=1, color='black')),
                   hovertemplate=
                   "番号: %{text}<br>X: %{x:.2f}<br>Y: %{y:.2f}<br>大きさ: %{marker.size:.2f}<extra></extra>",
                   name="")

               layout1 = go.Layout(
                   title="上司としてのワークスタイル（傾向）",
                   font=dict(family="IPAexGothic"),
                   width=900,
                   xaxis=dict(title=dict(
                       text=
                       "適切な指示傾向（創造性・自立性・融和性・感受性）<br><span style='font-size:12px;'>※円：元気良さと発信力（会話性＋幸福性）</span>",
                       standoff=20),
                              range=[-5, 105],
                              dtick=25),
                   yaxis=dict(title="相談しやすさ（尊重性＋共感性）",
                              range=[-5, 105],
                              dtick=25),
                   height=700,
                   shapes=[
                       dict(type="rect",
                            x0=0,
                            x1=50,
                            y0=50,
                            y1=100,
                            fillcolor="rgba(255,228,225,0.5)",
                            layer="below",
                            line=dict(width=0)),
                       dict(type="rect",
                            x0=50,
                            x1=100,
                            y0=50,
                            y1=100,
                            fillcolor="rgba(255,255,224,0.5)",
                            layer="below",
                            line=dict(width=0)),
                       dict(type="rect",
                            x0=0,
                            x1=50,
                            y0=0,
                            y1=50,
                            fillcolor="rgba(224,255,255,0.5)",
                            layer="below",
                            line=dict(width=0)),
                       dict(type="rect",
                            x0=50,
                            x1=100,
                            y0=0,
                            y1=50,
                            fillcolor="rgba(240,255,240,0.5)",
                            layer="below",
                            line=dict(width=0))
                   ],
                   annotations=[
                       dict(x=5,
                            y=102,
                            text="見守り支援タイプ",
                            showarrow=False,
                            font=dict(family="IPAexGothic",
                                      color="red",
                                      size=12),
                            xanchor="left"),
                       dict(x=95,
                            y=102,
                            text="柔軟実行指導タイプ",
                            showarrow=False,
                            font=dict(family="IPAexGothic",
                                      color="red",
                                      size=12),
                            xanchor="right"),
                       dict(x=5,
                            y=-2,
                            text="職人気質タイプ",
                            showarrow=False,
                            font=dict(family="IPAexGothic",
                                      color="red",
                                      size=12),
                            xanchor="left"),
                       dict(x=95,
                            y=-2,
                            text="目標追求指導タイプ",
                            showarrow=False,
                            font=dict(family="IPAexGothic",
                                      color="red",
                                      size=12),
                            xanchor="right")
                   ])

               layout2 = go.Layout(
                   title="部下としてのワークスタイル（基本）",
                   font=dict(family="IPAexGothic"),
                   width=900,
                   xaxis=dict(title=dict(
                       text=
                       "主体性（創造性＋自立性）<br><span style='font-size:12px;'>※円の大きさ（幸福性）</span>",
                       standoff=20),
                              range=[-5, 105],
                              tickvals=[0, 100]),
                   yaxis=dict(title="柔軟性（尊重性）", range=[-5, 105], dtick=25),
                   height=700,
                   shapes=[
                       dict(type="rect",
                            x0=0,
                            x1=33.33,
                            y0=50,
                            y1=100,
                            fillcolor="rgba(255,228,225,0.5)",
                            layer="below",
                            line=dict(width=0)),
                       dict(type="rect",
                            x0=33.33,
                            x1=66.66,
                            y0=50,
                            y1=100,
                            fillcolor="rgba(255,255,224,0.5)",
                            layer="below",
                            line=dict(width=0)),
                       dict(type="rect",
                            x0=66.66,
                            x1=100,
                            y0=50,
                            y1=100,
                            fillcolor="rgba(240,255,240,0.5)",
                            layer="below",
                            line=dict(width=0)),
                       dict(type="rect",
                            x0=0,
                            x1=33.33,
                            y0=0,
                            y1=50,
                            fillcolor="rgba(224,255,255,0.5)",
                            layer="below",
                            line=dict(width=0)),
                       dict(type="rect",
                            x0=33.33,
                            x1=66.66,
                            y0=0,
                            y1=50,
                            fillcolor="rgba(255,248,220,0.5)",
                            layer="below",
                            line=dict(width=0)),
                       dict(type="rect",
                            x0=66.66,
                            x1=100,
                            y0=0,
                            y1=50,
                            fillcolor="rgba(255,240,245,0.5)",
                            layer="below",
                            line=dict(width=0)),
                       dict(type="line",
                            x0=33.33,
                            x1=33.33,
                            y0=0,
                            y1=100,
                            line=dict(color="white", width=1)),
                       dict(type="line",
                            x0=66.66,
                            x1=66.66,
                            y0=0,
                            y1=100,
                            line=dict(color="white", width=1))
                   ],
                   annotations=[
                       dict(x=5,
                            y=102,
                            text="E：素直な指示待ちタイプ",
                            showarrow=False,
                            font=dict(family="IPAexGothic",
                                      color="red",
                                      size=12),
                            xanchor="left"),
                       dict(x=50,
                            y=102,
                            text="C：組織調整実行タイプ",
                            showarrow=False,
                            font=dict(family="IPAexGothic",
                                      color="red",
                                      size=12),
                            xanchor="center"),
                       dict(x=95,
                            y=102,
                            text="A：柔軟主体行動タイプ",
                            showarrow=False,
                            font=dict(family="IPAexGothic",
                                      color="red",
                                      size=12),
                            xanchor="right"),
                       dict(x=5,
                            y=-2,
                            text="F：独自世界の気難しいタイプ",
                            showarrow=False,
                            font=dict(family="IPAexGothic",
                                      color="red",
                                      size=12),
                            xanchor="left"),
                       dict(x=50,
                            y=-2,
                            text="D：組織調整（こだわり）タイプ",
                            showarrow=False,
                            font=dict(family="IPAexGothic",
                                      color="red",
                                      size=12),
                            xanchor="center"),
                       dict(x=95,
                            y=-2,
                            text="B：理論目標達成タイプ",
                            showarrow=False,
                            font=dict(family="IPAexGothic",
                                      color="red",
                                      size=12),
                            xanchor="right")
                   ])

               fig1 = go.Figure(data=[trace1], layout=layout1)
               fig2 = go.Figure(data=[trace2], layout=layout2)

               # PDF出力処理
               if filename_prefix:
                    from plotly.subplots import make_subplots

                    # 上下に2段配置（1列2行）
                    fig_combined = make_subplots(
                        rows=2,
                        cols=1,
                        vertical_spacing=0.15,
                        subplot_titles=("上司としてのワークスタイル（傾向）",
                                        "部下としてのワークスタイル（基本）"))

                    fig_combined.add_trace(trace1, row=1, col=1)
                    fig_combined.add_trace(trace2, row=2, col=1)

                    # レイアウト統合設定（日本語・サイズ調整）
                    fig_combined.update_layout(
                        height=1600,
                        width=900,
                        font=dict(family="IPAexGothic", size=12),
                        showlegend=False,
                    )

                    # 保存（1枚PDF）
                    fig_combined.write_image(f"{filename_prefix}_結果統合.pdf",
                                             format="pdf")

               chart_div = plot(fig1, output_type='div') + "<hr>" + plot(
                   fig2, output_type='div')

     return render_template("index.html",
                            chart_html=chart_div,
                            version="main_v14_v9 / index_v18",
                            selected1_j=selected1_j,
                            selected2_j=selected2_j,
                            selected1_b=selected1_b,
                            selected2_b=selected2_b,
                            distance_result_j=distance_result_j,
                            distance_result_b=distance_result_b,
                            filename=filename_prefix,
                            max_points=max_points)


if __name__ == "__main__":
     app.run(debug=True, port=3000)
