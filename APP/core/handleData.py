import mongodb
import face_recognition
import numpy as np
from bson.objectid import ObjectId
tolerance_search = tolerance_db = 0.4

def levenshtein_similarity(str1, str2):
    if len(str1) < 1 or len(str2) < 1:
        return 0
    str1 = str1[0]
    str2 = str2[0]
    distance = levenshtein_distance(str1, str2)
    max_len = max(len(str1), len(str2))
    similarity = (max_len - distance) / max_len * 100
    return similarity

# Hàm tính độ tương đồng Levenshtein
def levenshtein_distance(str1, str2):
    m = len(str1)
    n = len(str2)

    # Tạo ma trận độ tương đồng với kích thước (m+1)x(n+1)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    # Khởi tạo giá trị ban đầu cho ma trận độ tương đồng
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    # Tính độ tương đồng
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if str1[i - 1] == str2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1]) + 1

    return dp[m][n]

def filter_duplicates(arr):
    filtered_arr = []
    for row in arr:
        filtered_row = list(set(row))
        filtered_arr.append(filtered_row)
    return filtered_arr

def get_all_documents2(collection):
    documents = collection.find()
    result = []
    for document in documents:
        obj = {
            "face": document["face"],
            "picture": document["picture"],
            "_id": document["_id"]
        }
        result.append(obj)
    return result

def getAllBib(collection):
    documents = mongodb.get_all_documents(collection)
    documents = list(documents)
    same_bib = []
    for i in range(0, len(documents)):
        bib = documents[i]['_id']
        temp = []
        temp.append(bib)
        for j in range(i+1, len(documents)):
            bib2 = documents[j]['_id']
            if levenshtein_similarity(documents[i]['bib'], documents[j]['bib']) > 80:
                temp.append(bib2)
        if len(temp) > 0:
            same_bib.append(temp)
    same_bib2 = filter_duplicates(same_bib)
    return same_bib2

def getAllPicture(collection, all_bib):
    # Retrieve all face_documents
    face_documents = get_all_documents2(collection)

    all_picture =[]
    for s in all_bib: #same_bib2
        for ss in s:
            find = mongodb.find_document_by_id(collection, ss)
            if isinstance(find, dict):  # Check if 'find' is a dictionary
                face = find['face']
                if len(face) > 0:
                    faces = face
                    break
        pictures =[]
        for face_document in face_documents:
            f1 = np.asarray(face_document['face'])
            f2 = np.asarray(faces)
            if f1.shape == (128,):
                temp = []
                result = face_recognition.compare_faces([f1], f2, tolerance=tolerance_db)
                if result[0]:
                    temp = face_document['_id']
            if isinstance(temp, ObjectId):
                pictures.append(temp)
        all_picture.append(pictures)
    return all_picture

def orList(all_bib, all_picture):
    new_list = []
    for i in range(len(all_bib)):
        merged_list = list(set(all_bib[i] + all_picture[i]))
        merged_list = list(map(str, merged_list))  # Chuyển các ObjectId thành chuỗi
        new_list.append(merged_list)

    return new_list

def save_id_to_mongodb(collection, b_id, f_id, o_id):
    b_id = list(map(str, b_id))
    f_id = list(map(str, f_id))
    ids = {
        'bib_id': b_id,
        'face_id': f_id,
        'or_id': o_id,
    }
    collection.insert_one(ids)

def id2path(collection, list_id):
    path = []
    for id in list_id:
        full_path = mongodb.find_document_by_id(collection, id)['picture']
        if full_path not in path:
            path.append(full_path.replace("static/", ""))
    return path

def filterDuplicatedPath(list_paths):
    unique = []
    for list_path in list_paths:
        if list_path not in unique:
            unique.append(list_path)
    return unique
#main function
def handleData(collection_name):
    collection, client = mongodb.connect_to_mongodb(collection_name)
    new_collection, client = mongodb.connect_to_mongodb(f'optimized_{collection_name}')

    all_collection = mongodb.get_all_collections(client)

    if new_collection.name in all_collection:
        new_collection.drop()
        new_collection, client = mongodb.connect_to_mongodb(f'optimized_{collection_name}')

    all_bib = getAllBib(collection)
    all_face = getAllPicture(collection, all_bib)
    or_list = orList(all_bib, all_face)

    for bib_id, face_id, or_id in zip(all_bib, all_face, or_list):
        save_id_to_mongodb(new_collection, bib_id, face_id, or_id)
    return True


def findSimilarId(collection_name, client, bib, mode):
    if mode == 'bib' or mode == 'and':
        field = 'bib_id'

    else:
        field = 'or_id'

    collection = mongodb.connect_to_collection(collection_name, client)
    new_collection = mongodb.connect_to_collection(f'optimized_{collection_name}', client)
    bib_documents = mongodb.find_similar_values(collection, 'bib', bib)

    list_ids = []
    for bib_document in bib_documents:
        print((bib_document['bib'][0]), (bib))
        if (len(bib_document['bib'][0]) == len(bib)):
            if levenshtein_similarity(bib_document['bib'][0], bib) >= 80:
                print(levenshtein_similarity(bib_document['bib'][0], bib))
                list_ids.append(bib_document['_id'])
        else:
            list_ids.append(bib_document['_id'])
    list_ids = list(map(str, list_ids))


    unique_list = []
    for id in list_ids:
        find = mongodb.find_similar_values(new_collection, field, id)
        for f in find:
            if f not in unique_list:
                unique_list.append(f)

    final_list = []
    for i in unique_list:
        for j in i[field]:
            if j not in final_list:
                final_list.append(j)

    return final_list

def findSimilarFace(collection_name, client, Face_vector, mode):
    if mode == 'face' or mode == 'and':
        field = 'face_id'
    else:
        field = 'or_id'

    collection = mongodb.connect_to_collection(collection_name, client)
    new_collection = mongodb.connect_to_collection(f'optimized_{collection_name}', client)

    documents = mongodb.get_all_documents(collection)

    list_ids = []
    for face_document in documents:
        flag = False
        saved_face_encode = np.asarray(face_document['face'])
        if saved_face_encode.shape == (128,):
            result = face_recognition.compare_faces([Face_vector], saved_face_encode, tolerance=tolerance_search)
            flag = True if result[0] else False
        else:
            flag = False
        if flag:
            list_ids.append(face_document['_id'])
    list_ids = list(map(str, list_ids))


    unique_list = []
    for id in list_ids:
        find = mongodb.find_similar_values(new_collection, field, id)
        for f in find:
            if f not in unique_list:
                unique_list.append(f)

    final_list = []
    for i in unique_list:
        for j in i[field]:
            if j not in final_list:
                final_list.append(j)

    return final_list

def findOrSimalar(collection, collection_name, client, bib, Face_vector):
    mode = 'or'
    pictures_by_bib = []
    pictures_by_face = []
    if len(bib) > 0 and bib != "-1":
        bibs = findSimilarId(collection_name, client, bib, mode)
        list_bibs = id2path(collection, bibs)
        pictures_by_bib = filterDuplicatedPath(list_bibs)

    if len(Face_vector) >= 128:
        faces = findSimilarFace(collection_name, client, Face_vector, mode)
        list_faces = id2path(collection, faces)
        pictures_by_face = filterDuplicatedPath(list_faces)

    return filterDuplicatedPath(pictures_by_bib + pictures_by_face)
