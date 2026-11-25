import unittest
from random import Random
from callbreak import Card, DECK, IllegalAction, Play, legal_cards, run_game, score_tenths, trick_winner


def C(rank, suit):
    return Card(rank, suit)


class TestBot:
    """Random legal actions only, for testing the engine, not a competitive bot."""
    def __init__(self, seed):
        self.rng = Random(seed)
        self.calls = []

    def give_bid(self, cards, observation):
        assert len(cards) == 13 and observation.phase == 'bid'
        assert observation.legal_cards == () and observation.bids[observation.player] is None
        self.calls.append((cards, observation))
        return self.rng.randint(1, 13)

    def play_card(self, cards, observation):
        assert observation.phase == 'play' and observation.legal_cards
        assert set(observation.legal_cards) <= set(cards)
        self.calls.append((cards, observation))
        return self.rng.choice(observation.legal_cards)


class EngineTests(unittest.TestCase):
    def test_deck(self):
        self.assertEqual(len(set(DECK)), 52)
        with self.assertRaises(ValueError):
            Card(1, 'S')

    def test_follow_and_beat(self):
        h = [C(2,'H'), C(12,'H'), C(14,'H'), C(14,'S')]
        t = [Play(0, C(10,'H'))]
        self.assertEqual(legal_cards(h, t), (C(12,'H'), C(14,'H')))
        self.assertEqual(legal_cards(h, t+[Play(1, C(13,'S'))]), tuple(h[:3]))
        self.assertEqual(legal_cards([C(2,'H'), C(14,'S')], t), (C(2,'H'),))
        self.assertEqual(legal_cards(h, []), tuple(h))

    def test_trump_and_discard(self):
        h = [C(2,'S'), C(12,'S'), C(14,'D')]
        t = [Play(0, C(10,'H'))]
        self.assertEqual(legal_cards(h, t), tuple(h[:2]))
        self.assertEqual(legal_cards(h, t+[Play(1, C(10,'S'))]), (C(12,'S'),))
        self.assertEqual(legal_cards(h, t+[Play(1, C(13,'S'))]), tuple(h[:2]))
        self.assertEqual(legal_cards([h[2]], t), (h[2],))
        self.assertEqual(legal_cards(h, [Play(0, C(10,'S'))]), (C(12,'S'),))

    def test_winner(self):
        t = [Play(3,C(10,'H')), Play(0,C(14,'D')), Play(1,C(11,'H'))]
        self.assertEqual(trick_winner(t), 1)
        self.assertEqual(trick_winner(t+[Play(2,C(2,'S'))]), 2)
        self.assertEqual(trick_winner([Play(0,C(5,'S')), Play(1,C(7,'S'))]), 1)

    def test_scoring(self):
        self.assertEqual(score_tenths(3, 5), 32)
        self.assertEqual(score_tenths(4, 4), 40)
        self.assertEqual(score_tenths(5, 4), -50)
        self.assertEqual(score_tenths(13, 13), 130)
        with self.assertRaises(ValueError):
            score_tenths(0, 5)

    def test_game_and_observations(self):
        bots = [TestBot(i) for i in range(4)]
        result = run_game(bots, seed=19, first_dealer=2)
        self.assertEqual(len(result.rounds), 5)
        self.assertEqual([r.dealer for r in result.rounds], [2,3,0,1,2])
        self.assertEqual(result.score_tenths, tuple(sum(r.score_tenths[p] for r in result.rounds) for p in range(4)))
        self.assertEqual(result.winners, tuple(p for p in range(4) if result.score_tenths[p] == max(result.score_tenths)))
        for r in result.rounds:
            self.assertEqual(len(r.tricks), 13)
            self.assertEqual(sum(r.tricks_won), 13)
            self.assertEqual(set(p.card for t in r.tricks for p in t.plays), set(DECK))
            self.assertEqual(r.score_tenths, tuple(score_tenths(b, t) for b,t in zip(r.bids,r.tricks_won)))
            leader = (r.dealer+1)%4
            for t in r.tricks:
                self.assertEqual(tuple(p.player for p in t.plays), tuple((leader+i)%4 for i in range(4)))
                self.assertEqual(t.winner, trick_winner(t.plays))
                leader = t.winner
        for seat, bot in enumerate(bots):
            self.assertEqual(len(bot.calls), 70)
            for cards, obs in bot.calls:
                self.assertEqual(obs.player, seat)
                self.assertEqual(obs.hand_sizes[seat], len(cards))
                self.assertEqual(len(obs.previous_rounds), obs.round_number-1)
                self.assertEqual(obs.score_tenths, tuple(sum(r.score_tenths[p] for r in obs.previous_rounds) for p in range(4)))
                self.assertEqual(len(obs.played_cards), 52-sum(obs.hand_sizes))
                self.assertFalse(set(cards) & {p.card for p in obs.played_cards})
                if obs.phase == 'bid':
                    self.assertEqual(sum(b is not None for b in obs.bids), obs.bid_order.index(seat))
                else:
                    self.assertEqual(obs.legal_cards, legal_cards(cards, obs.current_trick))
                    self.assertEqual(obs.turn_order[len(obs.current_trick)], seat)
                    self.assertEqual(len(obs.completed_tricks), obs.trick_number-1)
                    self.assertEqual(sum(obs.tricks_won), len(obs.completed_tricks))
                self.assertFalse(hasattr(obs, 'hands'))

    def test_reproducibility_and_many_games(self):
        def run(seed):
            return run_game([TestBot(i) for i in range(4)], seed=seed)
        self.assertEqual(run(7), run(7))
        self.assertNotEqual(run(7), run(8))
        for seed in range(100):
            result = run(seed)
            for r in result.rounds:
                self.assertEqual(sum(r.tricks_won), 13)
                self.assertEqual(len({p.card for t in r.tricks for p in t.plays}), 52)

    def test_illegal_actions(self):
        class BadBid(TestBot):
            def give_bid(self, cards, observation): return True
        class BadCard(TestBot):
            def play_card(self, cards, observation): return 'AS'
        for bot in [BadBid(1), BadCard(1)]:
            with self.assertRaises(IllegalAction):
                run_game([bot]+[TestBot(i) for i in range(3)], seed=1)
        with self.assertRaises(ValueError):
            run_game([])


if __name__ == '__main__':
    unittest.main()
