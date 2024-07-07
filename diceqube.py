"""
Diceqube - Quantum Random Passwords
The most secure password generator on the planet.

Requires Python 3.6 or better

Features:
    - Strong but easily memorable passphrases
    - Generated from 100% unique quantum random data


Version History:
24.05 - MAY 2024
 - changed quantum data source to ANU QRDG

"""

# Diceqube - Quantum Diceware
__version__ = "24.05"
__date__ = "4 MAY 2024"
__author__ = "Justin M. Sloan"

# Importing necessary libraries
from importlib import resources
from fileinput import lineno
import json
import requests
import configparser


# Specify the location of the word list inside the package
RESOURCE_NAME = __package__
PATH = "word_list.txt"
WORD_LIST_FILE = resources.path(RESOURCE_NAME, PATH)

# Set count defaults
PHRASE_COUNT = 5
WORD_COUNT = 5

# Load API key from file
# Get a free API key at https://quantumnumbers.anu.edu.au/
config = configparser.ConfigParser()
config.read('config.txt')
free_api_key = config['APIKEY']['free'] # 100 requests/month for free
paid_api_key = config['APIKEY']['paid'] # Unlimited requests/month for $0.005/request


# ANU QRDG server URL
API_URL="https://api.quantumnumbers.anu.edu.au"

# Set mode options
VERBOSE = True

# Load the standard wordlist file as dict
WORD_DICT = {}
with open(WORD_LIST_FILE) as f:
    for line in f.readlines():
        index, word = line.strip().split('\t')
        WORD_DICT[int(index)] = word


def diceqube():
    '''Generate a list of N passwords and display them to the user'''

    # Get the time so we can calculate how long it takes
    #start_time = time.time()

    #time_stamp = __get_last_execution_timestamp()
    #time_delta = int(time.time() - time_stamp)
    #__verbose(f"Last execution: {time_delta} seconds ago.")

    print("Requesting entropy, please wait...")

    blocks = calculate_entropy(PHRASE_COUNT, WORD_COUNT)
    entropy = get_entropy(blocks)
    password_list = []

    # Loop until requested number of passphrases are generated
    for i in range(0, PHRASE_COUNT):
        entropy, password = generate_password(entropy, WORD_COUNT)
        password_list.append(password)
        print(f"{i}: {password}")

    # Calculate how long it took and print if Verbose mode is on
    #run_time = int((time.time() - start_time) * 10) / 10
    #__verbose(f"--- Finished in {run_time} seconds ---")

    return password_list


def __get_block(entropy):
    block = iter(entropy)
    try:
        return next(block)
    except StopIteration:
        print("Error: end of block list.")


def get_entropy(blocks_count=1):
    """
    Collect entropy from the ANU QRNG and return a list of 4-digit
    hexadecimal numbers
    - we need a way to limit requests to once per minute
    -- environment variables?
    -- pause function that counts down time if needed?
    """
    #__verbose(f"Getting {blocks_count} blocks of entropy...")
    response = fetch_AQN(blocks_count=blocks_count)

    #__verbose("The request was successful!")
    #__save_execution_timestamp()
    request = json.loads(response.text)
    blocks = request['data']
    count_check = len(blocks)
    if count_check == blocks_count:
        #__verbose("Block count validated.")
        combined_entropy = ''.join(blocks)
        entropy = [combined_entropy[i:i+4] for i in range(0, len(combined_entropy), 4)]
        #__verbose(entropy)

        return entropy
    else:
        #__save_execution_timestamp()
        print(f"Error: {blocks_count} block(s) were requested but {count_check} blocks were returned.")


def calculate_entropy(phrase_count=1, word_count=5):
    """
    Calculate how much entropy data is needed and return an int of
    how many blocks to request
    Formula: Num_Blocks = (Words * 5) * Num_Phrases
    - minimum block request is 1
    - we can get 512 rolls per block
    - each word requires 5 rolls
    """
    # sanitize input
    phrase_count = int(phrase_count) # truncate
    word_count = int(word_count) # truncate

    # do some error checking
    if phrase_count < 1 or word_count < 1:
        print(f"Error {lineno}: Word Count ({word_count}) or Phrase Count ({phrase_count}) cannot be less than 1.")
        exit(1)
    elif phrase_count > 100:
        print(f"Error {lineno}: Phrase Count cannot be greater than 100.")
        exit(1)
    elif word_count > 12:
        print(f"Error {lineno}: Word Count cannot be greater than 30.")
        exit(1)

    # do the math
    roll_count = (word_count * 6) * phrase_count # we need six rolls per word
    block_count = roll_count / 10
    blocks = int(block_count + 1) # truncate and round up
    #__verbose(f"Blocks calculated: {blocks}")

    return blocks


def generate_password(entropy, word_count=5, char="-", pre="", post=""):
    """
    Generate a single password and return as a string
    """
    dice_words = []
    dice = []
    numbers = []

    block_count = word_count * 5              # get enough blocks for the number of words
    blocks = entropy[:block_count]            # slice block_count items from entropy
    del entropy[:block_count]                 # delete the sliced items from entropy

    rand_num_count = word_count               # get enough blocks for use a base10 numbers
    num_blocks = entropy[:rand_num_count]     # slice rand_num_count items from entropy
    del entropy[:rand_num_count]              # delete the sliced items from entropy

    for block in blocks:                      # convert hexadecimal blocks to mod6
        die = int(block, 16) % 6 + 1
        dice.append(str(die))

    for num in num_blocks:                    # convert hexadecimal blocks to mod99
        number = int(num, 16) % 99
        numbers.append(str(number))

    dice = ''.join(dice)
    roll = [str(dice)[i:i + 5] for i in range(0, len(str(dice)), 5)]
    num_loop = 0
    for i in roll:
        #__verbose(f"Dice Rolls: {i}")
        # TODO make capitalization an arg option
        token = WORD_DICT[int(i)]
        rand_number = numbers[num_loop]
        num_loop += 1
        #__verbose(str(token + rand_number))
        word = token[0].upper() + token[1:] + str(rand_number)
        dice_words.append(word)

    password = pre + char.join(dice_words) + post

    return entropy, password


def fetch_AQN(api_key=free_api_key, blocks_count=1):
    """
    Fetches quantum data from ANU AQN service and returns
    it as a list of integers. Each request can produce up
    to 170 diceware words.
    """
    headers = {'Content-Type': 'application/json',
               'x-api-key': api_key,
              }
    response = requests.get(f"{API_URL}?length={blocks_count}&type=hex16&size=10", headers=headers)

    if not response.status_code == 200:
        if not paid_api_key:
            print(f"Error {response.status_code}: There are no remaining free requests")
        else:
            response = fetch_AQN(paid_api_key)  # change key and try again

    return response


