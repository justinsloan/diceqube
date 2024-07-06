# Importing necessary libraries
from flask import Flask
from flask import render_template
import string
import secrets
import json
import requests
import configparser
import pkg_resources

# Specify the location of the word list inside the package
RESOURCE_NAME = __name__
PATH = "word_list.txt"
WORD_LIST_FILE = pkg_resources.resource_filename(RESOURCE_NAME, PATH)

# Load API key from file
# Get a free API key at https://quantumnumbers.anu.edu.au/
config = configparser.ConfigParser()
config.read('config.txt')
free_api_key = config['APIKEY']['free'] # 100 requests/month for free
paid_api_key = config['APIKEY']['paid'] # Unlimited requests/month for $0.005/request


# ANU QRDG server URL
API_URL="https://api.quantumnumbers.anu.edu.au/"

# Set mode options
VERBOSE = True #bool(args.verbose) # Sets VERBOSE to True if arg is provided, False if not
#LOCAL = False

# Load the standard wordlist file
WORD_DICT = {}
with open(WORD_LIST_FILE) as f:
    for line in f.readlines():
        index, word = line.strip().split('\t')
        WORD_DICT[int(index)] = word

# start the flask application
app = Flask(__name__)


@app.route('/')  # Define route for root URL
def diceqube():
    '''Generate a list of 5 passwords and display them to the user'''

    valid = validate_request(args.count, args.words)

    if not valid:
        exit()

    # p_verbose("Gathering quantum data...")
    qube = fetch_AQN()

    if qube.status_code == 200:
        content = qube.text
        load = json.loads(content)
        data = load["data"]
        password_list = [generate_diceware_phrase(data, args.count, args.words, args.char, args.pretext, args.posttext) for _ in range(1)]
    else:
        password_list = f"Error: {qube.status_code}, {qube.text}"

    return render_template('index.html', password_list=password_list)

def generate_random_password():
    '''Generate a random password of 12 characters (8 alphabets, 4 digits).'''

    alphabet = string.ascii_letters  # 26 lowercase + 26 uppercase letters
    numbers = string.digits  # 0 to 9 digits
    all_chars = alphabet + numbers  # Combine both alphabets and numbers

    while True:
        password = ''.join(secrets.choice(all_chars) for i in range(8))
        password += ''.join(secrets.choice(numbers) for i in range(4))

        if any(c.islower() for c in password) and any(c.isupper() for c in password):
            break  # The randomly generated password has at least one uppercase & lowercase letter, 8 alphabets + 4 digits

    return password


def generate_diceware_phrase(data, phrase_count=5, word_count=6, char="-", pre="", post=""):
    """Generates passphrases"""
    qube_i = 0
    for phrase in range(0, phrase_count):
        phrase_words = []

        for word in range(0, word_count):
            token = ""

            for i in range(5):
                roll = data[qube_i] % 6 + 1
                qube_i += 1
                token += str(roll)

            #p_verbose(f"Dice Roll: {token}")
            phrase_words.append(WORD_DICT[int(token)])

        passphrase = pre + char.join(phrase_words) + post
        return passphrase


def fetch_AQN(api_key=free_api_key):
    """
    Fetches quantum data from ANU AQN service and returns
    it as a list of integers. Each request can produce up
    to 170 diceware words.
    """
    headers = {'Content-Type': 'application/json',
               'x-api-key': api_key,
              }
    response = requests.get(f"{API_URL}?length=1020&type=uint16", headers=headers)

    while response.status_code == 500:
        if not paid_api_key:
            print("Error: There are no remaining free requests")
        else:
            response = fetch_AQN(paid_api_key)  # change key and try again

    return response


def validate_request(phrases, words):
    """
    Validates the request is within the maximum range (170)
    and returns a boolean.
    """
    word_count = phrases * words
    if word_count > 170:
        max = int(170 / words)
        print(f"Error: With {words} words per passphrase, you can only generate {max} passphrases per request.")
        return False
    return True


# Run the Flask app if this script is executed directly
if __name__ == '__main__':
    app.run(debug=True)