from flask import Flask, render_template, url_for, request, redirect, session
from better_profanity import profanity
import json
from date import cleanDate, year, day, month, is_after_school_hours as isAfterSchool

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = True
app.secret_key = 'catbean'

# --- Helper Functions for Data Storing ---
def load(file):
    with open("./data/" + file + '.json', 'r') as f:
        return json.load(f)

def save(data, file) -> None:
    with open("./data/" + file + '.json', 'w') as f:
        json.dump(data, f, indent=4)

# --- Real-Time Chat Feed endpoint ---
@app.route("/getChatData")
def getChatData():
    return load("chat")

# --- Chatroom Interface Page ---
@app.route("/chat", methods=["GET", "POST"])
def chat():
    if "name" not in session:
        return redirect(url_for("login", error="Please log in to use the chatroom."))
        
    if request.method == "POST":
        rosterData = load("roster")
        user = session["name"]
        
        # Guardrail: Check if user is muted
        if rosterData.get(user, {}).get("is_muted", False):
            return "You are muted and cannot chat.", 403
            
        content = request.form.get("content")
        date_str = cleanDate() + " " + str(day) + " " + str(month)
        content = profanity.censor(content)
        
        chat_data = load("chat")
        chat_data.append({
            "author": user,
            "date": date_str,
            "content": content
        })
        save(chat_data, "chat")
        return "Success", 200
        
    return render_template("chat.html")

# --- Resources Directory Page ---
@app.route("/resources")
def resources():
    try:
        resources_data = load("resc")
    except:
        resources_data = []
    return render_template("resc.html", resc=resources_data)

# --- Homepage Route ---
@app.route("/")
def homepage():
    siteData = load("site")
    rosterData = load("roster")
    bullitenData = load("bulliten")
    error = request.args.get("error")
    return render_template("index.html", error=error, roster=rosterData, bulliten=bullitenData, leader=siteData['leader'])

# --- Authentication Handling (Login / Logout) ---
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    
    if request.method == "POST":
        name = request.form.get('username')
        key = request.form.get('key')
        rosterData = load("roster")
        
        if name in rosterData:
            # Guardrail: Check if user is suspended
            if rosterData[name].get("is_suspended", False):
                return render_template("login.html", error="Your account has been suspended by an administrator.")
                
            if key == rosterData[name]["password"]:
                session['name'] = name
                session['rank'] = rosterData[name]["rank"]
                session['admin'] = True if rosterData[name]["rank"] == 0 else False
                return redirect(url_for("homepage", error="Logged in!"))
            return render_template("login.html", error="That's not the right key ):<")
        else:
            return render_template("login.html", error="....you're not in coding club?")
    return "Something went wrong"

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("homepage", error="Logged Out."))

# --- Password Management ---
@app.route("/change_password", methods=["GET", "POST"])
def change_password():
    if "name" not in session:
        return redirect(url_for("login", error="Please log in first."))
        
    if request.method == "GET":
        return render_template("change_password.html")
        
    if request.method == "POST":
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")
        
        rosterData = load("roster")
        user = session["name"]
        
        if current_password != rosterData[user]["password"]:
            return render_template("change_password.html", error="Current password is incorrect.")
            
        if new_password != confirm_password:
            return render_template("change_password.html", error="New passwords do not match.")
            
        rosterData[user]["password"] = new_password
        save(rosterData, "roster")
        return redirect(url_for("homepage", error="Password changed successfully!"))

# --- Dashboard Control Panels (Admin & Curator) ---
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if "name" not in session or not session.get("admin"):
        return redirect(url_for("homepage", error="Unauthorized."))
        
    rosterData = load("roster")
    if request.method == "GET":
        return render_template("admin.html", roster=rosterData)
        
    if request.method == "POST":
        form_type = request.form.get('type')
        
        if form_type == "addUser":
            name = request.form.get('name')
            rank = int(request.form.get('rank'))
            if name:
                rosterData[name] = {"password": "catbean", "rank": rank, "is_muted": False, "is_suspended": False}
                save(rosterData, 'roster')
            return redirect(url_for("admin"))
            
        if form_type == "deleteUser":
            name = request.form.get('name')
            if name in rosterData:
                del rosterData[name]
                save(rosterData, 'roster')
            return redirect(url_for("admin"))

        if form_type == "editUser":
            old_name = request.form.get('old_name')
            new_name = request.form.get('new_name')
            new_password = request.form.get('password')
            new_rank = int(request.form.get('rank'))
            
            if old_name in rosterData:
                # Keep tracking status configurations during edits
                current_mute = rosterData[old_name].get("is_muted", False)
                current_suspension = rosterData[old_name].get("is_suspended", False)
                
                if old_name != new_name and new_name:
                    rosterData[new_name] = {"password": new_password, "rank": new_rank, "is_muted": current_mute, "is_suspended": current_suspension}
                    del rosterData[old_name]
                else:
                    rosterData[old_name] = {"password": new_password, "rank": new_rank, "is_muted": current_mute, "is_suspended": current_suspension}
                save(rosterData, 'roster')
            return redirect(url_for("admin"))
            
        # Global Mod Tool Handlers
        if form_type == "modAction":
            target_user = request.form.get("target_user")
            action = request.form.get("action")
            
            if target_user in rosterData:
                if action == "mute":
                    rosterData[target_user]["is_muted"] = True
                elif action == "unmute":
                    rosterData[target_user]["is_muted"] = False
                elif action == "suspend":
                    rosterData[target_user]["is_suspended"] = True
                elif action == "unsuspend":
                    rosterData[target_user]["is_suspended"] = False
                elif action == "ban":
                    del rosterData[target_user]  # Banning removes account data instantly
                
                save(rosterData, "roster")
            return redirect(url_for("admin"))

        if form_type == "addResc":
            url = request.form.get('url')
            title = request.form.get('title')
            rescou = load("resc")
            rescou.append({"url": url, "title": title})
            save(rescou, "resc")
            return redirect(url_for("admin"))
            
        if form_type == "bulletinAdd":
            content = request.form.get('content')
            bullitenData = load("bulliten")
            date_str = cleanDate() + " '" + str(year)[2:]
            bullitenData.insert(0, {
                "date": date_str,
                "author": session.get("name"),
                "content": content
            })
            save(bullitenData, "bulliten")
            return redirect(url_for("admin"))
            
        if form_type == "clearChat":
            save([], "chat")
            return redirect(url_for("admin"))

@app.route("/curator", methods=["GET", "POST"])
def curator():
        # Grant access if user is full admin (rank 0) or curator (rank 1)
    if session.get("rank") not in [0, 1]:
        return redirect(url_for("homepage", error="Unauthorized."))
        
    rosterData = load("roster")
    if request.method == "GET":
        return render_template("curator.html", roster=rosterData)
        
    if request.method == "POST":
        form_type = request.form.get('type')
        # ... keep curator logic here ...
        return redirect(url_for("curator"))

# --- Help Forum Thread Routing ---
@app.route("/forum", methods=['GET', 'POST'])
def forum():
    postsData = load("posts")
    if request.method == "GET":
        if "name" not in session:
            return redirect(url_for("login"))
        return render_template("forum.html", posts=postsData)
        
    if request.method == "POST":
        rosterData = load("roster")
        user = session["name"]
        
        # Guardrail: Check if user is muted on the forum
        if rosterData.get(user, {}).get("is_muted", False):
            return "You are muted and cannot post.", 403
            
        fType = request.form.get('type')
        if fType == "deletePost":
            id = request.form.get('id')
            del postsData[int(id)]
            save(postsData, "posts")
            return redirect(url_for("forum"))
            
        if fType == "newPost":
            content = request.form.get('content')
