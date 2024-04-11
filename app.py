from flask import Flask, render_template, request, redirect, session
from pymongo import MongoClient
import random

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['higher_lower_game']
collection = db['game_sessions']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/play')
def play():
    session.clear()  # Clear any existing game session
    session['round'] = 1
    session['player_wins'] = 0
    return redirect('/guess')

@app.route('/guess', methods=['GET', 'POST'])
def guess():
    if 'round' not in session or session['round'] > 5:
        return redirect('/play')

    if 'number' not in session:
        session['number'] = random.randint(1, 100)
        session['guesses'] = 0

    if request.method == 'POST':
        guess = request.form['guess']
        session['guesses'] += 1

        if (guess == 'higher' and session['next_number'] > session['number']) or \
           (guess == 'lower' and session['next_number'] < session['number']):
            session['player_wins'] += 1
            session['round'] += 1
            if session['player_wins'] >= 3 or session['round'] > 5:
                game_status = "Won" if session['player_wins'] >= 3 else "Lost"
                save_game_result(session['player_wins'], session['next_number'], session['guesses'])
                session.clear()
                return redirect('/result')
            else:
                session['number'] = session['next_number']
                session['next_number'] = random.randint(1, 100)
                session['guesses'] = 0
                return render_template('guess.html', message='You won this round! On to the next round.', round=session['round'])

        else:
            message = 'Incorrect! Try again.'
    else:
        session['next_number'] = random.randint(1, 100)
        message = 'Is the next number higher or lower?'

    return render_template('guess.html', message=message, round=session['round'])

def save_game_result(player_wins, number_to_guess, guesses):
    game_result = {'player_wins': player_wins, 'number_to_guess': number_to_guess, 'guesses': guesses}
    collection.insert_one(game_result)

@app.route('/result')
def result():
    game_history = collection.find()
    return render_template('result.html', game_history=game_history)

@app.route('/games_history')
def games_history():
    game_history = collection.find()
    return render_template('games_history.html', game_history=game_history)

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True)
