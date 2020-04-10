#!flask/bin/python
from flask import Flask, jsonify, render_template, request, redirect, abort, session
from datetime import datetime
from firebase_admin import credentials, firestore, initialize_app
import random, math, time, queue,requests, json, secrets

app = Flask(__name__)
# secrets.token_urlsafe(len('_5#y2L"F4Q8z\n\xec]/'))
app.secret_key = secrets.token_urlsafe(len('_5#y2L"F4Q8z\n\xec]/'))

# ----- DB Zone -----
# Initialize Firestore DB
cred = credentials.Certificate('concur-20-firebase-adminsdk-03qea-027b4ebb9b.json')
default_app = initialize_app(cred)
db = firestore.client()
member_ref = db.collection('Members')
flight_ref = db.collection('Flights')
hotel_ref = db.collection('Hotels')
# ----- DB Zone -----

# ----- Function Zone -----
# Hotel API for Request and Book
def hotel_request(get_data=False):
    all_hotel = [doc.to_dict() for doc in hotel_ref.stream()]
    time.sleep(random.randint(0,2))

    if get_data is True:
        return all_hotel
    else:
        flag = False
        for flight in all_hotel:
            if flight['available'] is True:
                flag = True

        return flag

# Flight API for Request and Book
def flight_request(get_data=False):
    all_flight = [doc.to_dict() for doc in flight_ref.stream()]
    time.sleep(random.randint(0,2))

    if get_data is True:
        return all_flight
    else:
        flag = False
        for flight in all_flight:
            if flight['available'] is True:
                flag = True

        return flag

from threading import Thread

# Thread process for booking trip
def get_comp_data():
    # request for data
    q = queue.Queue()
    th1 = Thread(target=lambda q,arg: q.put(['hotel_data',hotel_request(arg)]),args=(q,True,))
    th1.start()
    print("Thread Start: request to hotal api")
    th2 = Thread(target=lambda q,arg: q.put(['flight_data',flight_request(arg)]),args=(q,True,))
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
def req_comp_avail():
    q = queue.Queue()
    th1 = Thread(target=lambda q,arg: q.put(['hotel_avail',hotel_request(arg)]),args=(q,False,))
    th1.start()
    print("Thread Start: request to hotal api")
    th2 = Thread(target=lambda q,arg: q.put(['flight_avail',flight_request(arg)]),args=(q,False,))
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

# ----- Transaction Function Zone -----
@firestore.transactional
def transaction_(transaction,p_id,h_id,sess):
    result = {'hist_book':None,'avail_check':None,'book_status':False}
    print('start request to crawl Flight Hotel Available')
    resp = req_comp_avail()
    result['avail_check'] = resp
    if resp["hotel_avail"] and resp["flight_avail"]:
        resp = get_comp_data()
        tar_flight = resp['flight_data'][int(p_id)-1]
        tar_hotel =  resp['hotel_data'][int(h_id)-1]
        if tar_flight['available'] and tar_hotel['available']:
            trans = {'hotel':tar_hotel,'Flight':tar_flight,'status':'pending'}
            session['user']['transaction_'].append(trans)

            # ----- Update -----
            doc1 = db.collection('Flights').document(str(int(p_id)-1)).get(transaction=transaction)
            doc2 = db.collection('Hotels').document(str(int(h_id)-1)).get(transaction=transaction)
            doc3 = db.collection('Members').document(str(sess['uid'])).get(transaction=transaction)
            
            transaction.update(doc1.reference, {
                'available': False
            })
            print("Update Flight Transaction")
           
            transaction.update(doc2.reference, {
                'available': False
            })
            print("Update Hotel Transaction")
            
            transaction.update(doc3.reference,sess['user'])
            print("Update Member's Transaction")
            # ----- Update -----
            return {'user':session['user'],'error':'-1'}
        else:
            return {'hist':result,'Flight':tar_flight,'Hotel':tar_hotel,'error_msg':'Some Provider Not available','error':'0'}
    else:
        return {'hist':result,'error_msg':'Not either Providers available','error':'1'}
            
@firestore.transactional
def cancel_trans_(transaction,uid,trid):
    # ----- Update -----
    doc = db.collection('Members').stream()
    data = [d.to_dict() for d in doc]
    data[uid]['transaction_'].pop(trid)
    # print(data[uid])

    doc = db.collection('Members').document(str(uid)).get(transaction=transaction)
    transaction.update(doc.reference,data[uid])
    print("Update Member's Transaction")
# ----- Transaction Function Zone -----

# ----- Page Zone -----
# Index Page
@app.route("/",methods=['GET'])
def index():
    return render_template("index.html")

# sign up Page
@app.route("/signup",methods=['GET','POST'])
def signup():
    all_ = [doc.to_dict() for doc in member_ref.stream()]
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        base_ = {'Username':username,'Password':password,
            'signup_date':datetime.now().strftime("%c"),'transaction_':[]}

        try:
            id = str(len(all_))
            member_ref.document(id).set(base_)
            return redirect('/login',)
        except Exception as e:
            return f"An Error Occured: {e}"

        return redirect('/login',)
    else:
        return render_template("signup.html")

# Login Page
@app.route("/login",methods=['GET','POST'])
def login():
    all_ = [doc.to_dict() for doc in member_ref.stream()]
    usn_in_db = [a['Username'] for a in all_]
    pwd_in_db = [a['Password']for a in all_]
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if(password in pwd_in_db and username in usn_in_db):
            session['user'] = all_[usn_in_db.index(username)]
            session['uid'] = usn_in_db.index(username)
            # print(session['user'])
            return redirect('/afterlog')
        else:
            return abort(404)
    else:
        return render_template("login.html")

# Book Page
@app.route('/afterlog',methods=['GET'])
def afterlog():
    return render_template("afterlog.html")

# Profile Page
@app.route('/profile',methods=['GET','POST'])
def profile():
    if request.method == 'POST':
        old_pass = request.form["old_pwd"]
        if session['user']['Password'] == old_pass:
            new_pass = request.form['new_pwd']
            session['user']['Password'] = new_pass
            try:
                id = str(session['uid'])
                member_ref.document(id).update(session['user'])
                # return jsonify({"success": True}), 200
            except Exception as e:
                print(f"An Error Occured: {e}")
            return redirect('/')
        
        return redirect('/profile')
    else:
        if not session["user"] is None:
            user = session["user"]
            return render_template("profile.html", user=user,uid=session['uid'])
        else:
            print("No username found in session")
            return redirect("/sign_in")
    # return render_template("profile.html")
# ----- Page Zone -----

# ----- Route API Zone -----
# ----- CRUD -----
@app.route('/member/create', methods=['POST'])
def member_create():
    """
        create() : Add document to Firestore collection with request body
        Ensure you pass a custom ID as part of json body in post request
        e.g. json={"Password":"00000","Username":"Gambit","_ID":0,"book_":{"flight_booked":false,"hotel_booked":false},
                "stamp":"April 9, 2020 at 12:00:00 AM UTC+7"}
    """
    try:
        id = str(request.json['_ID'])
        member_ref.document(id).set(request.json)
        return jsonify({"success": True}), 200
    except Exception as e:
        return f"An Error Occured: {e}"

@app.route('/member/list', methods=['GET'])
def member_read():
    """
        read() : Fetches documents from Firestore collection as JSON
        todo : Return document that matches query ID
        all_todos : Return all documents
    """
    try:
        # Check if ID was passed to URL query
        todo_id = request.args.get('id')    
        if todo_id:
            todo = member_ref.document(todo_id).get()
            return jsonify(todo.to_dict()), 200
        else:
            all_todos = [doc.to_dict() for doc in member_ref.stream()]
            return jsonify(all_todos), 200
    except Exception as e:
        return f"An Error Occured: {e}"

@app.route('/member/update', methods=['POST', 'PUT'])
def member_update():
    """
        update() : Update document in Firestore collection with request body
        Ensure you pass a custom ID as part of json body in post request
        e.g. json={"Password":"00000","Username":"Gambit","_ID":0,"book_":{"flight_booked":false,"hotel_booked":false},
                "stamp":"April 9, 2020 at 12:00:00 AM UTC+7"}
    """
    try:
        data = request.json
        id = str(data['id'])
        del data['id']
        member_ref.document(id).update(data)
        return jsonify({"success": True}), 200
    except Exception as e:
        return f"An Error Occured: {e}"
        
@app.route('/member/delete', methods=['GET', 'DELETE'])
def member_delete():
    """
        delete() : Delete a document from Firestore collection
    """
    try:
        # Check for ID in URL query
        todo_id = request.args.get('id')
        member_ref.document(todo_id).delete()
        return jsonify({"success": True}), 200
    except Exception as e:
        return f"An Error Occured: {e}"

@app.route('/flight/create', methods=['POST'])
def flight_reate():
    """
        create() : Add document to Firestore collection with request body
        Ensure you pass a custom ID as part of json body in post request
        e.g. json={"Password":"00000","Username":"Gambit","_ID":0,"book_":{"flight_booked":false,"hotel_booked":false},
                "stamp":"April 9, 2020 at 12:00:00 AM UTC+7"}
    """
    try:
        id = str(request.json['_ID'])
        flight_ref.document(id).set(request.json)
        return jsonify({"success": True}), 200
    except Exception as e:
        return f"An Error Occured: {e}"

@app.route('/flight/list', methods=['GET'])
def flight_read():
    """
        read() : Fetches documents from Firestore collection as JSON
        todo : Return document that matches query ID
        all_todos : Return all documents
    """
    try:
        # Check if ID was passed to URL query
        todo_id = request.args.get('id')    
        if todo_id:
            todo = flight_ref.document(todo_id).get()
            return jsonify(todo.to_dict()), 200
        else:
            all_todos = [doc.to_dict() for doc in member_ref.stream()]
            return jsonify(all_todos), 200
    except Exception as e:
        return f"An Error Occured: {e}"

@app.route('/flight/update', methods=['POST', 'PUT'])
def flight_update():
    """
        update() : Update document in Firestore collection with request body
        Ensure you pass a custom ID as part of json body in post request
        e.g. json={"Password":"00000","Username":"Gambit","_ID":0,"book_":{"flight_booked":false,"hotel_booked":false},
                "stamp":"April 9, 2020 at 12:00:00 AM UTC+7"}
    """
    try:
        data = request.json
        id = str(data['id'])
        del data['id']
        flight_ref.document(id).update(data)
        return jsonify({"success": True}), 200
    except Exception as e:
        return f"An Error Occured: {e}"
        
@app.route('/flight/delete', methods=['GET', 'DELETE'])
def flight_delete():
    """
        delete() : Delete a document from Firestore collection
    """
    try:
        # Check for ID in URL query
        todo_id = request.args.get('id')
        flight_ref.document(todo_id).delete()
        return jsonify({"success": True}), 200
    except Exception as e:
        return f"An Error Occured: {e}"

@app.route('/hotel/create', methods=['POST'])
def hotel_create():
    """
        create() : Add document to Firestore collection with request body
        Ensure you pass a custom ID as part of json body in post request
        e.g. json={"Password":"00000","Username":"Gambit","_ID":0,"book_":{"flight_booked":false,"hotel_booked":false},
                "stamp":"April 9, 2020 at 12:00:00 AM UTC+7"}
    """
    try:
        id = str(request.json['_ID'])
        hotel_ref.document(id).set(request.json)
        return jsonify({"success": True}), 200
    except Exception as e:
        return f"An Error Occured: {e}"

@app.route('/hotel/list', methods=['GET'])
def hotel_read():
    """
        read() : Fetches documents from Firestore collection as JSON
        todo : Return document that matches query ID
        all_todos : Return all documents
    """
    try:
        # Check if ID was passed to URL query
        todo_id = request.args.get('id')    
        if todo_id:
            todo = hotel_ref.document(todo_id).get()
            return jsonify(todo.to_dict()), 200
        else:
            all_todos = [doc.to_dict() for doc in member_ref.stream()]
            return jsonify(all_todos), 200
    except Exception as e:
        return f"An Error Occured: {e}"

@app.route('/hotel/update', methods=['POST', 'PUT'])
def hotel_update():
    """
        update() : Update document in Firestore collection with request body
        Ensure you pass a custom ID as part of json body in post request
        e.g. json={"Password":"00000","Username":"Gambit","_ID":0,"book_":{"flight_booked":false,"hotel_booked":false},
                "stamp":"April 9, 2020 at 12:00:00 AM UTC+7"}
    """
    try:
        data = request.json
        id = str(data['id'])
        del data['id']
        hotel_ref.document(id).update(data)
        return jsonify({"success": True}), 200
    except Exception as e:
        return f"An Error Occured: {e}"
        
@app.route('/hotel/delete', methods=['GET', 'DELETE'])
def hotel_delete():
    """
        delete() : Delete a document from Firestore collection
    """
    try:
        # Check for ID in URL query
        todo_id = request.args.get('id')
        hotel_ref.document(todo_id).delete()
        return jsonify({"success": True}), 200
    except Exception as e:
        return f"An Error Occured: {e}"
# ----- CRUD -----
# ----- Additional CRUD -----
@app.route('/all', methods=['GET', 'DELETE'])
def export():
    result = {}
    all_hotel = [doc.to_dict() for doc in hotel_ref.stream()]
    all_member = [doc.to_dict() for doc in member_ref.stream()]
    all_flight = [doc.to_dict() for doc in flight_ref.stream()]
    temp = {}
    for i in range(len(all_member)):
        temp[str(i)] = all_member[i]
    result['Members'] = temp
    temp = {}
    for i in range(len(all_hotel)):
        temp[str(i)] = all_hotel[i]
    result['Hotels'] = temp
    temp = {}
    for i in range(len(all_flight)):
        temp[str(i)] = all_flight[i]
    result['Flights'] = temp
    print(json.dumps(result,indent=4))
    with open('firestore-indata.json','wb') as file:
        # file.write(json.dumps(result,indent=4))
        json.dump(result,file,indent=4)
    
    return jsonify(result)
# ----- Additional CRUD -----
@app.route('/book',methods=['POST'])
def get_book():
    try:
        user = session['user']
    except:
        return redirect('/')
    transaction = db.transaction()
    p_id = request.form['plane']
    h_id = request.form['hotel']
    t_response = transaction_(transaction,p_id,h_id,session)
    if int(t_response['error']) < 0:
        return jsonify({'trans_reponse':t_response,'status':'Success'})
    else:
        return jsonify({'trans_reponse':t_response,'status':'Unsuccess'})

@app.route('/cancel/<trid>',methods=['GET','POST'])
def cancel_tr(trid):
    transaction = db.transaction()
    user = session['user']
    cancel_trans_(transaction,int(session['uid']),int(trid))
    return render_template("profile.html", user=user,uid=session['uid'])

@app.route('/logout')
def logout():
    app.secret_key = secrets.token_urlsafe(len('_5#y2L"F4Q8z\n\xec]/'))
    return redirect('/')
# ----- Route API Zone -----

if __name__ == "__main__":
	app.run(debug=True,threaded=True)

