import socket
from storage import add_record, save_attendance
from webpages import student_page, admin_page, admin_login_page

ADMIN_PASSWORD = "teacher123"

def url_decode(s):
    s = s.replace("+", " ")
    out = ""
    i = 0
    while i < len(s):
        if s[i] == "%" and i + 2 < len(s):
            out += chr(int(s[i+1:i+3], 16))
            i += 3
        else:
            out += s[i]
            i += 1
    return out

def parse_body(req):
    try:
        body = req.split("\r\n\r\n", 1)[1]
        params = {}
        for p in body.split("&"):
            k, v = p.split("=")
            params[k] = url_decode(v)
        return params
    except:
        return {}

def start_server():
    s = socket.socket()
    s.bind(("0.0.0.0", 80))
    s.listen(5)

    while True:
        conn, _ = s.accept()
        req = conn.recv(1024).decode()
        path = req.split(" ")[1]

        if path == "/":
            conn.send(student_page())

        elif path.startswith("/submit"):
            query = path.split("?")[1]
            params = {}
            for p in query.split("&"):
                k, v = p.split("=")
                params[k] = url_decode(v)

            if add_record(params["name"], params["roll"]):
                conn.send("HTTP/1.1 200 OK\n\nAttendance submitted.")
            else:
                conn.send("HTTP/1.1 200 OK\n\nRoll already submitted.")

        elif path == "/admin":
            conn.send(admin_login_page())

        elif path == "/login":
            params = parse_body(req)
            if params.get("password") == ADMIN_PASSWORD:
                conn.send(admin_page())
            else:
                conn.send("HTTP/1.1 403 Forbidden\n\nWrong password")

        elif path == "/clear" and req.startswith("POST"):
            save_attendance([])
            conn.send("HTTP/1.1 200 OK\n\nAttendance cleared")

        else:
            conn.send("HTTP/1.1 404 Not Found\n\n")

        conn.close()
