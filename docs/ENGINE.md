# Call Break engine

Headless Python 3.10+ game engine for evaluating Call Break bots. No third-party runtime dependencies, GUI or competitive bot logic.

## Start

Open a terminal at the repository root. Run the tests:

```sh
python -m unittest discover -s tests -v
```

Copy `bot_template.py` to your own bot module, fill in its two methods, then run a game from a Python script in this directory:

```python
from callbreak import run_game
from my_bot import MyBot

result = run_game([MyBot() for _ in range(4)], seed=42)
print(result.scores)   # cumulative scores by seat
print(result.winners)  # tuple of all winning seats
```

You can also install the package with `python -m pip install -e .` if desired.

## Bot contract

```python
from callbreak import Card, Observation

class MyBot:
    def give_bid(self, cards: tuple[Card, ...], observation: Observation) -> int:
        # Return an integer between 1 and 13.
        raise NotImplementedError

    def play_card(self, cards: tuple[Card, ...], observation: Observation) -> Card:
        # Return a card from observation.legal_cards.
        raise NotImplementedError
```

No inheritance is required. Both callbacks receive immutable snapshots. `cards` is only the acting player's remaining hand, sorted by suit (C, D, H, S) and increasing rank. Other hands and undealt deck order are not exposed. Each card is a frozen, hashable `Card(rank, suit)`. Ranks are integers 2–14, where 11=J, 12=Q, 13=K, 14=A. Suits are strings C, D, H, S. For example, `Card(14, 'S')` is the ace of spades. `str(card)` produces `AS`.

`give_bid` is called once per round per player. `play_card` is called once per trick per player. Invalid actions raise `IllegalAction` with round, seat and (for plays) trick information; the engine does not substitute a move. A bot can retain its own internal state across calls. Use a distinct instance for each seat and a fresh set of bots for independent games, unless you intentionally want learning across games. Bot exceptions propagate.

## Observation reference

All player-indexed tuples use fixed seats 0, 1, 2, 3. Round and trick numbers start at 1, except trick_number=0 during bidding.

| Field / property | Meaning |
|---|---|
| `player` | Your seat index. |
| `phase` | `'bid'` or `'play'`. |
| `round_number`, `total_rounds` | Round counters. |
| `dealer`, `leader` | Dealer and current trick leader (first leader during bidding). |
| `trick_number` | Current trick, or 0 while bidding. |
| `bids` | Public bids by seat; `None` until a player bids. |
| `tricks_won` | Completed tricks won in the current round, by seat. |
| `scores` | Cumulative scores from completed rounds, by seat. |
| `score_tenths` | Same scores as exact integers in units of 0.1. |
| `current_trick` | Tuple of `Play(player, card)` in play order. |
| `completed_tricks` | Tuple of `Trick(plays, winner)` in current round. |
| `played_cards` | Flattened `Play` records from the current round, including the current trick. |
| `legal_cards` | All cards you may legally return; empty during bidding. |
| `previous_rounds` | Public `RoundResult` history of completed rounds. |
| `hand_sizes` | Remaining card counts by seat. |
| `lead_suit` | Leading suit, or `None` before a card is played. |
| `current_winner` | Seat currently winning the trick, or `None` if empty. |
| `turn_order` | Full current trick order, starting with its leader. |
| `bid_order` | Full bidding order, starting after dealer. |

For example, `observation.current_trick[0].card.suit` is the led suit when a card has already been played. `observation.tricks_won[observation.player]` is your own current trick count. Each `Play` has `.player` and `.card`. Each `Trick` has `.plays` and `.winner`. Historical `RoundResult` objects have `.round_number`, `.dealer`, `.bids`, `.tricks_won`, `.scores`, `.score_tenths`, and `.tricks`. Round result scores are round deltas, unlike observation scores.

## Rules implemented

- Four players; standard 52-card deck; 13 cards each, 13 tricks per round; five rounds by default.
- First dealer randomly chosen, then advances one seat per round. Bidding and first trick start after dealer. Seats advance cyclically. Winner leads the next trick.
- Sequential bids, each 1–13; no restriction on sum of bids. Previous bids are public.
- Spades are permanent trump. Highest trump wins; otherwise highest card of the leading suit wins.
- If you have the led suit, you must follow it. If any card of that suit can beat the current winner, you must choose one of those winning cards. If a trump already wins a non-spade lead, you still must follow the lead suit if possible, but any card of that suit is legal.
- If you cannot follow suit and hold spades, you must play a spade, overtrumping when possible. If you cannot overtrump, a lower spade is compulsory. If you have neither the led suit nor spades, any card is legal.
- A leader may play any card, including spades. No redeal conditions, special bids, bonus money, or additional house rules.
- Bid b and tricks t: if t >= b, score = b + 0.1*(t-b); otherwise score = -b. Highest cumulative score wins. All first-place ties are returned (no tie-breaker). Scoring uses integer tenths internally.

## Engine API

`run_game(bots, *, seed=None, rounds=5, first_dealer=None) -> GameResult`

`bots` must contain four bot objects in seat order. `seed` controls the local RNG for deck shuffles and random initial dealer. If supplied, `first_dealer` fixes the initial dealer (0–3) instead of drawing it randomly. Reproduce a game with the same arguments and deterministic or identically seeded fresh bots. Bot randomness is separate from the engine RNG.

`GameResult` provides `.scores`, `.score_tenths`, `.winners` (tuple of seat indices), and `.rounds` (complete public round records). For large experiments, call `run_game` repeatedly and rotate bot seats; the engine is independent of the simulation/analysis layer.

Other exported helpers: `DECK`, `SUITS`, `RANKS`, `TRUMP`, `legal_cards(hand, trick)`, `trick_winner(trick)`, `score_tenths(bid, tricks)`.

## Files

- `callbreak/engine.py`: rules, data types, game runner and scoring.
- `callbreak/__init__.py`: public imports.
- `bot_template.py`: empty two-method bot template.
- `tests/test_engine.py`: rule, score, observation, invalid-action and full-game tests (test-only random bots).
- `pyproject.toml`: optional package metadata.

The observation API prevents accidental hidden-information access; it is not a security sandbox for untrusted bot code. This is a standalone implementation rather than an edit of older project files.
