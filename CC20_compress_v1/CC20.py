#!flask/bin/python
from flask import Flask, jsonify, render_template, request, redirect, abort
# from flask_sqlalchemy import SQLAlchemy
from firebase_admin import credentials, firestore, initialize_app
import random, math, time, queue

app = Flask(__name__)

# ----- DB Zone -----
# Initialize Firestore DB
cred = credentials.Certificate('concur-20-firebase-adminsdk-03qea-027b4ebb9b.json')
default_app = initialize_app(cred)
db = firestore.client()
todo_ref = db.collection('Members')
# ----- DB Zone -----

# ----- Function Zone -----
# Hotel API for Request and Book
def hotel_api(ratio=(0.5,0.5)):
    li_one = [1 for i in range(math.ceil(ratio[1])+1)]
    li_zero = [0 for i in range(math.ceil(ratio[0])+1)]
    li_one.extend(li_zero)
    ans = random.choice(li_one)
    
    time.sleep(random.randint(0,2))
        
    if ans is 1:
        return True
    else:
        return False

# Flight API for Request and Book
def flight_api(ratio=(0.7,0.3)):
    li_one = [1 for i in range(math.ceil(ratio[1])+1)]
    li_zero = [0 for i in range(math.ceil(ratio[0])+1)]
    li_one.extend(li_zero)
    ans = random.choice(li_one)

    time.sleep(random.randint(0,2))

    if ans is 1:
        return True
    else:
        return False


from threading import Thread

# Thread process for booking trip
def book():
    q = queue.Queue()
    th1 = Thread(target=lambda q,arg: q.put(['hotal_resp',hotel_api(arg)]),args=(q,(0.5,0.5),))
    th1.start()
    print("Thread Start: request to hotal api")
    th2 = Thread(target=lambda q,arg: q.put(['flight_resp',flight_api(arg)]),args=(q,(0.5,0.5),))
    th2.start()
    print('Thread Start: request to flight api')
    
    th1.join()
    th2.join()
    print('All Thread Join')
    result = {}
    while not q.empty():
        item = q.get()
        result.update({item[0]:item[1]})    
    print('Update:',result)
    return result

# Thread process for request api data
def api_call():
    q = queue.Queue()
    th1 = Thread(target=lambda q,arg: q.put(['hotal_resp',hotel_api(arg)]),args=(q,(0.5,0.5),))
    th1.start()
    print("Thread Start: request to hotal api")
    th2 = Thread(target=lambda q,arg: q.put(['flight_resp',flight_api(arg)]),args=(q,(0.5,0.5),))
    th2.start()
    print('Thread Start: request to flight api')
    
    th1.join()
    th2.join()
    print('All Thread Join')
    result = {}
    while not q.empty():
        item = q.get()
        result.update({item[0]:item[1]})    
    print('Update:',result)
    return result

# ----- Function Zone -----

# ----- Page Zone -----
# Index Page
@app.route("/",methods=['GET'])
def index():
    return render_template("index.html")
# Login Page
@app.route("/login",methods=['GET','POST'])
def login():
    all_ = [doc.to_dict() for doc in todo_ref.stream()]
    usn_in_db = [a['Username'] for a in all_]
    pwd_in_db = [a['Password']for a in all_]
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if(password in pwd_in_db and username in usn_in_db):
            return redirect('/afterlog')
        else:
            return abort(404)
    else:
        return render_template("login.html")

# Book Page
@app.route('/afterlog',methods=['GET'])
def afterlog():
    return render_template("afterlog.html")

# ----- Page Zone -----

# ----- Route API Zone -----
# ----- CRUD -----
@app.route('/create', methods=['POST'])
def create():
    """
        create() : Add document to Firestore collection with request body
        Ensure you pass a custom ID as part of json body in post request
        e.g. json={"Password":"00000","Username":"Gambit","_ID":0,"book_":{"flight_booked":false,"hotel_booked":false},
                "stamp":"April 9, 2020 at 12:00:00 AM UTC+7"}
    """
    try:
        id = request.json['_ID']
        todo_ref.document(id).set(request.json)
        return jsonify({"success": True}), 200
    except Exception as e:
        return f"An Error Occured: {e}"

@app.route('/list', methods=['GET'])
def read():
    """
        read() : Fetches documents from Firestore collection as JSON
        todo : Return document that matches query ID
        all_todos : Return all documents
    """
    try:
        # Check if ID was passed to URL query
        todo_id = request.args.get('id')    
        if todo_id:
            todo = todo_ref.document(todo_id).get()
            return jsonify(todo.to_dict()), 200
        else:
            all_todos = [doc.to_dict() for doc in todo_ref.stream()]
            return jsonify(all_todos), 200
    except Exception as e:
        return f"An Error Occured: {e}"

@app.route('/update', methods=['POST', 'PUT'])
def update():
    """
        update() : Update document in Firestore collection with request body
        Ensure you pass a custom ID as part of json body in post request
        e.g. json={"Password":"00000","Username":"Gambit","_ID":0,"book_":{"flight_booked":false,"hotel_booked":false},
                "stamp":"April 9, 2020 at 12:00:00 AM UTC+7"}
    """
    try:
        id = request.json['id']
        todo_ref.document(id).update(request.json)
        return jsonify({"success": True}), 200
    except Exception as e:
        return f"An Error Occured: {e}"
        
@app.route('/delete', methods=['GET', 'DELETE'])
def delete():
    """
        delete() : Delete a document from Firestore collection
    """
    try:
        # Check for ID in URL query
        todo_id = request.args.get('id')
        todo_ref.document(todo_id).delete()
        return jsonify({"success": True}), 200
    except Exception as e:
        return f"An Error Occured: {e}"
# ----- CRUD -----
# ----- Additional CRUD -----


# ----- Additional CRUD -----
@app.route('/book',methods=['GET'])
def get_book():
    result = {'hist_book':None,'hist_ask':None,'book_status':False}

    print('#--------------------------------------------------------------------------#')
    print('Call ask to api...')
    resp_chk = api_call()
    result['hist_ask'] = resp_chk
    resp_book = None
    if (resp_chk['hotal_resp'] is True) and (resp_chk['flight_resp'] is True):
        print('Ready for book!!!')
        print('Call book to api...')
        resp_book = book()
        if (resp_book['hotal_resp'] is True) and (resp_book['flight_resp'] is True):
            print('Success to book!!!')
            result['book_status'] = True

        else:
            print('Unsuccess to book!!!')

    else:
        print('Not ready for book!!!')
    
    result['hist_book'] = resp_book
    print('#--------------------------------------------------------------------------#')
    return jsonify(result)

    # return jsonify({'hist_book':resp_book,
    #                 'hist_ask':resp_chk})
# ----- Route API Zone -----

if __name__ == "__main__":
	app.run(debug=True,threaded=True)

