from .diceqube import diceqube
from flask import Flask
from flask import render_template

# instantiate flask application
app = Flask(__name__)


@app.route('/')  # Define route for root URL
def index():
    password_list = diceqube()
    return render_template('index.html', password_list=password_list)

# Run the Flask app if this script is executed directly
if __name__ == '__main__':
    app.run(debug=True)