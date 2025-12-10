from flask import Flask, render_template, url_for, request, redirect, session
app = Flask(__name__)
from better_profanity import profanity
import json
from date import cleanDate, year, day, month, is_after_school_hours as isAfterSchool

app.config["SESSION_PERMANENT"] = True



def load(file):
   with open("./data/" + file + '.json', 'r') as f:
       return json.load(f)

def save(data, file) -> None:
   with open("./data/" + file + '.json', 'w') as f:
       json.dump(data, f, indent=4)

@app.route("/getChatData")
def getChatData():
    return load("chat")

siteData = load("site")
rosterData = load("roster")
bullitenData = load("bulliten")
postsData: list = load('posts')

app.secret_key = 'catbean'


@app.route("/")
def homepage():
    siteData = load("site")
    rosterData = load("roster")
    bullitenData = load("bulliten")
    error = request.args.get("error")
    return render_template("index.html", error=error, roster=rosterData, bulliten=bullitenData, leader=siteData['leader'])

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("homepage", error="Logged Out."))

@app.route("/login", methods=["GET", "POST"])
def login():
    siteData = load("site")
    rosterData = load("roster")
    bullitenData = load("bulliten")
    postsData: list = load('posts')
    if request.method == "GET":
        return render_template("login.html")
    if request.method == "POST":
        name = request.form.get('username')
        key = request.form.get('key')
        if name in rosterData[0] or name in rosterData[1] or name in rosterData[2]:
            if key == app.secret_key:
                session['name'] = name
                session['admin'] = False
                session['rank'] = 2 if name in rosterData[2] else 1
                if name in rosterData[0]:
                    session['admin'] = True
                return redirect(url_for("homepage", error="logged in!"))
            return render_template("login.html", error="that's not the right key ):<")
        else:
            return render_template("login.html", error="....you're not in coding club? (you didn't put in the right name)")
    return "uhh... beau messed up the coding"

@app.route("/admin", methods=["GET", "POST"])
def admin():
    siteData = load("site")
    rosterData = load("roster")
    bullitenData = load("bulliten")
    postsData: list = load('posts')
    if request.method == "GET":
        if "name" not in session:
            return redirect(url_for("homepage", error="Unauthorized."))
        if session["admin"]:
            return render_template("admin.html", roster=rosterData)
        if session["name"] in rosterData[1]:
            return render_template("curator.html", roster=rosterData)
        return redirect(url_for("homepage", error="Unauthorized."))
    if request.method == "POST":
        if request.form.get('type') == "addUser":
            name = request.form.get('name')
            rank = request.form.get('rank')
            d = load('roster')
            d[int(rank)].append(name)
            save(d, 'roster')
            return redirect(url_for("admin"))
        if request.form.get('type') == "deleteUser":
            name = request.form.get('name')
            rank = request.form.get('rank')
            d:list = load('roster')
            i = d[int(rank)].index(name)
            del d[int(rank)][i]
            save(d, 'roster')
            return redirect(url_for("admin"))
        if request.form.get('type') == "addResc":
            url = request.form.get('url')
            title = request.form.get('title')
            rescou:list = load("resc")
            rescou.append({
                "url": url,
                "title": title
            })
            save(rescou, "resc")
            return redirect(url_for("admin"))
        if request.form.get('type') == "bulletinAdd":
            content = request.form.get('content')
            bullitenData = load("bulliten")
            date = cleanDate() + " '" + str(year)[2:]
            bullitenData.insert(0, {
                "date":date,
                "author": session.get("name"),
                "content": content
            })
            save(bullitenData, "bulliten")
            return redirect(url_for("admin"))
        if request.form.get('type') == "clearChat":
            save([], "chat")
            return redirect(url_for("admin"))

@app.route("/forum", methods=['GET', 'POST'])
def forum():
    postsData = load("posts")
    if request.method == "GET":
        postsData = load("posts")
        if "name" not in session:
            return redirect("/login")
        return render_template("forum.html", posts=postsData)
    if request.method == "POST":
        fType = request.form.get('type')
        name = session["name"]
        content = request.form.get('content')
        date = cleanDate()
        if fType == "deletePost":
            id = request.form.get('id')
            del postsData[int(id)]
            save(postsData, "posts")
            return redirect(url_for("forum"))
        if fType == "newPost":
            content = request.form.get('content')
            date = cleanDate() + " '" + str(year)[2:]
            content = profanity.censor(content)
            postsData.append({
                "author": name,
                "date": date,
                "content": content,
                "id": len(postsData),  # append to end so id matches index
                "replies": []
            })

            save(postsData, "posts")
            return redirect(url_for("forum"))
        if fType == "replyToPost":
            postId = request.form.get('postID')
            content = request.form.get('c')
            date = cleanDate()
            content = profanity.censor(content)
            d = load('posts')
            d[int(postId)]["replies"].append({
                "author": name,
                "date": date,
                "content": content
            })
            save(d, "posts")
            return redirect(url_for("forum"))

@app.route("/chat", methods=['GET', 'POST'])
def chat():
    if isAfterSchool():
        postsData = load("chat")
        if request.method == "GET":
            postsData = load("chat")
            if "name" not in session:
                return redirect("/login")
            return render_template("chat.html", posts=postsData)
        if request.method == "POST":
            fType = request.form.get('type')
            name = session["name"]
            content = request.form.get('content')
            date = cleanDate()
            if fType == "newPost":
                content = request.form.get('content')
                date = cleanDate()
                content = profanity.censor(content)
                postsData.append({
                    "author": name,
                    "date": str(month) + "/" + str(day),
                    "content": content,
                    "id": len(postsData)  # append to end so id matches index
                })
                save(postsData, "chat")
                return ""  # instead of redirect

    return "It's not after school! You can't access this page during school hours (8am-3pm)."

@app.route("/rescources")
def rescources():
    res = load("resc")
    return render_template("resc.html", resc=res)



if __name__ == '__main__':
    app.run(debug=True, port=5000, host="0.0.0.0")

