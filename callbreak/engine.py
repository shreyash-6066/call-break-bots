"""Deterministic, headless Call Break engine (Python 3.10+)."""
from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import Protocol, Sequence

SUITS = ('C', 'D', 'H', 'S')
TRUMP = 'S'
RANKS = tuple(range(2, 15))


@dataclass(frozen=True, order=True)
class Card:
    rank: int
    suit: str

    def __post_init__(self):
        if type(self.rank) is not int or self.rank not in RANKS or self.suit not in SUITS:
            raise ValueError('Card requires rank 2–14 and suit C, D, H or S')

    def __str__(self):
        return f"{ {11:'J', 12:'Q', 13:'K', 14:'A'}.get(self.rank, self.rank)}{self.suit}"


DECK = tuple(Card(rank, suit) for suit in SUITS for rank in RANKS)


@dataclass(frozen=True)
class Play:
    player: int
    card: Card


def _strength(card: Card, lead: str) -> tuple[int, int]:
    return (2 if card.suit == TRUMP else 1 if card.suit == lead else 0, card.rank)


def trick_winner(trick: Sequence[Play]) -> int:
    """Return the seat currently winning a nonempty trick (even if incomplete)."""
    if not trick:
        raise ValueError('Empty trick has no winner')
    lead = trick[0].card.suit
    return max(trick, key=lambda p: _strength(p.card, lead)).player


def legal_cards(hand: Sequence[Card], trick: Sequence[Play]) -> tuple[Card, ...]:
    """Follow suit, else trump if possible; beat the current winner within that suit if possible."""
    if not trick:
        return tuple(hand)
    lead = trick[0].card.suit
    winning = max((p.card for p in trick), key=lambda c: _strength(c, lead))
    pool = tuple(c for c in hand if c.suit == lead)
    if not pool:
        pool = tuple(c for c in hand if c.suit == TRUMP)
    if not pool:
        return tuple(hand)
    beating = tuple(c for c in pool if _strength(c, lead) > _strength(winning, lead))
    return beating or pool


def score_tenths(bid: int, tricks: int) -> int:
    """Exact score, expressed in integer tenths of a point."""
    if type(bid) is not int or not 1 <= bid <= 13:
        raise ValueError('Bid must be an integer from 1 to 13')
    if type(tricks) is not int or not 0 <= tricks <= 13:
        raise ValueError('Tricks must be an integer from 0 to 13')
    return 10 * bid + (tricks - bid) if tricks >= bid else -10 * bid


@dataclass(frozen=True)
class Trick:
    plays: tuple[Play, ...]
    winner: int


@dataclass(frozen=True)
class RoundResult:
    round_number: int
    dealer: int
    bids: tuple[int, ...]
    tricks_won: tuple[int, ...]
    score_tenths: tuple[int, ...]  # round delta, not cumulative
    tricks: tuple[Trick, ...]

    @property
    def scores(self) -> tuple[float, ...]:
        return tuple(s / 10 for s in self.score_tenths)


@dataclass(frozen=True)
class Observation:
    player: int
    phase: str  # 'bid' or 'play'
    round_number: int  # 1-based
    total_rounds: int
    dealer: int
    leader: int  # first leader during bidding; current leader during play
    trick_number: int  # 0 during bidding; 1–13 during play
    bids: tuple[int | None, ...]  # None = not yet called
    tricks_won: tuple[int, ...]
    score_tenths: tuple[int, ...]  # cumulative, completed rounds only
    current_trick: tuple[Play, ...]
    completed_tricks: tuple[Trick, ...]  # current round only
    legal_cards: tuple[Card, ...]  # empty during bidding
    previous_rounds: tuple[RoundResult, ...]
    hand_sizes: tuple[int, ...]

    @property
    def scores(self) -> tuple[float, ...]:
        return tuple(s / 10 for s in self.score_tenths)

    @property
    def played_cards(self) -> tuple[Play, ...]:
        return tuple(p for t in self.completed_tricks for p in t.plays) + self.current_trick

    @property
    def lead_suit(self) -> str | None:
        return self.current_trick[0].card.suit if self.current_trick else None

    @property
    def current_winner(self) -> int | None:
        return trick_winner(self.current_trick) if self.current_trick else None

    @property
    def turn_order(self) -> tuple[int, ...]:
        return tuple((self.leader + i) % 4 for i in range(4))

    @property
    def bid_order(self) -> tuple[int, ...]:
        return tuple((self.dealer + i) % 4 for i in range(1, 5))


class Bot(Protocol):
    def give_bid(self, cards: tuple[Card, ...], observation: Observation) -> int: ...
    def play_card(self, cards: tuple[Card, ...], observation: Observation) -> Card: ...


class IllegalAction(ValueError):
    """A bot returned an invalid bid or card."""


@dataclass(frozen=True)
class GameResult:
    score_tenths: tuple[int, ...]
    rounds: tuple[RoundResult, ...]
    winners: tuple[int, ...]  # all tied first-place seats

    @property
    def scores(self) -> tuple[float, ...]:
        return tuple(s / 10 for s in self.score_tenths)


def run_game(bots: Sequence[Bot], *, seed: int | None = None, rounds: int = 5,
             first_dealer: int | None = None) -> GameResult:
    """Run a complete game. Seats are indices 0–3, in increasing cyclic order.

    The seed controls deck shuffles and initial dealer, not bot randomness.
    Invalid actions abort immediately; bot exceptions propagate. No bot is reset
    or copied by the engine. Instantiate a fresh bot per seat/game if desired.
    """
    bots = tuple(bots)
    if len(bots) != 4:
        raise ValueError('Exactly four bots required')
    if type(rounds) is not int or rounds < 1:
        raise ValueError('rounds must be a positive integer')
    if first_dealer is not None and (type(first_dealer) is not int or first_dealer not in range(4)):
        raise ValueError('first_dealer must be a seat 0–3')
    rng = Random(seed)
    initial_dealer = rng.randrange(4) if first_dealer is None else first_dealer
    scores = [0] * 4
    results: list[RoundResult] = []
    for round_number in range(1, rounds + 1):
        dealer = (initial_dealer + round_number - 1) % 4
        leader = (dealer + 1) % 4
        deck = list(DECK)
        rng.shuffle(deck)
        hands = [sorted(deck[i::4], key=lambda c: (SUITS.index(c.suit), c.rank)) for i in range(4)]
        bids: list[int | None] = [None] * 4
        won = [0] * 4
        history: list[Trick] = []
        current: list[Play] = []

        def observe(player: int, phase: str) -> Observation:
            return Observation(player, phase, round_number, rounds, dealer, leader,
                               len(history) + 1 if phase == 'play' else 0,
                               tuple(bids), tuple(won), tuple(scores), tuple(current),
                               tuple(history), legal_cards(hands[player], current) if phase == 'play' else (),
                               tuple(results), tuple(map(len, hands)))

        for offset in range(4):
            player = (leader + offset) % 4
            bid = bots[player].give_bid(tuple(hands[player]), observe(player, 'bid'))
            if type(bid) is not int or not 1 <= bid <= 13:
                raise IllegalAction(f'Round {round_number}, seat {player}: invalid bid {bid!r}')
            bids[player] = bid
        for trick_number in range(1, 14):
            current = []
            for offset in range(4):
                player = (leader + offset) % 4
                obs = observe(player, 'play')
                card = bots[player].play_card(tuple(hands[player]), obs)
                if not isinstance(card, Card) or card not in obs.legal_cards:
                    raise IllegalAction(f'Round {round_number}, trick {trick_number}, seat {player}: '
                                        f'illegal card {card!r}; legal cards: {obs.legal_cards!r}')
                hands[player].remove(card)
                current.append(Play(player, card))
            winner = trick_winner(current)
            won[winner] += 1
            history.append(Trick(tuple(current), winner))
            leader = winner
        final_bids = tuple(int(b) for b in bids)
        deltas = tuple(score_tenths(b, t) for b, t in zip(final_bids, won))
        scores = [s + d for s, d in zip(scores, deltas)]
        results.append(RoundResult(round_number, dealer, final_bids, tuple(won), deltas, tuple(history)))
    best = max(scores)
    return GameResult(tuple(scores), tuple(results), tuple(i for i, s in enumerate(scores) if s == best))
