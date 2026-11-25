# Research overview

This is a summary of the initial researcher-led mathematical investigation, with AI assistance for calculations and documentation. It is not a replacement for the detailed research journal or a record of experimental validation.

## CB-001 — Initial suit voids

Suppose my 13-card hand contains `k` cards of a particular suit, leaving `m = 13 - k` cards of that suit among the other 39 cards. Under a uniformly random initial deal, the positions occupied by those `m` cards form a uniformly random subset of the 39 opponent card positions.

By inclusion-exclusion, the probability `p(k)` that at least one opponent has no cards of that suit is

```math
p(k)=\frac{3\binom{26}{m}-3\binom{13}{m}+\binom{0}{m}}{\binom{39}{m}}.
```

Here a binomial coefficient is zero if its lower argument exceeds its upper argument, and `C(0,0)=1`. This is an exact initial-deal probability, not the probability that an Ace actually loses to a trump. A void opponent may not have a trump, and a player who is not initially void can become void later. The analysis is most relevant to non-trump suits.

## CB-002 — Ace bidding model (provisional)

Suppose I expect exactly `b` other tricks and have one additional Ace whose trick succeeds with probability `1-p`. Compare keeping bid `b` with increasing it to `b+1` (for `1 <= b <= 12`).

Under this simplified binary-outcome model:

```math
E[S_b]=b+0.1(1-p),\qquad E[S_{b+1}]=(1-p)(b+1)-p(b+1).
```

Increasing the bid is favorable when

```math
p<\frac{0.9}{2b+1.9}.
```

Using the initial-void probability as a *proxy* for the Ace's failure probability produces preliminary counting guidance for non-trump Aces. The actual failure probability, uncertainty in the other tricks, and the effect of play strategy need investigation. This is not a validated bidding rule. Prior research deferred bid 8 and above.

## CB-003 — King bidding model (provisional)

One working hypothesis for a non-trump King is to consider the event that all three opponents start with at least two cards of its suit. With `m = 13-k`, its exact initial-deal probability is

```math
q(k)=\frac{\sum_{a+b+c=m,\ a,b,c\ge2}\binom{13}{a}\binom{13}{b}\binom{13}{c}}{\binom{39}{m}}.
```

This counts allocations of the remaining suit cards among the three opponents. It is not the exact chance of winning a trick with the King: the position and timing of the Ace, trump availability, and decisions during play matter.

If `q` is provisionally treated as the success probability of a single King, the same expected-value comparison as the Ace model gives

```math
q>\frac{2b+1}{2b+1.9}
```

as the condition for increasing the bid from `b` to `b+1`. The event probability is exact under random dealing; its use as a trick-win probability is a hypothesis to test.

## Multiple uncertain cards — open investigation

A King that does not individually justify an extra bid may still do so when considered jointly with another King. The next question is how to estimate the probability of winning at least one trick with several uncertain cards. Multiplying individual failure probabilities would require independence, which cannot be assumed automatically because the cards are dealt without replacement and play decisions may interact.

The combined model and its use in a bot are still under investigation.

## Validation questions

- How different are initial-deal suit-void probabilities from observed Ace failure rates?
- How well does the King proxy predict actual trick wins?
- What happens when the number of other tricks is uncertain rather than fixed?
- How do card-play order, public bids, opponent strategies and card-counting information change the estimates?
- Do these bidding rules improve expected score and overall game win rate in repeated simulations?

No simulation-based answers to these research questions are claimed yet.
