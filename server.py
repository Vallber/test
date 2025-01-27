import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import pymysql
import mimetypes

conn = None
cursor = None

try:
    conn = pymysql.connect(
        host="db",
        user="root",
        port=3306,
        password='1111',
        database="data"
    )
    cursor = conn.cursor()
    print("Successfully connected to the database.")
except Exception as e:
    print(f"Error connecting to the database: {e}")

print(f"Cursor value: {cursor}")

if cursor:
    try:
        result = cursor.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_name VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL,
            home_page VARCHAR(255),
            text TEXT NOT NULL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        conn.commit()
        print("Comments table created or already exists.")
        print(f"Result of CREATE TABLE: {result}")
    except Exception as e:
        print(f"Error creating comments table: {e}")
else:
    print("Cursor is None, cannot create comments table.")

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open('index.html', 'r', encoding='utf-8') as file:
                self.wfile.write(file.read().encode())
        elif self.path.startswith('/images/'):
            try:
                file_path = self.path[1:]
                with open(file_path, 'rb') as file:
                    self.send_response(200)
                    mime_type, _ = mimetypes.guess_type(file_path)
                    self.send_header('Content-type', mime_type)
                    self.end_headers()
                    self.wfile.write(file.read())
            except Exception as e:
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {"status": "error", "message": "Image not found"}
                self.wfile.write(json.dumps(response).encode())
        elif self.path == '/get_comments':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            try:
                cursor.execute('SELECT * FROM comments')
                comments = cursor.fetchall()
                comments_list = []
                for comment in comments:
                    comments_list.append({
                        'id': comment[0],
                        'user_name': comment[1],
                        'email': comment[2],
                        'home_page': comment[3],
                        'text': comment[4],
                        'date': comment[5].strftime('%Y-%m-%d %H:%M:%S')
                    })

                self.wfile.write(json.dumps(comments_list).encode())
            except Exception as e:
                print(f"Error fetching comments: {e}")
                response = {"status": "error", "message": "Error fetching comments"}
                self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {"status": "error", "message": "Not Found"}
            self.wfile.write(json.dumps(response).encode())

    def do_POST(self):
        global cursor 
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)

        user_name = data.get('user_name', '').strip()
        email = data.get('email', '').strip()
        home_page = data.get('home_page', '').strip()
        text = data.get('text', '').strip()

        print(f"Received data: user_name='{user_name}', email='{email}', home_page='{home_page}', text='{text}'")

        if not user_name or not email or not text:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {"status": "error", "message": "Missing required fields"}
            self.wfile.write(json.dumps(response).encode())
            print("Missing required fields")
            return

        try:
            if cursor:
                cursor.execute('''
                INSERT INTO comments (user_name, email, home_page, text)
                VALUES (%s, %s, %s, %s)
                ''', (user_name, email, home_page, text))
                conn.commit()
                response = {"status": "success", "message": "Comment added successfully!"}
                print("Comment added successfully and inserted into the database.")
            else:
                response = {"status": "error", "message": "Cursor is None, cannot insert comment."}
                print("Cursor is None, cannot insert comment.")
        except pymysql.MySQLError as e:
            print(f"MySQL Error: {e}")
            response = {"status": "error", "message": f"MySQL Error: {e}"}
        except Exception as e:
            print(f"Error inserting comment: {e}")
            response = {"status": "error", "message": f"Error inserting comment: {e}"}

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())

    def log_message(self, format, *args):
        return

def run(server_class=HTTPServer, handler_class=RequestHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting server at http://localhost:{port}')
    httpd.serve_forever()

if __name__ == '__main__':
    try:
        run()
    except KeyboardInterrupt:
        pass
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
