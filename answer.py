from subprocess import PIPE, Popen
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
import sqlite3

con = sqlite3.connect("test.db", check_same_thread = False)
cur = con.cursor()
try:
    cur.execute("CREATE TABLE PINGS(time, ip1, ip2, type, id, seq, length)")
except sqlite3.OperationalError:
    print("Table is already made")


def parse_and_add_to_db(line: str):
    line = line.replace(",", "")
    time, _1, ip1, _2, ip2, _3, _4, type, _5, id, _6, seq, _7, length  = line.split()
    ip2 = ip2[:-1]
    # print(f"inserting ('{time}', '{ip1}', '{ip2}', '{type}', {id}, {seq}, {length})")
    cur.execute(f"INSERT INTO PINGS VALUES('{time}', '{ip1}', '{ip2}', '{type}', {id}, {seq}, {length})")

def tcpdump_thread():
    # proc = Popen("sudo tcpdump -l -w /dev/null -i utun3 icmp --print -f -xx".split(), stdin=PIPE, stdout=PIPE, stderr=PIPE) # if we want the packet hex
    proc = Popen("sudo tcpdump -l -w /dev/null -i YOURINTERFACE icmp --print -f".split(), stdin=PIPE, stdout=PIPE, stderr=PIPE) # start a process to moitor pings
    assert proc.stdin is not None and proc.stdout is not None and proc.stderr is not None
    proc.stdin.write("YOURPASSWORDHERE\n".encode()) # password
    proc.stdin.flush()
    print("START")
    while True:
        parse_and_add_to_db(proc.stdout.readline().decode("latin-1"))

bg_tcpdump = Thread(target=tcpdump_thread)
bg_tcpdump.daemon = True
bg_tcpdump.start()

#Server
class functionserver(BaseHTTPRequestHandler):
    def do_GET(self):
        a, b = self.path[1:].split("/")
        print(a, b)
        data = cur.execute(f"SELECT * from PINGS where {a}=='{b}'").fetchall()
        #OUTPUT
        self.send_response(200)
        self.end_headers()
        self.wfile.write((("\n".join(map(str,data))).encode()))
        self.wfile.flush()
        
    def log_message(args,*kwargs):
        return None
        
httpd = HTTPServer(("127.0.0.1", 5000), functionserver)
httpd.serve_forever()
