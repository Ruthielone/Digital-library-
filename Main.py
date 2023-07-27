from flask import Flask, render_template, request, redirect, url_for
import os
import sqlite3

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DATABASE'] = 'library.db'
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'txt'}  # Supported file extensions

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def initialize_database():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def get_db():
    if not hasattr(app, 'sqlite_db'):
        app.sqlite_db = sqlite3.connect(app.config['DATABASE'])
    return app.sqlite_db

@app.teardown_appcontext
def close_db(error):
    if hasattr(app, 'sqlite_db'):
        app.sqlite_db.close()

@app.route('/')
def index():
    db = get_db()
    cur = db.execute('SELECT id, title FROM documents ORDER BY id DESC')
    documents = cur.fetchall()
    return render_template('index.html', documents=documents)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = file.filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            # Save document metadata to the database
            db = get_db()
            db.execute('INSERT INTO documents (title, filename) VALUES (?, ?)', [filename, filename])
            db.commit()

            return redirect(url_for('index'))
    return render_template('upload.html')

@app.route('/document/<int:document_id>')
def document(document_id):
    db = get_db()
    cur = db.execute('SELECT title, filename FROM documents WHERE id = ?', [document_id])
    document = cur.fetchone()
    if not document:
        return 'Document not found.'
    return render_template('document.html', document=document)

if __name__ == '__main__':
    initialize_database()
    app.run(debug=True)
