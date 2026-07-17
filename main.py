import requests
import datetime
import os
from google import genai

# 1. 前日の日付を取得する
yesterday = (datetime.date.today() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')

def fetch_academic_papers():
    # 検索キーワード（Semantic Scholarは英語論文がメインのため、英語での指定が最もヒットします）
    query = '"Organizational Behavior" OR "Person-Organization Fit" OR "Person-Organization Congruence"'
    url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={query}&limit=10&fields=title,abstract,year,publicationDate"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        papers = data.get('data', [])
    except Exception as e:
        print(f"Error fetching papers: {e}")
        return ""
    
    formatted_text = ""
    for paper in papers:
        pub_date = paper.get('publicationDate')
        # 前日以降に発表された論文があれば蓄積
        if pub_date and pub_date >= yesterday:
            formatted_text += f"Title: {paper['title']}\nAbstract: {paper.get('abstract', 'No abstract available')}\n\n"
            
    # 【補正ロジック】もし前日ぴったりの新着論文が1件もない日でもサイトが空っぽにならないよう、
    # キーワードにマッチする直近の注目論文トップ5件を代わりに要約対象にします
    if not formatted_text and papers:
        for paper in papers[:5]:
            formatted_text += f"Title: {paper['title']}\nAbstract: {paper.get('abstract', 'No abstract available')}\n\n"
            
    return formatted_text

def summarize_with_ai(raw_data):
    if not raw_data:
        return "本日の条件に合う新規論文・ニュースの取得データはありませんでした。"

    # GitHub Actionsの環境変数から安全にAPIキーを読み込む
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "エラー: GEMINI_API_KEY が設定されていません。"

    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    あなたは組織行動論・経営学の専門家です。
    以下の論文データから、「組織行動論、組織関係論、組織適合（P-Oフィット）」に関する重要なトピックを厳選し、
    実務やサービス開発に活かせる視点を含めて、毎朝のニュースレター形式で日本語で綺麗に要約してください。
    新しく応用できそうなサービスやツールのアイデア、あるいは既存のHRTechへの影響などがあれば、それも考察に含めてください。
    
    【データ】
    {raw_data}
    """
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )
    return response.text

# 実行フロー
raw_papers = fetch_academic_papers()
morning_summary = summarize_with_ai(raw_papers)

# --- ★結果をHTMLファイル（index.html）として自動保存する処理 ---
# これがあることで、GitHub Pagesを通じて自分専用のWebサイトとして閲覧できるようになります
html_content = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>毎朝の組織行動論・論文要約</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-900 text-slate-100 min-h-screen p-4 sm:p-8 font-sans">
    <div class="max-w-3xl mx-auto bg-slate-950 border border-slate-800 rounded-3xl p-6 sm:p-10 shadow-2xl mt-6">
        <span class="text-[10px] font-bold text-indigo-400 bg-indigo-500/10 border border-indigo-500/20 px-3 py-1 rounded-full uppercase tracking-wider">Daily Report</span>
        <h1 class="text-2xl sm:text-3xl font-bold mt-4 tracking-tight">毎朝の組織行動論・論文要約</h1>
        <p class="text-xs text-slate-500 mt-1">更新日時: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (JST)</p>
        <hr class="my-6 border-slate-800">
        <div class="whitespace-pre-wrap leading-relaxed text-sm text-slate-300 space-y-4">
{morning_summary}
        </div>
    </div>
</body>
</html>
"""

# ルート階層に index.html を書き出し
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("index.html の生成に成功しました。")
