import random
from flask import Flask, render_template, request
from datetime import datetime

import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

# 判斷是在 Vercel 還是本地
if os.path.exists('serviceAccountKey.json'):
    # 本地環境：讀取檔案
    cred = credentials.Certificate('serviceAccountKey.json')
else:
    # 雲端環境：從環境變數讀取 JSON 字串
    firebase_config = os.getenv('FIREBASE_CONFIG')
    cred_dict = json.loads(firebase_config)
    cred = credentials.Certificate(cred_dict)

firebase_admin.initialize_app(cred)

app = Flask(__name__)

@app.route("/")
def index():
    link = "<h1>歡迎進入郭晏丞的網站</h1>"
    link += "<a href=/mis>課程</a><hr>"
    link += "<a href=/today>現在日期時間</a><hr>"
    link += "<a href=/me>關於我</a><hr>"
    link += "<a href=/welcome?u=kyc&d=靜宜資管&c=資訊管理導論>Get傳值</a><hr>"
    link += "<a href=/account>網頁表單傳值</a><hr>"
    link += "<a href=/math>次方與根號運算</a><hr>"
    link += "<a href=/cup>線上擲筊</a><hr>"
    link += "<a href=/read3>讀取Firestore資料</a><hr>"
    link += "<a href=/search>搜尋老師</a><hr>"
    link += "<a href=/spider1>爬蟲課程</a><hr>"
    return link

@app.route("/spider1")
def spider1():
    from bs4 import BeautifulSoup
    import requests

    url = "https://www1.pu.edu.tw/~tcyang/course.html"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        Data = requests.get(url, headers=headers, timeout=10, verify=False)
        Data.encoding = "utf-8"
    except Exception as e:
        return f"錯誤: {e}"

    sp = BeautifulSoup(Data.text, "html.parser")

    courses = sp.select(".team-box")

    html = "<h2>課程列表</h2>"

    for c in courses:
        a_tag = c.find("a")
        title = c.find("h4")  # 課程名稱

        if a_tag:
            link = a_tag.get("href")

            # 補完整網址
            if link and not link.startswith("http"):
                link = "https://www1.pu.edu.tw/" + link

        else:
            link = ""

        name = title.text.strip() if title else "無名稱"

        # 👉 這裡就是你要的格式
        html += f"{link}<br>"
        html += f"{name}{link}<br>"
        html += f"{link}<br><br>"

    html += "<a href='/'>回首頁</a>"

    return html

@app.route("/search", methods=["GET", "POST"])
def search():
    db = firestore.client()
    results = []
    keyword = ""
    
    if request.method == "POST":
        keyword = request.form.get("keyword")
        collection_ref = db.collection("靜宜資管")
        docs = collection_ref.get()

        for doc in docs:
            user = doc.to_dict()
            if keyword in user["name"]:
                results.append({
                    "name": user["name"],
                    "lab": user["lab"]
                })

    return render_template("search.html", results=results, keyword=keyword)

@app.route("/read3")
def read3():
    Result = ""
    db = firestore.client()
    collection_ref = db.collection("靜宜資管")    
    docs = collection_ref.order_by("lab", direction=firestore.Query.DESCENDING).get() 
    for doc in docs:         
        Result += "文件內容：{}".format(doc.to_dict()) + "<br>"    
    return Result

@app.route("/mis")
def course():
	return "<h1>資訊管理導論</h1><a href=/>返回網頁</a>"

@app.route("/today")
def today():
	now = datetime.now()
	return render_template("today.html", datetime = str(now))


@app.route("/me")
def me():
	return render_template("mis2B.html")

@app.route("/welcome", methods=["GET"])
def welcome():
	user = request.values.get("u")
	d = request.values.get("d")
	c = request.values.get("c")
	return render_template("welcome.html", name = user, dep = d, course = c)

@app.route("/account", methods=["GET", "POST"])
def account():
    if request.method == "POST":
        user = request.form["user"]
        pwd = request.form["pwd"]
        result = "您輸入的帳號是：" + user + "; 密碼為：" + pwd 
        return result
    else:
        return render_template("account.html")

@app.route("/math", methods=["GET", "POST"])
def math():
    if request.method == "POST":
        try:
            # 對應你的 int(input())，從網頁表單取得資料並轉為整數
            x = int(request.form["x"])
            y = int(request.form["y"])
            opt = request.form["opt"]

            # 你的運算邏輯 (已修正 y=0 的 bug)
            if opt == "∧":
                result = x ** y
            elif opt == "√":
                if y == 0:
                    result = "數學不能開0次方根"
                else:
                    result = x ** (1/y)
            else:
                result = "請輸入 ∧ 或 √"
            
            # 將結果顯示在網頁上
            return f"計算結果：{result} <br><br><a href='/math'>繼續計算</a> | <a href='/'>回首頁</a>"
            
        except ValueError:
            return "輸入格式錯誤，請確保 x 和 y 都是輸入整數！<br><a href='/math'>返回重新計算</a>"
    else:
        return render_template("math.html")

@app.route('/cup', methods=["GET"])
def cup():
    # 檢查網址是否有 ?action=toss
    #action = request.args.get('action')
    action = request.values.get("action")
    result = None
    
    if action == 'toss':
        # 0 代表陽面，1 代表陰面
        x1 = random.randint(0, 1)
        x2 = random.randint(0, 1)
        
        # 判斷結果文字
        if x1 != x2:
            msg = "聖筊：表示神明允許、同意，或行事會順利。"
        elif x1 == 0:
            msg = "笑筊：表示神明一笑、不解，或者考慮中，行事狀況不明。"
        else:
            msg = "陰筊：表示神明否定、憤怒，或者不宜行事。"
            
        result = {
            "cup1": "/static/" + str(x1) + ".jpg",
            "cup2": "/static/" + str(x2) + ".jpg",
            "message": msg
        }
        
    return render_template('cup.html', result=result)

if __name__ == "__main__":
	app.run(debug=True)