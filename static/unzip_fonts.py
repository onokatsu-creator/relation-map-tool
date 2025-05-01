import zipfile

zip_path = "static/NotoSansJP-Regular.zip"
extract_to = "static"

with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    zip_ref.extractall(extract_to)

print("✅ ZIP展開が完了しました！")
