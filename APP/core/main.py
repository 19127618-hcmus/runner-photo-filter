import handleAttribute
from ultralytics import YOLO
import os, cv2
import easyocr
import mongodb
from multiprocessing import Pool, set_start_method
import handleData
import face_recognition
import tempfile, shutil


os.environ["KMP_DUPLICATE_LIB_OK"]="TRUE"

class Person: #person or runner is the same
    def __init__(self, bib, face, picture):
        self.bib = bib
        self.face = face
        self.picture = picture

weights_dir = os.path.join(os.path.dirname(__file__), 'weights')

model_person = YOLO(os.path.join(weights_dir, 'yolov8n.pt'))
model_bib = YOLO(os.path.join(weights_dir, 'bib.pt'))

reader = easyocr.Reader(['en'])

def handle1Image(image_path, model_person, model_bib, reader):
    detect_person_in_image = handleAttribute.detectPerson(image_path, model_person)
    list_of_person = handleAttribute.cropObj(detect_person_in_image)
    person_inf = []
    for person in list_of_person:
        bib = handleAttribute.detectBib(person, model_bib)
        bib_crop = handleAttribute.cropObj(bib)
        bib_ocr = handleAttribute.OCR(bib_crop, reader)
        if len(bib_ocr) <= 0:
            bib_ocr = handleAttribute.OCR([person], reader)
        face = handleAttribute.getFaceVector(person)
        person = Person(bib_ocr, face, image_path)
        person_inf.append(person)
    return person_inf

def process_image(image_path):
    person = handle1Image(image_path, model_person, model_bib, reader)
    return person

def handleFolderImage(folder_path):
    image_files = os.listdir(folder_path)
    save_persons = []

    with Pool() as pool:
        results = pool.map(process_image, [(folder_path + '/' + file_name) for file_name in image_files])

    save_persons.extend(results)

    return save_persons

def uploadAndEncodeImages(folder_path, list_of_file, race_name):
    collection, client = mongodb.connect_to_mongodb(race_name)
    save_persons = []
    with Pool() as pool:
        results = pool.map(process_image, [(folder_path + '/' + file_name) for file_name in list_of_file])
    save_persons.extend(results)

    for result in save_persons:
        for r in result:
            bib = r.bib
            face = r.face
            picture_path = r.picture
            if len(face) > 0:
                face = face[0].tolist()
            if len(bib) > 0 or len(face) > 0:
                mongodb.save_person_to_mongodb(collection, bib, face, picture_path)

    mongodb.close_mongodb_connection(client)
    handleData.handleData(race_name)
    print('pass')
    return True

#input face to search
def selectFaceInput(image_path):
    image = cv2.imread(image_path)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(image_rgb)
    if not face_locations:
        return []
    temp_directory = tempfile.mkdtemp(dir='static/uploads/temp')
    expanded_face_locations = []
    for (top, right, bottom, left) in face_locations:
        top -= 80
        right += 20
        bottom += 30
        left -= 20
        expanded_face_locations.append((top, right, bottom, left))
    return_images_path = []
    for i, (top, right, bottom, left) in enumerate(expanded_face_locations):
        face_image = image[top:bottom, left:right]
        face_image_path = os.path.join(temp_directory, f"face_{i}.jpg")
        print(i, (face_image).shape)
        if (face_image).shape[0] != 0 and (face_image).shape[1] != 0 and (face_image).shape[2] != 0:
            cv2.imwrite(face_image_path, face_image)
        
            return_images_path.append(face_image_path)
    return return_images_path

def deleteTempFile(folder_path):
    if os.path.exists(folder_path):
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
        for subfolder in os.listdir(folder_path):
            subfolder_path = os.path.join(folder_path, subfolder)
            if os.path.isdir(subfolder_path):
                shutil.rmtree(subfolder_path)
        return True
    else:
        return False