# from ultralytics import YOLO
import cv2, re, os, tempfile
import face_recognition

def cropObj(result):
    obj = []
    for r in result:
        for box in r.boxes:
            x1, y1, x2, y2 = (box.xyxy[0]).tolist()
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            cropped_image = r.orig_img[y1:y2, x1:x2]
            obj.append(cropped_image)
    return obj

def savefig(result, name):
    image = cv2.cvtColor(result[0].orig_img, cv2.COLOR_RGB2BGR)
    for r in result:
        text = 0
        for box in r.boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            width = int(x2 - x1)
            height = int(y2 - y1)
            cv2.rectangle(image, (int(x1), int(y1)), (int(x2), int(y2)), (255, 0, 0), 3)
            cv2.putText(image, str(text), (int(x1), int(y1)), cv2.FONT_HERSHEY_SIMPLEX, 2, (90, 255, 100), 1, cv2.LINE_AA)
            text += 1
    rgb_img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    cv2.imwrite(f'/test/{name}.jpg', rgb_img)

#handle person
def detectPerson(image_path, model):
    image = cv2.imread(image_path)
    result = model(image, classes=0)
    result[0].orig_img_path = image_path
    return result

#handle bib
def detectBib(runner, model):
    result = model(runner)
    return result

#handle ocr
def OCR(bib, reader):
    if len(bib) > 0:
        output = reader.readtext(bib[0], detail = 0)
        result_cleaned = [re.sub(r'\W+', '', string) for string in output]
        number_pattern = re.compile(r'\d{3,}|[a-zA-Z]\d{2,}')
        result_filter = [number for number in result_cleaned if number_pattern.match(number)]
        result = [number for number in result_filter if len(number) != 4 or (len(number) == 4 and not number.startswith(('201', '202', '203')))]
    else:
        result = []
    return result

#handle face
def getFaceVector(person):
    image = cv2.cvtColor(person, cv2.COLOR_RGB2BGR)
    encoding = face_recognition.face_encodings(image)
    return encoding

