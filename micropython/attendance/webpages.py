from storage import load_attendance

def student_page():
    return """HTTP/1.1 200 OK

<!DOCTYPE html>
<html>
<body>
<h2>Student Attendance</h2>
<form action="/submit" method="get">
Name:<br><input name="name"><br><br>
Roll No:<br><input name="roll"><br><br>
<input type="submit" value="Submit">
</form>
</body>
</html>
"""

def admin_login_page():
    return """HTTP/1.1 200 OK

<!DOCTYPE html>
<html>
<body>
<h2>Teacher Login</h2>
<form action="/login" method="post">
Password:<br>
<input type="password" name="password"><br><br>
<input type="submit" value="Login">
</form>
</body>
</html>
"""

def admin_page():
    rows = ""
    for r in load_attendance():
        name = r.get("name", "")
        roll = r.get("roll", "")
        date = r.get("date", "N/A")
        time = r.get("time", "N/A")

        rows += "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>".format(
            name, roll, date, time
        )

    return """HTTP/1.1 200 OK

<!DOCTYPE html>
<html>
<body>
<h2>Attendance Records</h2>
<table border="1">
<tr><th>Name</th><th>Roll</th><th>Date</th><th>Time</th></tr>
{}
</table>
<form action="/clear" method="post">
<br><input type="submit" value="Clear Attendance">
</form>
</body>
</html>
""".format(rows)

