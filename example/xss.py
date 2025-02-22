from flask import Flask, request, render_template_string

app = Flask(__name__)
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'False') == 'True'

@app.route('/')
def index():
    # Retrieve user input from query parameter "user_input"
    user_input = request.args.get('user_input', '')

    # WARNING: Directly including user input in HTML without sanitization is unsafe.
    # This is intentionally vulnerable to demonstrate cross-site scripting (XSS).
    template = f"""
    <!DOCTYPE html>
    <html>
      <head>
        <title>XSS Demonstration</title>
      </head>
      <body>
        <h1>XSS Vulnerability Demo</h1>
        <form method="get" action="/">
          <label for="user_input">Enter text:</label>
          <input type="text" id="user_input" name="user_input">
          <button type="submit">Submit</button>
        </form>
        <h2>Your Input:</h2>
        <div>{user_input}</div>
      </body>
    </html>
    """
    return render_template_string(template)

if __name__ == '__main__':
    app.run()
