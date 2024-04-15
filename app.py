# pip install and import flask, and mongoDB library
from flask import Flask, render_template, request, redirect, session
from pymongo import MongoClient

# rng for card generation
import random

app = Flask(__name__)

# temporary key for session data
app.secret_key = 'tempKey'

# Connect to MongoDB database
client = MongoClient('mongodb://localhost:27017/')
db = client['higher_lower_game']
collection = db['game_sessions']


# route for landing page, index.html
@app.route('/')
def index():
    return render_template('index.html')


# route for play page.
# this route just initializes the game, and immediately redirects user to guess.html where they play the game
@app.route('/play')
def play():
    # ensure data stream is clear
    session.clear()
    # set to round = 1
    session['round'] = 1
    # set wins and losses for each round to 0
    session['player_wins'] = 0
    session['rounds_lost'] = 0
    # use redirect() to send user to guess form
    return redirect('/guess')


# this route is where the user plays game: guess.html. We use GET and POST methods to grab data from html
# and inject it into python code without JS
# this is also where we handle logic currently.
# TODO: Separate logic into multiple functions as demonstrated in BP of app
@app.route('/guess', methods=['GET', 'POST'])
def guess():
    # this ensures that there is no issue with session data stream
    if 'round' not in session or session['round'] > 5:
        return redirect('/play')

    # here we set up local session vars to generate card number and handle the amount of guesses per game
    # this will be cleared per game, hence why it is local to guess
    if 'number' not in session:
        session['number'] = random.randint(1, 100)
        session['guesses'] = 0

    # grab data from button/form
    if request.method == 'POST':
        guess = request.form['guess']

        # reset guesses to 0 for each new round
        session['guesses'] = 0

        # TODO: logic here is clunky, ugly, nested, and hard to read. This will change.

        # This is just checking if user's guess was correct
        if (guess == 'higher' and session['next_number'] > session['number']) or \
                (guess == 'lower' and session['next_number'] < session['number']):
            # if it is correct, we increment the win +rounds played
            session['player_wins'] += 1
            session['round'] += 1
            # if we win, we need to check if we have won best of 5
            if session['player_wins'] >= 3 or session['round'] > 5:
                # if the user won, we set game status to won, and save game result(mongoDB save function)
                game_status = "Won" if session['player_wins'] >= 3 else "Lost"
                save_game_result(session['player_wins'], session['rounds_lost'], game_status)
                session.clear()
                # after we declared win and save result to mongoDB database through save_game_result, we redirect to
                # end game page /result
                return redirect('/result')
            else:
                # else, if we didn't win game yet, play another round and break out of this hideous nested loop
                session['number'] = session['next_number']
                session['next_number'] = random.randint(1, 100)
                return render_template('guess.html', message='You won this round! On to the next round.',
                                       round=session['round'])

        else:  # If the user lost the round
            # increment rounds lost
            session['rounds_lost'] += 1
            # if the user lost the game
            if session['rounds_lost'] >= 3:
                # set status to lost
                game_status = "Lost"
                # send data to database using our save_game_result function
                save_game_result(session['player_wins'], session['rounds_lost'], game_status)
                # clear the session data stream
                session.clear()
                # redirect to display game result to user
                return redirect('/result')
            else:
                # else we keep playing more rounds based on incorrect answer
                session['round'] += 1
                session['number'] = session['next_number']
                session['next_number'] = random.randint(1, 100)
                return render_template('guess.html', message='Incorrect!', round=session['round'])
    # if user didn't respond yet we prompt
    else:
        session['next_number'] = random.randint(1, 100)
        message = 'Is the next number higher or lower?'

    return render_template('guess.html', message=message, round=session['round'])


# This is a simple function that create a python dictionary, and the injects the data into the mongoDB database
# using the collection insert_one method.
def save_game_result(player_wins, rounds_lost, outcome):
    game_result = {'player_wins': player_wins, 'rounds_lost': rounds_lost, 'outcome': outcome}
    collection.insert_one(game_result)


# TODO: this page needs to display game outcome, currently not functional
# displays if user won or lost
# route for the result.html page
@app.route('/result')
def result():
    return render_template('result.html')


# this route is for the games_history.html page, where the database data is injected and displayed
@app.route('/games_history')
def games_history():
    # here we use collection, which is out database collection var, and we store it into a var game_history
    game_history = collection.find()

    # here we render the html page and send the database data to the html where it is injected.
    return render_template('games_history.html', game_history=game_history)


# route for the about.html page where users can read about how to play and what the app does
@app.route('/about')
def about():
    return render_template('about.html')


# run the flask app
if __name__ == '__main__':
    app.run(debug=True)
