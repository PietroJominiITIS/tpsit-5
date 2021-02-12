import socket
import re

PORT = 5000
REQUEST_TEMPLATE = f''' \
POST /login/submit HTTP/1.0
Host: 127.0.0.1:{PORT}
Content-Type: application/x-www-form-urlencoded
Content-Length: %d

%s
'''


def build_request(username, password):
    body = f'username={username}&password={password}'
    return REQUEST_TEMPLATE % (len(body), body, )


def make_request(username, password):
    request = build_request(username, password)

    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect(('127.0.0.1', PORT))
    conn.send(request.encode())

    response = ''
    chunk = conn.recv(1024).decode()
    while (chunk):
        response += chunk
        chunk = conn.recv(1024).decode()

    return response


def parse_response(response):
    regex = r"Location: http:\/\/127.0.0.1:5000\/(.+)\r"
    matches = re.findall(regex, response, re.MULTILINE)
    return matches[0] if len(matches) > 0 else False


def check_response(response):
    to = parse_response(response)
    return to and to == 'dashboard'


with open('passwords.txt') as passwords:
    for line in passwords.readlines():
        username, password = line.strip().split(' ')
        response = make_request(username, password)
        if check_response(response):
            print(f'OK username={username} password={password}')
