#!flask/bin/python
from flask import Flask, jsonify
import random, math

app = Flask(__name__)

# Hotel API for Request and Book
def hotel_api(ratio=(0.5,0.5),delay=0):
    li_one = [1 for i in range(math.ceil(ratio[1])+1)]
    li_zero = [0 for i in range(math.ceil(ratio[0])+1)]
    li_one.extend(li_zero)
    ans = random.choice(li_one)
    if ans is 1:
        return True
    else:
        return False

# Flight API for Request and Book
def flight_api(ratio=(0.5,0.5),delay=0)):
    li_one = [1 for i in range(math.ceil(ratio[1])+1)]
    li_zero = [0 for i in range(math.ceil(ratio[0])+1)]
    li_one.extend(li_zero)
    ans = random.choice(li_one)
    if ans is 1:
        return True
    else:
        return False

# Thread process for booking trip
def book():
    pass

# Thread process for request api data
def api_call():
    pass


# Index Page
@app.route('/', methods=['GET'])
def index():
    pass

# Book Page
@app.route('/book', methods=['GET'])
def get_book():
    pass


if __name__ == "__main__":
	app.run(debug=True)

