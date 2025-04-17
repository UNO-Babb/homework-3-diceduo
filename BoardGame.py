from flask import Flask, render_template_string, request, session, redirect, url_for
import random
import os

app = Flask(__name__)
app.secret_key = 'race_to_20_secret'

# Load events from events.txt
def load_events():
    events = {}
    turn = 'Player 1'
    if os.path.exists('events.txt'):
        with open('events.txt', 'r') as file:
            for line in file:
                line = line.strip()
                if line.startswith('Turn:'):
                    turn = line.split(':')[1].strip()
                elif ':' in line:
                    space, content = line.split(':', 1)
                    space = int(space.strip())
                    items = [i.strip() for i in content.split(',') if i.strip()]
                    events[space] = items
    return turn, events

initial_turn, board_events = load_events()

@app.route('/')
def index():
    if 'positions' not in session:
        session['positions'] = {'Player 1': 1, 'Player 2': 1}
        session['turn'] = initial_turn
        session['log'] = []
        session['skip_turns'] = {'Player 1': False, 'Player 2': False}

    winner = None
    for player, pos in session['positions'].items():
        if pos == 20:
            winner = player

    return render_template_string(TEMPLATE,
                                  positions=session['positions'],
                                  turn=session['turn'],
                                  log=session['log'],
                                  board_events=board_events,
                                  winner=winner)

@app.route('/roll')
def roll():
    if 'positions' not in session:
        return redirect(url_for('index'))

    log = session['log']
    turn = session['turn']
    if turn is None:
        return redirect(url_for('index'))

    skip_turn = session['skip_turns'].get(turn, False)

    if skip_turn:
        log.append(f"{turn} skips this turn due to Hotel event.")
        session['skip_turns'][turn] = False
        session['turn'] = 'Player 2' if turn == 'Player 1' else 'Player 1'
        return redirect(url_for('index'))

    p1_roll = random.randint(1, 6)
    p2_roll = random.randint(1, 6)
    log.append(f"Player 1 rolls {p1_roll}, Player 2 rolls {p2_roll}.")

    if p1_roll == p2_roll:
        log.append("It's a tie! No one moves.")
    else:
        winner = 'Player 1' if p1_roll > p2_roll else 'Player 2'
        roll_value = max(p1_roll, p2_roll)
        current_pos = session['positions'][winner]
        new_pos = min(current_pos + roll_value, 20)
        session['positions'][winner] = new_pos
        log.append(f"{winner} moves to space {new_pos}.")

        events = board_events.get(new_pos, [])
        for event in events:
            if event == 'Troll':
                new_pos = max(1, new_pos - 3)
                session['positions'][winner] = new_pos
                log.append(f"{winner} encountered a Troll and moves back to {new_pos}.")
            elif event == 'Hotel':
                session['skip_turns'][winner] = True
                log.append(f"{winner} landed on a Hotel and will skip their next turn.")
            elif event == 'Shortcut':
                new_pos = min(20, new_pos + 2)
                session['positions'][winner] = new_pos
                log.append(f"{winner} found a Shortcut and advances to {new_pos}.")

        if new_pos == 20:
            log.append(f"🎉 {winner} wins the game! 🎉")
            session['turn'] = None
            return redirect(url_for('index'))

    session['turn'] = 'Player 2' if turn == 'Player 1' else 'Player 1'
    return redirect(url_for('index'))

TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Race to 20</title>
    <style>
        .board { display: flex; flex-wrap: wrap; }
        .space {
            width: 60px; height: 60px; border: 1px solid #000;
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            margin: 2px;
        }
        .player1 { color: blue; font-weight: bold; }
        .player2 { color: red; font-weight: bold; }
    </style>
</head>
<body>
    <h1>Race to 20</h1>
    {% if winner %}
        <h2>🎉 {{ winner }} wins the game! 🎉</h2>
    {% else %}
        <p><strong>Current Turn:</strong> {{ turn }}</p>
        <form action="/roll" method="get">
            <button type="submit">Roll Dice</button>
        </form>
    {% endif %}

    <div class="board">
        {% for i in range(1, 21) %}
        <div class="space">
            <div><strong>{{ i }}</strong></div>
            {% set contents = board_events.get(i, []) %}
            {% if positions['Player 1'] == i %}<div class="player1">🔵</div>{% endif %}
            {% if positions['Player 2'] == i %}<div class="player2">🔴</div>{% endif %}
            {% for item in contents %}
                {% if item not in ['Player 1', 'Player 2'] %}
                    <div>{{ item }}</div>
                {% endif %}
            {% endfor %}
        </div>
        {% endfor %}
    </div>

    <h2>Game Log</h2>
    <ul>
        {% for entry in log %}
        <li>{{ entry }}</li>
        {% endfor %}
    </ul>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(debug=True)
