#!flask/bin/python
from flask import Flask, jsonify
import random, math, time

app = Flask(__name__)

# Hotel API for Request and Book
def hotel_api(ratio=(0.5,0.5),delay=0):
    li_one = [1 for i in range(math.ceil(ratio[1])+1)]
    li_zero = [0 for i in range(math.ceil(ratio[0])+1)]
    li_one.extend(li_zero)
    ans = random.choice(li_one)
    if delay > 0:
        time.sleep(delay)
        
    if ans is 1:
        return True
    else:
        return False

# Flight API for Request and Book
def flight_api(ratio=(0.5,0.5),delay=0):
    li_one = [1 for i in range(math.ceil(ratio[1])+1)]
    li_zero = [0 for i in range(math.ceil(ratio[0])+1)]
    li_one.extend(li_zero)
    ans = random.choice(li_one)
    if delay > 0:
        time.sleep(delay)

    if ans is 1:
        return True
    else:
        return False

from concurrent.futures import ThreadPoolExecutor

# Thread process for booking trip
def book():
    with ThreadPoolExecutor(max_workers=2) as exe:
        resp_h = exe.submit(hotel_api)
        resp_f = exe.submit(flight_api)
        if resp_h and resp_f:
            return True
        else:
            return {"hotel_resp":resp_h,
                    "flight_resp":resp_f}

# Thread process for request api data
def api_call():
    with ThreadPoolExecutor(max_workers=2) as exe:
        resp_h = exe.submit(hotel_api)
        resp_f = exe.submit(flight_api)
        if resp_h and resp_f:
            return True
        else:
            return {"hotel_resp":resp_h,
                    "flight_resp":resp_f}


# Index Page
@app.route('/', methods=['GET'])
def index():
    pass

# Book Page
@app.route('/book', methods=['GET'])
def get_book():
    resp_chk = api_call()
    if resp_chk:
        resp_book = book()
    else:
        return resp_chk

# create member data
@app.route('/member', methods=['POST'])
def create_member():
    pass

if __name__ == "__main__":
	app.run(debug=True)

