# Call Break Bots

Exploring Call Break strategies through combinatorics, probability, expected-value analysis and computational experiments.

**Status:** Game engine v1.0 implemented and tested; mathematical strategy research in progress. Competitive bots and benchmarking are future work.

## Motivation

Call Break is a four-player trick-taking card game in which players predict how many tricks they will win before playing their hands. A player must balance the reward for a higher bid against the penalty for failing to meet it, while making decisions with incomplete information about opponents' cards.

I want to investigate how mathematical reasoning and computational experiments can improve both bidding and card-playing decisions. The goal is to build a sequence of increasingly capable bots, test their strategies under reproducible conditions, and understand why those strategies succeed or fail.

## The game

This implementation uses the following rule variant:

- Four players receive 13 cards each from a standard 52-card deck.
- Each player bids between 1 and 13 tricks before play begins.
- Spades are permanent trump; the highest trump wins a trick, or the highest card of the leading suit if no trump is played.
- Players must follow suit if possible, beat the current winner within the compulsory suit if possible, and play a spade if they cannot follow suit and hold one. If overtrumping is impossible, a lower spade is still compulsory.
- The winner of each trick leads the next. A game consists of five rounds by default.

For a bid `b` and actual tricks won `t`, the score is

```math
S(b,t)=\begin{cases}
b+0.1(t-b), & t\ge b,\\
-b, & t<b.
\end{cases}
```

For example, bidding 3 and winning 5 earns 3.2 points; bidding 3 and winning 2 earns -3 points. The player with the highest cumulative score wins; ties are retained. See [the engine documentation](docs/ENGINE.md) for the exact rule and API details. Other Call Break variants may use different rules.

## Research and strategy development

The initial bidding strategy investigates when high cards, particularly Aces and Kings, should contribute to a bid. Rather than assuming every high card guarantees a trick, I am examining how suit distributions and the cost of missing a bid affect that decision.

| Research question | Approach | Status |
| --- | --- | --- |
| How likely is an opponent to start without cards of my suit? | Exact combinatorial counting and inclusion-exclusion | Initial-deal model derived |
| When should an Ace increase my bid? | Simplified expected-value comparison using initial suit voids as a proxy for risk | Provisional |
| When should a King increase my bid? | Model the event that every opponent starts with at least two cards of that suit | Provisional |
| Can multiple risky Kings jointly justify one extra bid? | Study the probability distribution of their combined trick wins | Under investigation |
| How well do these assumptions hold during real play? | Compare predictions with simulated games | Planned |

See [the research overview](docs/RESEARCH_OVERVIEW.md) for the current mathematical models, assumptions and limitations. The detailed research journal, if maintained separately, should be preserved alongside this overview.

## Game engine

To make strategy development independent of game mechanics, I asked ChatGPT to implement a reusable Python engine. It deals cards, manages bidding and turn order, enforces legal moves, evaluates trick winners and calculates scores. It also provides reproducible shuffling, public game histories and a fixed interface for every bot.

Each bot implements only two methods:

```python
from callbreak import Card, Observation

class MyBot:
    def give_bid(self, cards: tuple[Card, ...], observation: Observation) -> int:
        raise NotImplementedError

    def play_card(self, cards: tuple[Card, ...], observation: Observation) -> Card:
        raise NotImplementedError
```

`cards` contains the acting player's remaining hand. `observation` contains public information, including announced bids, scores, tricks won, played cards and legal moves. Opponents' hidden hands are not included. The bot is responsible only for choosing its bid and card.

## Getting started

Requires Python 3.10 or newer. No third-party runtime dependencies are required. From the repository root:

```bash
python -m unittest discover -s tests -v
```

Copy `bot_template.py` to `my_bot.py` and implement both methods. Then a game can be run as follows:

```python
from callbreak import run_game
from my_bot import MyBot

result = run_game([MyBot() for _ in range(4)], seed=42)
print(result.scores)
print(result.winners)
```

A seed fixes the engine's random draws. Bots with their own randomness need separate seeding for full reproducibility. The template is intentionally incomplete: it is not a working competitive bot.

## Repository structure

```text
call-break-bots/
├── callbreak/
│   ├── __init__.py
│   └── engine.py              # Rules, observations, scoring and game runner
├── docs/
│   ├── ENGINE.md              # Complete engine API and rule specification
│   └── RESEARCH_OVERVIEW.md   # Mathematical models and their limitations
├── tests/
│   └── test_engine.py         # Automated engine tests
├── bot_template.py            # Interface for my own bots
├── pyproject.toml
├── .gitignore
└── README.md
```

## Roadmap

- [x] Define a consistent game engine and bot interface.
- [x] Implement and test game mechanics.
- [x] Investigate initial suit-distribution probabilities.
- [x] Develop provisional Ace and King bidding models.
- [ ] Extend the bidding model to multiple uncertain high cards.
- [ ] Implement baseline and probability-based competitive bots.
- [ ] Develop card-playing strategies using observed game history.
- [ ] Build a reproducible tournament and evaluation framework.
- [ ] Test assumptions and compare strategies against baselines.
- [ ] Explore reinforcement learning as a possible extension.

## Authorship and use of AI

I lead the research: I formulate the strategy questions, propose and evaluate mathematical assumptions, and decide how to turn the analysis into bot strategies. My intended implementation work is the bots themselves and their evaluation.

ChatGPT (OpenAI) was used to implement the standalone game engine, bot interface, test suite and initial technical documentation. It has also assisted with combinatorial probability calculations, expected-value comparisons and organizing my research notes. The initial repository documentation was drafted with ChatGPT's assistance. The strategy research is a collaboration in which I direct the investigation; the research summaries do not assign individual derivations to either contributor without a reliable record of who performed them.

AI-generated engine code is covered by the automated tests, but those tests do not prove that every rule variant or strategic assumption is correct. No competitive bot performance or reinforcement learning results are claimed at this stage.

## Testing and reproducibility

The current engine passes eight automated tests covering card distribution, legal moves, trick winners, scoring, invalid actions, observation consistency, complete games and seeded reproducibility. The test suite includes random-play simulations for correctness checks, not competitive strategy evaluation.
