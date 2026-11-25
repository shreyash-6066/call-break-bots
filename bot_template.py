from callbreak import Card, Observation


class MyBot:
    def give_bid(self, cards: tuple[Card, ...], observation: Observation) -> int:
        raise NotImplementedError('Implement your bidding strategy here')

    def play_card(self, cards: tuple[Card, ...], observation: Observation) -> Card:
        raise NotImplementedError('Implement your playing strategy here')
