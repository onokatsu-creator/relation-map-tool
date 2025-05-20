import os
import plotly.io as pio

# ▼ Kaleidoプロセスのシャットダウン処理を一旦コメントアウトまたは削除してみる ▼
# try:
#     pio.kaleido.scope.shutdown_kaleido_process()
# except Exception as e:
#     print(f"Kaleido shutdown error (this is often normal on first run): {e}")
print(f"--- Skipping initial Kaleido shutdown for this test ---")
# ▲ Kaleidoプロセスのシャットダウン処理 ▲

# --- フォント設定の修正箇所 ---
# 1. デフォルトのフォントファミリーを指定
font_family_to_use = "IPAexGothic"  # スペースなしに戻す
pio.kaleido.scope.default_font_family = font_family_to_use
print(
    f"--- Setting Kaleido default_font_family to: '{font_family_to_use}' ---")

# 2. default_font_paths に static/fonts ディレクトリへの絶対パスを指定する
#    スクリプトの場所を基準に絶対パスを生成
script_dir = os.path.dirname(os.path.abspath(__file__))
static_font_dir = os.path.join(script_dir, "static", "fonts")
static_font_file_path = os.path.join(static_font_dir, "IPAexGothic.ttf")

print(f"--- Checking for local font file at: '{static_font_file_path}' ---")
if os.path.exists(static_font_file_path):
    pio.kaleido.scope.default_font_paths = [static_font_dir]
    print(
        f"--- Setting Kaleido default_font_paths to: ['{static_font_dir}'] ---"
    )
else:
    print(
        f"--- !!! WARNING: Local font file NOT found at '{static_font_file_path}'. PNG font may be garbled. Attempting to rely on system fonts. ---"
    )
    pio.kaleido.scope.default_font_paths = []  # フォールバックとしてシステムフォントに期待

# --- ここまでフォント設定の修正箇所 ---

pio.kaleido.scope.mathjax = None
pio.kaleido.scope.plotlyjs = None
pio.kaleido.scope.default_format = "png"  # ★変更の可能性: デフォルトをpngにしてみる (write_imageで指定するので影響は少ないはず)

from flask import Flask, render_template, request
from flask import send_file
import plotly.graph_objs as go
from plotly.offline import plot
import math
import traceback  # エラーの詳細表示のために追加

app = Flask(__name__)


# ここに追加
@app.route("/download/<filename>")
def download_file(filename):
    # outputディレクトリがなければ作成
    if not os.path.exists("output"):
        os.makedirs("output")
    return send_file(f"output/{filename}", as_attachment=True)


# 📍 def index(): の前に追加
def calculate_distance(x_vals, y_vals, idx1, idx2):
    dx = x_vals[idx1] - x_vals[idx2]
    dy = y_vals[idx1] - y_vals[idx2]
    return math.sqrt(dx**2 + dy**2)


@app.route("/", methods=["GET", "POST"])
def index():
    chart_html_j_content = ""
    chart_html_b_content = ""
    distance_result_j = ""
    distance_result_b = ""
    selected1_j = selected2_j = ""
    selected1_b = selected2_b = ""
    filename_prefix = ""
    max_points = 0

    highlight_point1_j = highlight_point2_j = highlight_point3_j = ""
    highlight_point1_b = highlight_point2_b = highlight_point3_b = ""

    visible_points_j_selected = []
    visible_points_b_selected = []

    names_list = []  # names_listを初期化

    if request.method == "POST":
        data = request.form.get("numbers", "")
        selected1_j = request.form.get("point1_j", "")
        selected2_j = request.form.get("point2_j", "")
        selected1_b = request.form.get("point1_b", "")
        selected2_b = request.form.get("point2_b", "")
        filename_prefix_from_form = request.form.get("filename", "")
        filename_prefix = filename_prefix_from_form
        highlight_point1_j = request.form.get("highlight_point1_j", "")
        highlight_point2_j = request.form.get("highlight_point2_j", "")
        highlight_point3_j = request.form.get("highlight_point3_j", "")
        highlight_point1_b = request.form.get("highlight_point1_b", "")
        highlight_point2_b = request.form.get("highlight_point2_b", "")
        highlight_point3_b = request.form.get("highlight_point3_b", "")
        visible_points_j_selected = request.form.getlist("visible_points_j")
        visible_points_b_selected = request.form.getlist("visible_points_b")

        if data.strip():
            parsed_rows = []
            names_list_temp = []
            input_lines = data.strip().split("\n")
            for line_idx, line in enumerate(input_lines):
                parts = [part.strip() for part in line.strip().split("\t")]
                if len(parts) >= 14:
                    name = parts[0]
                    numerical_values_str = parts[2:14]
                    if len(numerical_values_str) == 12:
                        try:
                            numerical_values = [
                                int(val.strip())
                                for val in numerical_values_str
                            ]
                            parsed_rows.append(numerical_values)
                            names_list_temp.append(
                                name if name else f"NoName{line_idx+1}")
                        except ValueError as ve:
                            print(
                                f"  Warning: ValueError during int conversion: {ve}. Original parts for numbers: {numerical_values_str}. Skipping line: '{line}'"
                            )
                            continue
                    else:
                        print(
                            f"  Warning: Incorrect number of numerical values (expected 12, got {len(numerical_values_str)}). Skipping line: '{line}'"
                        )
                else:
                    print(
                        f"  Warning: Insufficient columns (expected at least 14, got {len(parts)}). Skipping line: '{line}'"
                    )

            rows = parsed_rows
            names_list = names_list_temp
            original_max_points = len(rows)
            max_points = original_max_points

            if original_max_points == 0:
                print(
                    "--- No data parsed, skipping graph generation for Plotly ---"
                )
            else:
                plot_x_vals1, plot_y_vals1, plot_size1, plot_label1_filtered = [], [], [], []
                plot_x_vals2, plot_y_vals2, plot_size2, plot_label2_filtered = [], [], [], []
                visible_original_indices_j = []
                visible_original_indices_b = []

                if not visible_points_j_selected and original_max_points > 0:
                    temp_visible_j = [
                        str(i + 1) for i in range(original_max_points)
                    ]
                else:
                    temp_visible_j = visible_points_j_selected

                for i, r in enumerate(rows):
                    point_num_str = str(i + 1)
                    current_name = names_list[i] if i < len(
                        names_list) else f"Name{i+1}"
                    if point_num_str in temp_visible_j:
                        x1 = (r[8] * 20 + r[9] * 10 + r[6] +
                              r[10]) / 1280 * 100
                        y1 = (r[5] * 10 + r[4]) / 440 * 100
                        s1 = (r[2] + r[0]) / 80 * 100
                        plot_x_vals1.append(x1)
                        plot_y_vals1.append(y1)
                        plot_size1.append(s1)
                        plot_label1_filtered.append(current_name)
                        visible_original_indices_j.append(i)

                if not visible_points_b_selected and original_max_points > 0:
                    temp_visible_b = [
                        str(i + 1) for i in range(original_max_points)
                    ]
                else:
                    temp_visible_b = visible_points_b_selected

                for i, r in enumerate(rows):
                    point_num_str = str(i + 1)
                    current_name = names_list[i] if i < len(
                        names_list) else f"Name{i+1}"
                    if point_num_str in temp_visible_b:
                        x2 = (r[8] * 10 + r[9]) / 440 * 100
                        y2 = (r[5]) / 40 * 100
                        s2 = (r[2]) / 40 * 100
                        plot_x_vals2.append(x2)
                        plot_y_vals2.append(y2)
                        plot_size2.append(s2)
                        plot_label2_filtered.append(current_name)
                        visible_original_indices_b.append(i)

                x_vals1_all, y_vals1_all = [], []
                x_vals2_all, y_vals2_all = [], []
                for r_val in rows:
                    x_vals1_all.append(
                        (r_val[8] * 20 + r_val[9] * 10 + r_val[6] + r_val[10])
                        / 1280 * 100)
                    y_vals1_all.append((r_val[5] * 10 + r_val[4]) / 440 * 100)
                    x_vals2_all.append((r_val[8] * 10 + r_val[9]) / 440 * 100)
                    y_vals2_all.append((r_val[5]) / 40 * 100)

                if selected1_j and selected2_j and selected1_j.isdigit(
                ) and selected2_j.isdigit():
                    idx1 = int(selected1_j) - 1
                    idx2 = int(selected2_j) - 1
                    if 0 <= idx1 < original_max_points and 0 <= idx2 < original_max_points:
                        dist = calculate_distance(x_vals1_all, y_vals1_all,
                                                  idx1, idx2)
                        name1_j = names_list[idx1] if idx1 < len(
                            names_list) else selected1_j
                        name2_j = names_list[idx2] if idx2 < len(
                            names_list) else selected2_j
                        distance_result_j = f"【上司】点{selected1_j}({name1_j})と点{selected2_j}({name2_j})の距離は {dist:.2f} です。"

                if selected1_b and selected2_b and selected1_b.isdigit(
                ) and selected2_b.isdigit():
                    idx1_b_dist = int(selected1_b) - 1
                    idx2_b_dist = int(selected2_b) - 1
                    if 0 <= idx1_b_dist < original_max_points and 0 <= idx2_b_dist < original_max_points:
                        dist = calculate_distance(x_vals2_all, y_vals2_all,
                                                  idx1_b_dist, idx2_b_dist)
                        name1_b = names_list[idx1_b_dist] if idx1_b_dist < len(
                            names_list) else selected1_b
                        name2_b = names_list[idx2_b_dist] if idx2_b_dist < len(
                            names_list) else selected2_b
                        distance_result_b = f"【部下】点{selected1_b}({name1_b})と点{selected2_b}({name2_b})の距離は {dist:.2f} です。"

                line_colors1_plot = []
                line_widths1_plot = []
                marker_colors1_plot = []
                h_idx1_j = int(
                    highlight_point1_j
                ) - 1 if highlight_point1_j and highlight_point1_j.isdigit(
                ) else -1
                h_idx2_j = int(
                    highlight_point2_j
                ) - 1 if highlight_point2_j and highlight_point2_j.isdigit(
                ) else -1
                h_idx3_j = int(
                    highlight_point3_j
                ) - 1 if highlight_point3_j and highlight_point3_j.isdigit(
                ) else -1
                for original_idx in visible_original_indices_j:
                    is_selected_for_dist_j1 = selected1_j and selected1_j.isdigit(
                    ) and (int(selected1_j) - 1) == original_idx
                    is_selected_for_dist_j2 = selected2_j and selected2_j.isdigit(
                    ) and (int(selected2_j) - 1) == original_idx
                    if is_selected_for_dist_j1:
                        line_colors1_plot.append("blue")
                        line_widths1_plot.append(3)
                    elif is_selected_for_dist_j2:
                        line_colors1_plot.append("red")
                        line_widths1_plot.append(3)
                    else:
                        line_colors1_plot.append("black")
                        line_widths1_plot.append(1)

                    if original_idx == h_idx1_j:
                        marker_colors1_plot.append("red")
                    elif original_idx == h_idx2_j:
                        marker_colors1_plot.append("blue")
                    elif original_idx == h_idx3_j:
                        marker_colors1_plot.append("yellow")
                    else:
                        marker_colors1_plot.append("teal")

                line_colors2_plot = []
                line_widths2_plot = []
                marker_colors2_plot = []
                h_idx1_b = int(
                    highlight_point1_b
                ) - 1 if highlight_point1_b and highlight_point1_b.isdigit(
                ) else -1
                h_idx2_b = int(
                    highlight_point2_b
                ) - 1 if highlight_point2_b and highlight_point2_b.isdigit(
                ) else -1
                h_idx3_b = int(
                    highlight_point3_b
                ) - 1 if highlight_point3_b and highlight_point3_b.isdigit(
                ) else -1
                for original_idx in visible_original_indices_b:
                    is_selected_for_dist_b1 = selected1_b and selected1_b.isdigit(
                    ) and (int(selected1_b) - 1) == original_idx
                    is_selected_for_dist_b2 = selected2_b and selected2_b.isdigit(
                    ) and (int(selected2_b) - 1) == original_idx
                    if is_selected_for_dist_b1:
                        line_colors2_plot.append("blue")
                        line_widths2_plot.append(3)
                    elif is_selected_for_dist_b2:
                        line_colors2_plot.append("red")
                        line_widths2_plot.append(3)
                    else:
                        line_colors2_plot.append("black")
                        line_widths2_plot.append(1)

                    if original_idx == h_idx1_b:
                        marker_colors2_plot.append("red")
                    elif original_idx == h_idx2_b:
                        marker_colors2_plot.append("blue")
                    elif original_idx == h_idx3_b:
                        marker_colors2_plot.append("yellow")
                    else:
                        marker_colors2_plot.append("orange")

                font_settings = dict(family=font_family_to_use, size=12)

                trace1 = go.Scatter(
                    x=plot_x_vals1,
                    y=plot_y_vals1,
                    mode='markers+text',
                    text=plot_label1_filtered,
                    textfont=dict(family=font_family_to_use, size=10),
                    textposition='middle center',
                    marker=dict(size=plot_size1,
                                sizemode='diameter',
                                sizeref=2.5,
                                sizemin=10,
                                color=marker_colors1_plot,
                                line=dict(color=line_colors1_plot,
                                          width=line_widths1_plot)),
                    hovertemplate=
                    "名前: %{text}<br>X: %{x:.2f}<br>Y: %{y:.2f}<br>大きさ: %{marker.size:.2f}<extra></extra>",
                    name="")
                trace2 = go.Scatter(
                    x=plot_x_vals2,
                    y=plot_y_vals2,
                    mode='markers+text',
                    text=plot_label2_filtered,
                    textfont=dict(family=font_family_to_use, size=10),
                    textposition='middle center',
                    marker=dict(size=plot_size2,
                                sizemode='diameter',
                                sizeref=2.5,
                                sizemin=10,
                                color=marker_colors2_plot,
                                line=dict(color=line_colors2_plot,
                                          width=line_widths2_plot)),
                    hovertemplate=
                    "名前: %{text}<br>X: %{x:.2f}<br>Y: %{y:.2f}<br>大きさ: %{marker.size:.2f}<extra></extra>",
                    name="")

                layout1 = go.Layout(
                    title="上司としてのワークスタイル（傾向）",
                    font=font_settings,
                    width=900,
                    height=900,
                    margin=dict(b=120),
                    dragmode=False,
                    xaxis=dict(title=dict(
                        text=
                        "適切な指示傾向（創造性・自立性・融和性・感受性）<br><span style='font-size:12px;'>※円：元気良さと発信力（会話性＋幸福性）</span>",
                        standoff=20),
                               range=[-5, 105],
                               dtick=25,
                               constrain="domain",
                               fixedrange=True),
                    yaxis=dict(title="相談しやすさ（尊重性＋共感性）",
                               range=[-5, 105],
                               dtick=25,
                               scaleanchor="x",
                               scaleratio=1,
                               constrain="domain",
                               fixedrange=True),
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
                             font=dict(color="red", size=12),
                             xanchor="left"),
                        dict(x=95,
                             y=102,
                             text="柔軟実行指導タイプ",
                             showarrow=False,
                             font=dict(color="red", size=12),
                             xanchor="right"),
                        dict(x=5,
                             y=-2,
                             text="職人気質タイプ",
                             showarrow=False,
                             font=dict(color="red", size=12),
                             xanchor="left"),
                        dict(x=95,
                             y=-2,
                             text="目標追求指導タイプ",
                             showarrow=False,
                             font=dict(color="red", size=12),
                             xanchor="right")
                    ])
                layout2 = go.Layout(
                    title="部下としてのワークスタイル（基本）",
                    font=font_settings,
                    width=900,
                    height=900,
                    margin=dict(b=120),
                    dragmode=False,
                    xaxis=dict(title=dict(
                        text=
                        "主体性（創造性＋自立性）<br><span style='font-size:12px;'>※円の大きさ（幸福性）</span>",
                        standoff=20),
                               range=[-5, 105],
                               tickvals=[0, 100],
                               constrain="domain",
                               fixedrange=True),
                    yaxis=dict(title="柔軟性（尊重性）",
                               range=[-5, 105],
                               dtick=25,
                               scaleanchor="x",
                               scaleratio=1,
                               constrain="domain",
                               fixedrange=True),
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
                             font=dict(color="red", size=12),
                             xanchor="left"),
                        dict(x=50,
                             y=102,
                             text="C：組織調整実行タイプ",
                             showarrow=False,
                             font=dict(color="red", size=12),
                             xanchor="center"),
                        dict(x=95,
                             y=102,
                             text="A：柔軟主体行動タイプ",
                             showarrow=False,
                             font=dict(color="red", size=12),
                             xanchor="right"),
                        dict(x=5,
                             y=-2,
                             text="F：独自世界の気難しいタイプ",
                             showarrow=False,
                             font=dict(color="red", size=12),
                             xanchor="left"),
                        dict(x=50,
                             y=-2,
                             text="D：組織調整（こだわり）タイプ",
                             showarrow=False,
                             font=dict(color="red", size=12),
                             xanchor="center"),
                        dict(x=95,
                             y=-2,
                             text="B：理論目標達成タイプ",
                             showarrow=False,
                             font=dict(color="red", size=12),
                             xanchor="right")
                    ])

                fig1 = go.Figure(data=[trace1], layout=layout1)
                fig2 = go.Figure(data=[trace2], layout=layout2)

                chart_html_j_content = plot(fig1, output_type='div')
                chart_html_b_content = plot(fig2, output_type='div')

                output_dir = "output"
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)

                if filename_prefix_from_form.strip():
                    output_filename_j = f"{filename_prefix_from_form.strip()}_上司.png"
                    output_filename_b = f"{filename_prefix_from_form.strip()}_部下.png"
                else:
                    output_filename_j = "上司.png"
                    output_filename_b = "部下.png"

                full_output_path_j = os.path.join(output_dir,
                                                  output_filename_j)
                full_output_path_b = os.path.join(output_dir,
                                                  output_filename_b)

                try:
                    print(
                        f"--- Attempting to write image for fig1: {full_output_path_j} ---"
                    )
                    # 重要なデバッグ情報: Kaleidoのスコープ設定を出力
                    print(
                        f"--- Kaleido scope before fig1.write_image: default_font_family='{pio.kaleido.scope.default_font_family}', default_font_paths={pio.kaleido.scope.default_font_paths} ---"
                    )
                    fig1.write_image(full_output_path_j,
                                     format="png",
                                     width=900,
                                     height=900,
                                     scale=2)
                    print(
                        f"--- Successfully wrote image for fig1: {full_output_path_j} ---"
                    )
                except Exception as e:
                    print(
                        f"--- Error writing image for fig1: {full_output_path_j} ---"
                    )
                    print(f"--- Error details for fig1: {e} ---")
                    traceback.print_exc()

                try:
                    print(
                        f"--- Attempting to write image for fig2: {full_output_path_b} ---"
                    )
                    # 重要なデバッグ情報: Kaleidoのスコープ設定を出力
                    print(
                        f"--- Kaleido scope before fig2.write_image: default_font_family='{pio.kaleido.scope.default_font_family}', default_font_paths={pio.kaleido.scope.default_font_paths} ---"
                    )
                    fig2.write_image(full_output_path_b,
                                     format="png",
                                     width=900,
                                     height=900,
                                     scale=2)
                    print(
                        f"--- Successfully wrote image for fig2: {full_output_path_b} ---"
                    )
                except Exception as e:
                    print(
                        f"--- Error writing image for fig2: {full_output_path_b} ---"
                    )
                    print(f"--- Error details for fig2: {e} ---")
                    traceback.print_exc()
        else:
            print(
                "--- Data is empty or whitespace, skipping graph generation ---"
            )
            names_list = []

    return render_template(
        "index.html",
        chart_html_j=chart_html_j_content,
        chart_html_b=chart_html_b_content,
        version=
        "main_v14_v10_font_fix_attempt5_final_local / index_v22",  # バージョン更新
        selected1_j=selected1_j,
        selected2_j=selected2_j,
        selected1_b=selected1_b,
        selected2_b=selected2_b,
        distance_result_j=distance_result_j,
        distance_result_b=distance_result_b,
        filename=filename_prefix,
        max_points=max_points,
        highlight_point1_j=highlight_point1_j,
        highlight_point2_j=highlight_point2_j,
        highlight_point3_j=highlight_point3_j,
        highlight_point1_b=highlight_point1_b,
        highlight_point2_b=highlight_point2_b,
        highlight_point3_b=highlight_point3_b,
        visible_points_j_selected=visible_points_j_selected,
        visible_points_b_selected=visible_points_b_selected,
        names_list=names_list)


if __name__ == "__main__":
    if not os.path.exists("output"):
        os.makedirs("output")
    app.run(host='0.0.0.0', port=3000, debug=True)
