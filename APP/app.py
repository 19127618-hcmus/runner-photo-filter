import os
import sys, math
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from werkzeug.utils import secure_filename
import face_recognition
import multiprocessing
import numpy as np
sys.path.insert(1, 'core')
import handleData
import mongodb
import main

#config
app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
client = mongodb.connect_to_client()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_image_filenames(folder_path):
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif']  # Các phần mở rộng phổ biến của tập tin hình ảnh
    
    image_filenames = []
    for filename in os.listdir(folder_path):
        if any(filename.lower().endswith(ext) for ext in image_extensions):
            image_filenames.append(filename)
    
    return image_filenames

#route
@app.route('/')
def home():
    race_name = 'testMAP'
    collection = mongodb.connect_to_collection(race_name, client)
    documents = mongodb.get_all_documents(collection)  
    
    image_paths = [doc['picture'] for doc in documents]
    filter = handleData.filterDuplicatedPath(image_paths)
    return render_template('index.html', race_name = race_name, image_paths=filter)

@app.route('/load_images', methods=['POST'])
def load_images():
    race_name = request.form.get('race_name')
    page = int(request.form.get('page'))
    per_page = 24  # Số lượng hình ảnh trên mỗi trang

    collection = mongodb.connect_to_collection(race_name, client)
    documents = mongodb.get_all_documents(collection)

    image_paths = [doc['picture'] for doc in documents]
    filter = handleData.filterDuplicatedPath(image_paths)

    start_index = (page - 1) * per_page
    end_index = start_index + per_page

    images_for_page = filter[start_index:end_index]
    total_pages = math.ceil(len(filter) / per_page)

    return jsonify({'images': images_for_page, 'totalPages': total_pages})

@app.route('/submit', methods=['POST'])
def submit():
    pictures_by_bib = []
    pictures_by_face = []

    pictures_by_bib = []
    unique_pictures_by_face = []

    bib = "-1"
    input_face_encode = "-1"

    if 'selected_image' not in request.form and 'bib' not in request.form and 'race_name' not in request.form:
        return redirect(url_for('home'))

    bib = request.form.get('bib')
    race_name = request.form.get('race_name')
    face_path = '' 
    face_path = request.form.get('selected_image')

    option = request.form.get('search_method')

    print('/n/n ', request.form)
    if race_name == '':
        return redirect(url_for('home'))
    if face_path == '' and bib == '':
        return redirect(url_for('home'))
    
    #connect collection
    collection = mongodb.connect_to_collection(race_name, client)
    new_collection = mongodb.connect_to_collection(f'optimized_{race_name}', client)

    # Xử lý việc nhập bib
    if len(bib) > 0:
        bib_documents = handleData.findSimilarId(race_name, client, bib, 'bib')
        list_pictures = handleData.id2path(collection, bib_documents)
        pictures_by_bib = handleData.filterDuplicatedPath(list_pictures)
    
    # Xử lý việc nhập hình ảnh
    if 'selected_image' in request.form and len(face_path) > 0:
        input_face = face_recognition.load_image_file(face_path)
        input_face_encode = face_recognition.face_encodings(input_face)[0]
        face_documents = handleData.findSimilarFace(race_name, client, input_face_encode, 'face')
        list_pictures = handleData.id2path(collection, face_documents)
        pictures_by_face = handleData.filterDuplicatedPath(list_pictures)
        # unique_list = handleData.filterDuplicatedPath(pictures_by_bib + pictures_by_face)

        print(option)
    if option == 'bib':
        print(pictures_by_bib)
        return render_template('result.html', outputPicture=pictures_by_bib)
    elif option == 'face':
        return render_template('result.html', outputPicture=pictures_by_face)
    elif option == 'both':
        unique_or_list = handleData.findOrSimalar(collection, race_name, client, bib, input_face_encode)
        return render_template('result.html', outputPicture=unique_or_list)
    elif option == 'and': 
        unique_and_list = handleData.filterDuplicatedPath(set(pictures_by_bib).intersection(pictures_by_face))
        return render_template('result.html', outputPicture=unique_and_list)
    else:
        return redirect(url_for('home'))

@app.route('/upload_image', methods=['POST'])
def upload_image():
    image_file = request.files['image']
    if image_file and allowed_file(image_file.filename):
        filename = secure_filename(image_file.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp', filename)
        image_file.save(image_path)

        faces = main.selectFaceInput(image_path)
        return jsonify({'faces': faces})

    return jsonify({'error': 'Invalid image file'})

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        race_name = request.form.get('race_name')
        images = request.files.getlist('images[]')
        race_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'race', race_name)

        if not os.path.exists(race_folder):
            os.makedirs(race_folder)

        for image in images:
            if image and allowed_file(image.filename):
                filename = secure_filename(image.filename)
                image_path = os.path.join(race_folder, filename)
                image.save(image_path)

        return redirect(url_for('upload_preview', race_name=race_name))

    return render_template('upload.html')


@app.route('/upload_preview/<race_name>')

def upload_preview(race_name):
    collection = mongodb.connect_to_collection(race_name, client)
    folder_path = os.path.join('static', 'uploads', 'race', race_name).replace("\\", "/")
    
    image_filenames = get_image_filenames(folder_path)
    documents = mongodb.get_all_documents(collection)

    formatted_documents = [doc['picture'].split('/')[-1] for doc in documents]

    new_images = [os.path.join('uploads/race', race_name, img.split('/')[-1]).replace("\\", "/") for img in image_filenames if img not in formatted_documents]

    return render_template('upload_preview.html', race_name=race_name, images=new_images)

@app.route('/upload_processing/<race_name>')
def upload_processing(race_name):
    collection = mongodb.connect_to_collection(race_name, client)
    folder_path = os.path.join('static', 'uploads', 'race', race_name).replace("\\", "/")
    
    image_filenames = get_image_filenames(folder_path)
    documents = mongodb.get_all_documents(collection)

    formatted_documents = [doc['picture'].split('/')[-1] for doc in documents]

    new_images = [img for img in image_filenames if img not in formatted_documents]
    new_images_count = len(new_images)

    # Chạy quá trình upload và mã hóa hình ảnh trong một tiến trình riêng biệt
    process = multiprocessing.Process(target=main.uploadAndEncodeImages, args=(folder_path, new_images, race_name))
    process.start()

    # Trả về kết quả cho client và tiếp tục xử lý
    return jsonify({'race_name': race_name, 'new_images': new_images, 'new_images_count': new_images_count})

if __name__ == '__main__':
    app.run(debug=True)
    mongodb.close_mongodb_connection(client)
    main.deleteTempFile(os.path.join(app.config['UPLOAD_FOLDER'], 'temp'))
