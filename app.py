from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
import os
from moviepy.editor import VideoFileClip

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ACCEPTED_FOLDER'] = 'static/uploads/accepted'
app.config['ALLOWED_EXTENSIONS'] = {'mp4', 'avi', 'mov'}
app.config['MAX_VIDEOS'] = 20


login_manager = LoginManager()
login_manager.init_app(app)

# Модератор
class User(UserMixin):
    def __init__(self, username):
        self.username = username

    def get_id(self):
        return self.username 

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# Проверка расширения файла
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Главная страница для пользователей
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_' + filename)
        file.save(temp_path)

        # Обрезка и сжатие видео
        clip = VideoFileClip(temp_path)
        clip = clip.subclip(0, min(15, clip.duration))  # Обрезка до 15 секунд

        # # Сжатие видео с сохранением пропорций
        # target_height = 480  # Задайте желаемую высоту
        # clip = clip.resize(height=target_height) # Изменение размера с сохранением пропорций

        # clip = clip.rotate(90)
        # Сохранение сжатого видео в новый файл
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        clip.write_videofile(output_path, codec='libx264', bitrate='1000k', fps=24)  # Укажите 


        # Удаление временного файла
        os.remove(temp_path)

        flash('File uploaded and compressed successfully')
        return redirect(url_for('index'))
    

# Страница модератора
@app.route('/moderator')
def moderator():
    if current_user.is_authenticated:
        videos = [video for video in os.listdir(app.config['UPLOAD_FOLDER']) if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], video))]
        return render_template('moderator.html', videos=videos)
    else:
        flash('You need to log in to access this page.')
        return render_template('login.html')

# Модерация видео
@app.route('/moderate/<action>/<filename>', methods=['POST'])
@login_required
def moderate_video(action, filename):
    video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    if action == 'accept':
        # Перемещение видео в основную папку
        accepted_path = os.path.join(app.config['ACCEPTED_FOLDER'], filename)
        os.rename(video_path, accepted_path)

        # Проверка на количество видео
        if len(os.listdir(app.config['ACCEPTED_FOLDER'])) > app.config['MAX_VIDEOS']:
            # Удаление самого старого видео
            oldest_video = min(os.listdir(app.config['ACCEPTED_FOLDER']), key=os.path.getctime)
            os.remove(os.path.join(app.config['ACCEPTED_FOLDER'], oldest_video))

        flash('Video accepted and added to the playlist.')
    elif action == 'decline':
        # Удаление видео
        if os.path.isfile(video_path):
            os.remove(video_path)
            flash('Video declined and removed.')
        else:
            flash('Error: The specified video does not exist or is not a file.')

    # Обновление списка видео после модерации
    return redirect(url_for('moderator'))  # Перенаправление на страницу модератора

# Страница воспроизведения видео
@app.route('/player')
def player():
    videos = os.listdir(os.path.join(app.config['ACCEPTED_FOLDER']))
    return render_template('player.html', videos=videos)

# Простой логин и пароль для модератора
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin'  # Замените на более безопасный пароль

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        user = User(username)
        login_user(user)
        return redirect(url_for('moderator'))
    else:
        flash('Invalid credentials')
        return redirect(url_for('index'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Запуск приложения
if __name__ == '__main__':
    app.run(debug=True)
