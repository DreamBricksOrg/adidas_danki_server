from flask import Flask, request, jsonify
from flask_mysqldb import MySQL
from datetime import datetime
from database import initialize_mysql

app = Flask(__name__)

mysql = initialize_mysql(app)


# Endpoint para adicionar um novo vídeo
@app.route('/videos', methods=['POST'])
def add_video():
    data = request.get_json()
    video_link = data['video_link']
    status = data['status']
    created_at = datetime.utcnow()

    cursor = mysql.connection.cursor()
    cursor.execute("INSERT INTO Video (created_at, video_link, status) VALUES (%s, %s, %s)",
                   (created_at, video_link, status))
    mysql.connection.commit()
    cursor.close()

    return jsonify({'message': 'Vídeo adicionado com sucesso!'}), 201


# Endpoint para listar vídeos ativos
@app.route('/videos/active', methods=['GET'])
def get_active_videos():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, video_link FROM Video WHERE status = 'ACTIVE'")
    videos = cursor.fetchall()
    cursor.close()

    return jsonify(videos), 200


# Endpoint para listar vídeos inativos
@app.route('/videos/inactive', methods=['GET'])
def get_inactive_videos():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, video_link FROM Video WHERE status = 'INACTIVE'")
    videos = cursor.fetchall()
    cursor.close()

    return jsonify(videos), 200


# Endpoint para alterar o status de um vídeo
@app.route('/videos/<int:id>', methods=['PUT'])
def update_video_status(id):
    data = request.get_json()
    new_status = data['status']

    cursor = mysql.connection.cursor()
    cursor.execute("UPDATE Video SET status = %s WHERE id = %s", (new_status, id))
    mysql.connection.commit()
    cursor.close()

    return jsonify({'message': 'Status atualizado com sucesso!'}), 200


if __name__ == '__main__':
    app.run(debug=True)
