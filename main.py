import os
import plotly.io as pio
from datetime import datetime
import pytz
# ★★★★★ ここから追加 ★★★★★
# サーバー起動日時を取得 (JST)
try:
    jst = pytz.timezone('Asia/Tokyo')
    server_startup_time = datetime.now(jst).strftime('%Y-%m-%d %H:%M:%S')
except Exception as e:
    # pytzがない場合などのフォールバック
    server_startup_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
# ★★★★★ ここまで追加 ★★★★★

# ▼ Kaleidoプロセスのシャットダウン処理はコメントアウトしたまま ▼
# try:
#     pio.kaleido.scope.shutdown_kaleido_process()
# except Exception as e:
#     print(f"Kaleido shutdown error (this is often normal on first run): {e}")
print(f"--- Skipping initial Kaleido shutdown for this test ---")
# ▲ Kaleidoプロセスのシャットダウン処理 ▲

# --- フォント設定の修正箇所 (Replit Assistantの提案を反映) ---
# 1. デフォルトのフォントファミリーを指定
font_family_to_use = "IPAexGothic"
pio.kaleido.scope.default_font_family = font_family_to_use
print(
    f"--- Setting Kaleido default_font_family to: '{font_family_to_use}' ---")

# 2. 複数の可能性のあるフォントパスをリスト化
script_dir = os.path.dirname(os.path.abspath(__file__))
possible_font_paths = [
    os.path.join(script_dir, "static", "fonts"),  # プロジェクト内のstatic/fonts
    os.path.expanduser("~/.fonts"),  # ユーザーのフォントディレクトリ (デプロイコマンドでここにコピーすることを期待)
    "/usr/share/fonts",  # 一般的なシステムフォントディレクトリ
    # 以下はNix環境でipaexfontがインストールされうる典型的なパスの例 (環境により変動の可能性あり)
    # "/nix/store", # これだけだと広すぎるので、より具体的なパスが分かれば追加
]
# 特定のNixストアパスを追加する場合は、デプロイログなどで確認できた有効なパスを使用
# 例: (ただし、このハッシュ値は環境によって変わるため、動的な特定が必要)
# nix_ipaex_path_example = "/nix/store/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx-ipaexfont-004.01/share/fonts/opentype"
# if os.path.exists(nix_ipaex_path_example):
#     possible_font_paths.append(nix_ipaex_path_example)

print(f"--- Possible font paths to check: {possible_font_paths} ---")

font_found_in_paths = False
for p_idx, font_dir_to_check in enumerate(possible_font_paths):
    # ディレクトリが存在するか、かつその直下にフォントファイルがあるかを確認
    # (fontconfigはサブディレクトリも検索するが、ここでは直接的な存在確認)
    font_file_in_dir = os.path.join(
        font_dir_to_check, "IPAexGothic.ttf")  # または "ipaexg.ttf" など実際のファイル名
    print(
        f"--- Checking path {p_idx+1}/{len(possible_font_paths)}: '{font_dir_to_check}'. Looking for '{os.path.basename(font_file_in_dir)}'. ---"
    )
    if os.path.exists(font_dir_to_check) and os.path.isdir(font_dir_to_check):
        # Kaleidoはフォントファイルそのものではなく、フォントファイルが含まれるディレクトリを期待する
        # また、fontconfigが動作していれば、ディレクトリ指定なしでもフォント名で見つかるはず
        # ここでは、Assistantの提案に沿って、フォントファイルが見つかったディレクトリを設定してみる
        if os.path.exists(font_file_in_dir):
            pio.kaleido.scope.default_font_paths = [font_dir_to_check]
            print(
                f"--- SUCCESS: IPAexGothic.ttf found in '{font_dir_to_check}'. Setting Kaleido default_font_paths to: ['{font_dir_to_check}'] ---"
            )
            font_found_in_paths = True
            break
        else:
            # サブディレクトリも簡易的に探索 (例: opentype, truetype, IPAexfontなど)
            # より堅牢にするには再帰的な探索が必要だが、まずは一般的なケースを試す
            common_subdirs = ["opentype", "truetype", "IPAexfont", "ipaexfont"]
            found_in_subdir = False
            for subdir_name in common_subdirs:
                potential_subdir = os.path.join(font_dir_to_check, subdir_name)
                font_file_in_subdir = os.path.join(potential_subdir,
                                                   "IPAexGothic.ttf")
                if os.path.exists(font_file_in_subdir):
                    pio.kaleido.scope.default_font_paths = [potential_subdir]
                    print(
                        f"--- SUCCESS: IPAexGothic.ttf found in subdirectory '{potential_subdir}'. Setting Kaleido default_font_paths to: ['{potential_subdir}'] ---"
                    )
                    font_found_in_paths = True
                    found_in_subdir = True
                    break
            if found_in_subdir:
                break
            print(
                f"--- IPAexGothic.ttf not directly found in '{font_dir_to_check}' or common subdirectories. ---"
            )
    else:
        print(
            f"--- Path '{font_dir_to_check}' does not exist or is not a directory. ---"
        )

if not font_found_in_paths:
    print(
        f"--- !!! WARNING: IPAexGothic.ttf NOT found in any of the specified possible_font_paths. Attempting to rely purely on fontconfig by setting default_font_paths to []. ---"
    )
    pio.kaleido.scope.default_font_paths = []

# --- ここまでフォント設定の修正箇所 ---

pio.kaleido.scope.mathjax = None
pio.kaleido.scope.plotlyjs = None
pio.kaleido.scope.default_format = "png"

from flask import Flask, render_template, request
from flask import send_file
import plotly.graph_objs as go
from plotly.offline import plot
import math
import traceback
from flask import redirect, url_for, session, flash  # login_requiredで使うものを中心に
from functools import wraps  # login_required デコレータ用
from PIL import Image, ImageDraw, ImageFont  # ← この行を追加

app = Flask(__name__)
# SECRET_KEYはセッション管理に必須です。
# 'FLASK_SECRET_KEY' という名前でReplitのSecretsに強力なランダム値を設定してください。
app.secret_key = os.environ.get('FLASK_SECRET_KEY')
if not app.secret_key:
    print("警告: FLASK_SECRET_KEYが環境変数に設定されていません。開発用のデフォルトキーを使用します。")
    # このフォールバックキーは開発時の一時的なものです。
    # Replitで公開する場合は必ずSecretsにユニークで複雑な値を設定してください。
    app.secret_key = "your_very_secret_dev_key_fallback_9876543210_zyxw"  # 例: 実際に使用する際はもっと複雑なものに


def login_required(f):

    @wraps(f)  # これにより、デコレートされた関数が元の関数の情報を引き継ぎます
    def decorated_function(*args, **kwargs):
        # ▼▼▼ デバッグ用プリントを追加 ▼▼▼
        print(
            f"--- [login_required decorator] Accessed for route: {request.path} ---"
        )
        app_password = os.environ.get('COMMON_PASSWORD')
        print(
            f"--- [login_required decorator] COMMON_PASSWORD from env: '{app_password}' ---"
        )

        stripped_app_password = None
        if app_password:  # app_passwordがNoneでないことを確認してからstrip()を呼ぶ
            stripped_app_password = app_password.strip()
            print(
                f"--- [login_required decorator] COMMON_PASSWORD after strip: '{stripped_app_password}' ---"
            )
        else:
            print(
                f"--- [login_required decorator] COMMON_PASSWORD is None. ---")
        # ▲▲▲ ここまでデバッグ用プリント ▲▲▲

        # COMMON_PASSWORDが設定されていて、かつ空文字列や空白のみでない場合に認証を要求
        if app_password and stripped_app_password:  # strip()後の値で判定
            # ▼▼▼ デバッグ用プリントを追加 ▼▼▼
            print(
                f"--- [login_required decorator] Password protection IS active. Checking session... ---"
            )
            # ▲▲▲ ここまでデバッグ用プリント ▲▲▲
            if not session.get('logged_in'):
                # ▼▼▼ デバッグ用プリントを追加 ▼▼▼
                print(
                    f"--- [login_required decorator] Session 'logged_in' is FALSE or not set. Redirecting to login. Target: {request.url} ---"
                )
                # ▲▲▲ ここまでデバッグ用プリント ▲▲▲
                return redirect(url_for('login', next=request.url))
            else:
                # ▼▼▼ デバッグ用プリントを追加 ▼▼▼
                print(
                    f"--- [login_required decorator] Session 'logged_in' is TRUE. Proceeding to target route. ---"
                )
                # ▲▲▲ ここまでデバッグ用プリント ▲▲▲
        else:
            # ▼▼▼ デバッグ用プリントを追加 ▼▼▼
            print(
                f"--- [login_required decorator] Password protection is NOT active (COMMON_PASSWORD is not set or empty after strip). Proceeding to target route. ---"
            )
            # ▲▲▲ ここまでデバッグ用プリント ▲▲▲
        return f(*args, **kwargs)

    return decorated_function


@app.route('/login', methods=['GET', 'POST'])
def login():
    # 環境変数 'COMMON_PASSWORD' を取得
    app_password = os.environ.get('COMMON_PASSWORD')

    # もし環境変数にパスワードが設定されていないか、空文字や空白のみの場合は、
    # ログイン不要（または既に有効）としてメインページへリダイレクト
    if not app_password or not app_password.strip():
        session['logged_in'] = True  # この場合もセッションはTrueにしておく
        return redirect(url_for('index'))

    # HTTP POSTリクエスト（フォームからデータが送信された）の場合の処理
    if request.method == 'POST':
        entered_password = request.form.get(
            'password')  # フォームから 'password' を取得

        # 入力されたパスワードが設定されたパスワードと一致するか確認
        if entered_password == app_password:
            session['logged_in'] = True  # セッションにログイン済み情報を保存
            flash('ログインしました。', 'success')  # 成功メッセージをフラッシュ

            # ログイン後にリダイレクトする先のURLを取得 (nextパラメータがあればそこへ)
            next_url = request.args.get('next') or url_for('index')
            return redirect(next_url)
        else:
            flash('パスワードが間違っています。もう一度お試しください。', 'danger')  # エラーメッセージをフラッシュ

    # HTTP GETリクエスト（単にログインページを表示する）の場合、
    # またはPOSTでパスワードが間違っていた場合は、ログインページを表示
    print(
        f"--- [Login Page] Rendering. Flashes in session: {session.get('_flashes', [])} ---"
    )
    return render_template('login.html')


@app.route('/logout')
def logout():
    # セッションから 'logged_in' の情報を削除する
    # session.pop(key, default) はキーが存在すればその値を削除して返し、なければdefaultを返す
    session.pop('logged_in', None)

    # ログアウトしたことをユーザーに通知するフラッシュメッセージ
    flash('ログアウトしました。', 'info')

    # ログアウト後はログインページにリダイレクトする
    return redirect(url_for('login'))


@app.route("/download/<filename>")
def download_file(filename):
    if not os.path.exists("output"):
        os.makedirs("output")
    return send_file(f"output/{filename}", as_attachment=True)


def calculate_distance(x_vals, y_vals, idx1, idx2):
    dx = x_vals[idx1] - x_vals[idx2]
    dy = y_vals[idx1] - y_vals[idx2]
    return math.sqrt(dx**2 + dy**2)


# ▼▼▼ この関数全体を追加します ▼▼▼
def create_list_image(items_list, output_path):
    """
    (番号, 名前) のペアのリストから、指定された仕様の画像を生成して保存する関数。
    注記：画像の高さやフォントサイズの設定により、リストに表示できるのはおよそ35件までです。
    """
    try:
        # --- 画像設定 ---
        IMG_HEIGHT = 1200
        IMG_WIDTH = 280
        FONT_SIZE = 24
        LINE_SPACING = 9
        TOP_MARGIN = 20
        SIDE_MARGIN = 20
        font_path = os.path.join(os.path.dirname(__file__), "static", "fonts",
                                 "IPAexGothic.ttf")
        BG_COLOR = "white"
        TEXT_COLOR = "black"
        LINE_COLOR = (220, 220, 220)

        # --- 計算 ---
        row_height = FONT_SIZE + LINE_SPACING
        drawable_height = IMG_HEIGHT - (TOP_MARGIN * 2)
        max_items = int(drawable_height / row_height)
        display_list = items_list[:max_items]
        if not display_list:
            print("Warning: No items to draw on the list image.")
            return

        # --- 画像生成 ---
        img = Image.new('RGB', (IMG_WIDTH, IMG_HEIGHT), BG_COLOR)
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype(font_path, FONT_SIZE)
        separator_x = IMG_WIDTH / 2
        draw.line([(separator_x, TOP_MARGIN),
                   (separator_x, IMG_HEIGHT - TOP_MARGIN)],
                  fill=LINE_COLOR,
                  width=1)

        # --- リストの描画 ---
        y_pos = TOP_MARGIN + (LINE_SPACING // 2)
        for original_number, name in display_list:
            number_text = f"{original_number}."
            display_name = (name[:5] + '...') if len(name) > 5 else name
            draw.text((separator_x - 15, y_pos),
                      number_text,
                      font=font,
                      fill=TEXT_COLOR,
                      anchor="ra")
            draw.text((separator_x + 15, y_pos),
                      display_name,
                      font=font,
                      fill=TEXT_COLOR,
                      anchor="la")
            y_pos += row_height

        # --- 画像の保存 ---
        img.save(output_path)
        print(f"Successfully created list image: {output_path}")

    except FileNotFoundError:
        print(
            f"ERROR: Font file not found at '{font_path}'. Cannot create list image."
        )
    except Exception as e:
        print(f"An error occurred during list image creation: {e}")


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    # --- 関数の先頭で変数を初期化 ---
    chart_html_j_content = ""
    chart_html_b_content = ""
    distance_result_j = ""
    distance_result_b = ""
    selected1_j, selected2_j = "", ""
    selected1_b, selected2_b = "", ""
    filename_prefix = ""
    max_points = 0
    highlight_points1_j_str, highlight_points2_j_str, highlight_points3_j_str = [], [], []
    highlight_points1_b_str, highlight_points2_b_str, highlight_points3_b_str = [], [], []
    visible_points_j_selected, visible_points_b_selected = [], []
    names_list = []

    # ★★★★★ ここから追加 ★★★★★
    # 入力件数の上限を設定 (この値を変更することで上限を調整可能)
    MAX_INPUT_LINES = 100
    # ★★★★★ ここまで追加 ★★★★★

    # --- POSTリクエスト（フォームが送信された）の場合のみ、データ処理を実行 ---
    if request.method == "POST":
        data = request.form.get("numbers", "")
        filename_prefix = request.form.get("filename", "")
        highlight_points1_j_str = request.form.getlist("highlight_point1_j")
        highlight_points2_j_str = request.form.getlist("highlight_point2_j")
        highlight_points3_j_str = request.form.getlist("highlight_point3_j")
        highlight_points1_b_str = request.form.getlist("highlight_point1_b")
        highlight_points2_b_str = request.form.getlist("highlight_point2_b")
        highlight_points3_b_str = request.form.getlist("highlight_point3_b")
        visible_points_j_selected = request.form.getlist("visible_points_j")
        visible_points_b_selected = request.form.getlist("visible_points_b")
        selected1_j = request.form.get("point1_j", "")
        selected2_j = request.form.get("point2_j", "")
        selected1_b = request.form.get("point1_b", "")
        selected2_b = request.form.get("point2_b", "")

        # --- データ入力があった場合のメイン処理 ---
        if data.strip():
            parsed_rows = []
            names_list_temp = []
            input_lines = data.strip().split("\n")
            error_found_in_loop = False

            # ★★★★★ ここから追加 ★★★★★
            # ▼▼▼ 入力件数制限 ▼▼▼
            if len(input_lines) > MAX_INPUT_LINES:
                flash(
                    f"入力データが{MAX_INPUT_LINES}件を超えています。最初の{MAX_INPUT_LINES}件のみを処理します。",
                    'warning')
                input_lines = input_lines[:MAX_INPUT_LINES]
            # ▲▲▲ ここまで追加 ▲▲▲
            # ★★★★★ ここまで追加 ★★★★★

            for line_idx, line in enumerate(input_lines):
                parts = [part.strip() for part in line.strip().split("\t")]
                line_display_name = f"「{line[:30]}...」" if len(
                    line) > 30 else f"「{line}」"

                if len(parts) >= 13:
                    name = parts[0]
                    numerical_values_str = parts[1:13]
                    if len(numerical_values_str) == 12:
                        try:
                            numerical_values = [
                                int(val.strip())
                                for val in numerical_values_str
                            ]
                            parsed_rows.append(numerical_values)
                            names_list_temp.append(
                                name if name else f"NoName{line_idx+1}")
                        except ValueError:
                            flash(
                                f"入力 {line_idx+1}行目 {line_display_name}: 数値に変換できないデータが含まれています。この行はスキップされました。",
                                'danger')
                            error_found_in_loop = True
                            print(
                                f"  Warning: ValueError on line {line_idx+1} ('{line}'). Skipping."
                            )
                            continue
                    else:
                        flash(
                            f"入力 {line_idx+1}行目 {line_display_name}: 数値データの数が12個ではありません (見つかった数: {len(numerical_values_str)})。この行はスキップされました。",
                            'danger')
                        error_found_in_loop = True
                        print(
                            f"  Warning: Incorrect number of numerical values on line {line_idx+1} ('{line}'). Skipping."
                        )
                else:
                    flash(
                        f"入力 {line_idx+1}行目 {line_display_name}: データ形式が正しくありません（タブ区切りの列が13未満です）。この行はスキップされました。",
                        'danger')
                    error_found_in_loop = True
                    print(
                        f"  Warning: Insufficient columns on line {line_idx+1} ('{line}'). Skipping."
                    )

            rows = parsed_rows
            names_list = names_list_temp
            max_points = len(rows)

            if max_points == 0:
                print(
                    "--- No valid data parsed, skipping graph generation ---")
                if not error_found_in_loop:
                    flash("有効なデータを1行も処理できませんでした。入力形式（名前<タブ>12個の数値）を再度ご確認ください。",
                          'danger')
            else:
                # --- ここからグラフ生成ロジック (元のコードのまま) ---
                highlight_indices1_j = [
                    int(p) - 1 for p in highlight_points1_j_str if p.isdigit()
                ]
                highlight_indices2_j = [
                    int(p) - 1 for p in highlight_points2_j_str if p.isdigit()
                ]
                highlight_indices3_j = [
                    int(p) - 1 for p in highlight_points3_j_str if p.isdigit()
                ]
                highlight_indices1_b = [
                    int(p) - 1 for p in highlight_points1_b_str if p.isdigit()
                ]
                highlight_indices2_b = [
                    int(p) - 1 for p in highlight_points2_b_str if p.isdigit()
                ]
                highlight_indices3_b = [
                    int(p) - 1 for p in highlight_points3_b_str if p.isdigit()
                ]

                plot_x_vals1, plot_y_vals1, plot_size1, plot_label1_filtered = [], [], [], []
                plot_x_vals2, plot_y_vals2, plot_size2, plot_label2_filtered = [], [], [], []
                visible_original_indices_j, visible_original_indices_b = [], []
                custom_data_j, custom_data_b = [], []

                if not visible_points_j_selected and max_points > 0:
                    temp_visible_j = [str(i + 1) for i in range(max_points)]
                else:
                    temp_visible_j = visible_points_j_selected
                for i, r in enumerate(rows):
                    point_num_str, current_name = str(
                        i + 1), names_list[i] if i < len(
                            names_list) else f"Name{i+1}"
                    if point_num_str in temp_visible_j:
                        x1 = (r[8] * 20 + r[9] * 10 + r[6] +
                              r[10]) / 1280 * 100
                        y1 = (r[5] * 10 + r[4]) / 440 * 100
                        s1 = (r[2] + r[0]) / 80 * 100
                        plot_x_vals1.append(x1)
                        plot_y_vals1.append(y1)
                        plot_size1.append(s1)
                        plot_label1_filtered.append(point_num_str)
                        custom_data_j.append(current_name)
                        visible_original_indices_j.append(i)

                if not visible_points_b_selected and max_points > 0:
                    temp_visible_b = [str(i + 1) for i in range(max_points)]
                else:
                    temp_visible_b = visible_points_b_selected
                for i, r in enumerate(rows):
                    point_num_str, current_name = str(
                        i + 1), names_list[i] if i < len(
                            names_list) else f"Name{i+1}"
                    if point_num_str in temp_visible_b:
                        x2 = (r[8] * 10 + r[9]) / 440 * 100
                        y2 = r[5] / 40 * 100
                        s2 = r[2] / 40 * 100
                        plot_x_vals2.append(x2)
                        plot_y_vals2.append(y2)
                        plot_size2.append(s2)
                        plot_label2_filtered.append(point_num_str)
                        custom_data_b.append(current_name)
                        visible_original_indices_b.append(i)

                x_vals1_all, y_vals1_all, x_vals2_all, y_vals2_all = [],[],[],[]
                for r_val in rows:
                    x_vals1_all.append(
                        (r_val[8] * 20 + r_val[9] * 10 + r_val[6] + r_val[10])
                        / 1280 * 100)
                    y_vals1_all.append((r_val[5] * 10 + r_val[4]) / 440 * 100)
                    x_vals2_all.append((r_val[8] * 10 + r_val[9]) / 440 * 100)
                    y_vals2_all.append(r_val[5] / 40 * 100)

                if selected1_j and selected2_j and selected1_j.isdigit(
                ) and selected2_j.isdigit():
                    idx1, idx2 = int(selected1_j) - 1, int(selected2_j) - 1
                    if 0 <= idx1 < max_points and 0 <= idx2 < max_points:
                        dist = calculate_distance(x_vals1_all, y_vals1_all,
                                                  idx1, idx2)
                        name1_j, name2_j = (
                            names_list[idx1] if idx1 < len(names_list) else
                            selected1_j), (names_list[idx2] if idx2
                                           < len(names_list) else selected2_j)
                        distance_result_j = f"【関係性】点{selected1_j}({name1_j})と点{selected2_j}({name2_j})の距離は {dist:.2f} です。"

                if selected1_b and selected2_b and selected1_b.isdigit(
                ) and selected2_b.isdigit():
                    idx1_b_dist, idx2_b_dist = int(selected1_b) - 1, int(
                        selected2_b) - 1
                    if 0 <= idx1_b_dist < max_points and 0 <= idx2_b_dist < max_points:
                        dist = calculate_distance(x_vals2_all, y_vals2_all,
                                                  idx1_b_dist, idx2_b_dist)
                        name1_b, name2_b = (
                            names_list[idx1_b_dist] if idx1_b_dist
                            < len(names_list) else selected1_b), (
                                names_list[idx2_b_dist] if idx2_b_dist
                                < len(names_list) else selected2_b)
                        distance_result_b = f"【育成】点{selected1_b}({name1_b})と点{selected2_b}({name2_b})の距離は {dist:.2f} です。"

                line_colors1_plot, line_widths1_plot, marker_colors1_plot = [], [], []
                for original_idx in visible_original_indices_j:
                    line_colors1_plot.append("black")
                    line_widths1_plot.append(1)
                    if original_idx in highlight_indices1_j:
                        marker_colors1_plot.append("red")
                    elif original_idx in highlight_indices2_j:
                        marker_colors1_plot.append("#1e90ff")  # ← 'blue' から変更
                    elif original_idx in highlight_indices3_j:
                        marker_colors1_plot.append("yellow")
                    else:
                        marker_colors1_plot.append("teal")

                line_colors2_plot, line_widths2_plot, marker_colors2_plot = [], [], []
                for original_idx in visible_original_indices_b:
                    line_colors2_plot.append("black")
                    line_widths2_plot.append(1)
                    if original_idx in highlight_indices1_b:
                        marker_colors2_plot.append("red")
                    elif original_idx in highlight_indices2_b:
                        marker_colors2_plot.append("#1e90ff")  # ← 'blue' から変更
                    elif original_idx in highlight_indices3_b:
                        marker_colors2_plot.append("yellow")
                    else:
                        marker_colors2_plot.append("teal")

                font_settings = dict(family=font_family_to_use, size=12)
                trace1 = go.Scatter(
                    x=plot_x_vals1,
                    y=plot_y_vals1,
                    mode='markers+text',
                    text=plot_label1_filtered,
                    customdata=custom_data_j,
                    textfont=dict(family=font_family_to_use, size=10),
                    textposition='middle center',
                    marker=dict(size=plot_size1,
                                sizemode='diameter',
                                sizeref=3.0,
                                sizemin=8,
                                color=marker_colors1_plot,
                                line=dict(color=line_colors1_plot,
                                          width=line_widths1_plot)),
                    # ツールチップを「番号」と「名前」のみのシンプルな表示に設定
                    hovertemplate=
                    "<b>番号: %{text}</b><br>名前: %{customdata}<extra></extra>",

                    # 参考：詳細情報（X, Y, 大きさ）も表示したい場合は、上の行をコメントアウトし、下の行のコメントを解除してください
                    # hovertemplate="<b>番号: %{text}</b><br>名前: %{customdata}<br>X: %{x:.2f}<br>Y: %{y:.2f}<br>大きさ: %{marker.size:.2f}<extra></extra>",
                    name="")
                trace2 = go.Scatter(
                    x=plot_x_vals2,
                    y=plot_y_vals2,
                    mode='markers+text',
                    text=plot_label2_filtered,
                    customdata=custom_data_b,
                    textfont=dict(family=font_family_to_use, size=10),
                    textposition='middle center',
                    marker=dict(size=plot_size2,
                                sizemode='diameter',
                                sizeref=3.0,
                                sizemin=8,
                                color=marker_colors2_plot,
                                line=dict(color=line_colors2_plot,
                                          width=line_widths2_plot)),
                    # ツールチップを「番号」と「名前」のみのシンプルな表示に設定
                    hovertemplate=
                    "<b>番号: %{text}</b><br>名前: %{customdata}<extra></extra>",

                    # 参考：詳細情報（X, Y, 大きさ）も表示したい場合は、上の行をコメントアウトし、下の行のコメントを解除してください
                    # hovertemplate="<b>番号: %{text}</b><br>名前: %{customdata}<br>X: %{x:.2f}<br>Y: %{y:.2f}<br>大きさ: %{marker.size:.2f}<extra></extra>",
                    name="")

                base_title1 = "関係性としてのワークスタイル（傾向）"
                display_title1 = f"{filename_prefix.strip()}： {base_title1}" if filename_prefix.strip(
                ) else base_title1
                layout1 = go.Layout(
                    title=display_title1,
                    font=font_settings,
                    width=810,
                    height=600,
                    margin=dict(l=30, r=30, b=120, t=50),
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
                               scaleratio=(2 / 3),
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

                base_title2 = "育成としてのワークスタイル（基本）"
                display_title2 = f"{filename_prefix.strip()}： {base_title2}" if filename_prefix.strip(
                ) else base_title2
                layout2 = go.Layout(
                    title=display_title2,
                    font=font_settings,
                    width=810,
                    height=600,
                    margin=dict(l=30, r=30, b=120, t=50),
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
                               scaleratio=(2 / 3),
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
                if not os.path.exists(output_dir): os.makedirs(output_dir)
                if filename_prefix.strip():
                    output_filename_j, output_filename_b = f"{filename_prefix.strip()}_関係性.png", f"{filename_prefix.strip()}_育成.png"
                else:
                    output_filename_j, output_filename_b = "関係性.png", "育成.png"
                full_output_path_j, full_output_path_b = os.path.join(
                    output_dir,
                    output_filename_j), os.path.join(output_dir,
                                                     output_filename_b)

                try:
                    fig1.write_image(full_output_path_j,
                                     format="png",
                                     width=900,
                                     height=600,
                                     scale=2)
                except Exception as e:
                    print(
                        f"--- Error writing image for fig1: {full_output_path_j} ---"
                    )
                    traceback.print_exc()
                try:
                    fig2.write_image(full_output_path_b,
                                     format="png",
                                     width=900,
                                     height=600,
                                     scale=2)
                except Exception as e:
                    print(
                        f"--- Error writing image for fig2: {full_output_path_b} ---"
                    )
                    traceback.print_exc()

                # ▼▼▼ このブロックをここに追加します ▼▼▼
                # --- 2種類のリスト画像の生成処理 ---

                # 1. 関係性マップのリスト画像
                list_items_j = [(i + 1, names_list[i])
                                for i in visible_original_indices_j]
                if list_items_j:

                    # ファイル名を決定
                    if filename_prefix.strip():
                        output_filename_list_j = f"{filename_prefix.strip()}_関係性_リスト.png"
                    else:
                        output_filename_list_j = "関係性_リスト.png"
                    full_output_path_list_j = os.path.join(
                        output_dir, output_filename_list_j)
                    # 画像を生成・保存
                    create_list_image(list_items_j, full_output_path_list_j)

                # 2. 育成マップのリスト画像
                list_items_b = [(i + 1, names_list[i])
                                for i in visible_original_indices_b]
                if list_items_b:
                    # ファイル名を決定
                    if filename_prefix.strip():
                        output_filename_list_b = f"{filename_prefix.strip()}_育成_リスト.png"
                    else:
                        output_filename_list_b = "育成_リスト.png"
                    full_output_path_list_b = os.path.join(
                        output_dir, output_filename_list_b)
                    # 画像を生成・保存
                    create_list_image(list_items_b, full_output_path_list_b)
                # ▲▲▲ ここまで追加 ▲▲▲

        # --- データ入力が空だった場合の処理 (if data.strip() の else) ---
        else:
            flash("データが入力されていません。", 'danger')
            print(
                "--- Data is empty or whitespace, skipping graph generation ---"
            )

    # --- テンプレートに渡す変数の準備とレンダリング ---
    return render_template("index.html",
                           chart_html_j=chart_html_j_content,
                           chart_html_b=chart_html_b_content,
                           version=f"最終起動: {server_startup_time}",
                           selected1_j=selected1_j,
                           selected2_j=selected2_j,
                           selected1_b=selected1_b,
                           selected2_b=selected2_b,
                           distance_result_j=distance_result_j,
                           distance_result_b=distance_result_b,
                           filename=filename_prefix,
                           max_points=max_points,
                           highlight_point1_j=highlight_points1_j_str,
                           highlight_point2_j=highlight_points2_j_str,
                           highlight_point3_j=highlight_points3_j_str,
                           highlight_point1_b=highlight_points1_b_str,
                           highlight_point2_b=highlight_points2_b_str,
                           highlight_point3_b=highlight_points3_b_str,
                           visible_points_j_selected=visible_points_j_selected,
                           visible_points_b_selected=visible_points_b_selected,
                           names_list=names_list)


if __name__ == "__main__":
    if not os.path.exists("output"):
        os.makedirs("output")
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port, debug=True)
