import plotly.graph_objects as go
import plotly.io as pio
import os

# --- Font settings (your existing code) ---
font_filename = "IPAexGothic.ttf" # フォントファイル名
font_dir_relative = "static/fonts" # プロジェクトルートからの相対的なフォントディレクトリ

# プロジェクトのルートディレクトリを基準に絶対パスを生成
# Replitでは通常、メインスクリプトがあるディレクトリがカレントワーキングディレクトリになることが多いです。
# より堅牢にするには、スクリプト自身の位置から相対パスを解決することも検討できます。
# 例: base_dir = os.path.dirname(os.path.abspath(__file__))
#     font_path = os.path.join(base_dir, font_dir_relative, font_filename)
# ここでは、元のコードのロジックに近い形で記述します。
font_path = os.path.abspath(os.path.join(font_dir_relative, font_filename))

print(f"テスト用フォントパス: {font_path}")
if not os.path.exists(font_path):
    print(f"警告: テスト用フォントファイルが見つかりません: {font_path}")
    # フォントがない場合はここで処理を中断するか、代替処理を検討
else:
    print(f"テスト用フォントファイル確認: {font_path}")

pio.kaleido.scope.default_font_family = "IPAexGothic" # フォント名を指定
pio.kaleido.scope.default_font_paths = [os.path.dirname(font_path)] # フォントファイルがあるディレクトリを指定
pio.kaleido.scope.mathjax = None
pio.kaleido.scope.plotlyjs = None
# pio.kaleido.scope.default_format = "pdf" # PNG出力時は必須ではない

# --- Create a simple figure ---
fig = go.Figure(data=[go.Scatter(x=[1, 2, 3], y=[2, 1, 3])])
fig.update_layout(
    title_text="日本語タイトルテスト１２３",
    font=dict(family="IPAexGothic", size=18) # ここもフォント名を指定
)

try:
    output_filename = "test_japanese_output.png"
    fig.write_image(output_filename, width=600, height=400, scale=2)
    print(f"'{output_filename}' を出力しました。文字化けを確認してください。")
except Exception as e:
    print(f"画像出力中にエラーが発生しました: {e}")