Every organisation that spends money on people has to pick which people. A retention
offer, an outreach call, a transaction pulled for manual fraud review, a clinical
follow-up: the budget covers a fraction of the population, so somebody chooses the
fraction.

The last two look different from the first two and are the same problem. An analyst hour
spent on a transaction is worth spending only if the review changes what happens to it,
and most reviews do not: the blatant fraud is stopped by the automated rules anyway, and
the clean transaction was never going to be a loss either way. A follow-up call after
discharge is worth making only if it is the call that keeps the patient out of hospital,
not when they would have been readmitted whatever anyone did, or were never going back in.
In all four, the budget buys a fixed number of actions, and most of those actions land on
people whose outcome was already settled. The normal way to choose who gets them is to
rank everyone by risk and treat the top of the list.

That is the wrong list. It is wrong in a way that is easy to miss, because it still
produces a report that looks fine.

Ranking by risk finds the people most likely to have the bad outcome. It does not find the
people whose outcome the intervention would change. Those are different groups. Sort a
population by what the intervention actually does to each person and there are four kinds
of people:

| | If nobody acts | If somebody acts | Worth the budget |
|---|---|---|---|
| **Persuadables** | bad outcome | good outcome | Yes. They are the entire return. |
| **Sure things** | good outcome | good outcome | No. They were fine already. |
| **Lost causes** | bad outcome | bad outcome | No. Nothing on offer helps. |
| **Sleeping dogs** | good outcome | bad outcome | No. Acting does damage. |

A risk model ranks people by the first column alone. It puts lost causes near the top,
because they really are the highest risk, and it has nothing at all to say about whether
the phone call helps. Persuadables sit in the middle of a risk ranking and get missed. And
a risk model cannot see sleeping dogs, so a campaign can spend its budget making outcomes
worse and still report a healthy response rate.

This project builds the machinery for ranking on the second question instead, "would
acting change this person's outcome", and for the part that usually gets skipped: showing
that the ranking is real rather than plausible. It ends in one results table, regenerated
by one command, that reports for every method how much outcome a fixed budget actually
buys, with a confidence interval, against two baselines: random targeting, and the
risk-ranking approach above. A slider on the demo page moves the budget and the
intervention list re-ranks, because "who do we treat" has a different answer at 10 percent
of the population than at 30.

**Where this stands: week 6 of 8.** All five datasets are benchmarked with seven methods
against both baselines, every score carrying a bootstrap interval, from one command.

The headline is a result the project was built to find and did not expect to be
conditional. At a budget covering the top 10 percent, the same risk-ranking baseline,
produced by the same code, buys **-0.20 on one dataset and +0.0055 on another**, against
random targeting's +0.26 and +0.0008. On the first it is worse than spending nothing, with
a confidence interval entirely below zero, and that is confirmed against the individual
effects the dataset was simulated from: the true mean effect on the people it targets is
negative, while the naive comparison of arms reports a healthy positive number. On the
second it matches every uplift model in the table and beats random targeting sevenfold.

So the honest claim is not "the intervention list is never the risk list". It is that the
two lists differ by an amount nobody can guess in advance, that the cost of assuming they
agree runs from nothing to worse than doing nothing, and that a single cheap diagnostic
settles which case you are in before anybody fits a model. The build window runs to the
start of November 2026, and the repository turns public with the full table in it.

<!-- more -->

## Why this is harder than a normal model

For any one person, only one of the two outcomes ever happens. You either sent the offer
or you did not, so you see either the treated outcome or the untreated one, never both.
The quantity this project estimates, the difference the intervention made to that
individual, is therefore missing for every individual in the data. It is not scarce or
noisy. It is absent, always, by construction.

That is why the usual machine-learning reflex does not work here. You cannot hold back a
test set and check predictions against the truth, because the truth was never recorded.
Any approach that claims otherwise is measuring something else, usually its own internal
consistency.

## How you check it anyway

Two kinds of data, doing two different jobs.

**Randomised data**, where the treatment was assigned by coin flip: three public marketing
and messaging experiments, the largest with 13.9 million rows. Individual truth is still
missing, but because assignment was random, group averages are trustworthy. That is enough
to answer the practical question: if we had followed this ranking at this budget, what
outcome would we have got?

**Simulated data**, where the effect was generated from a known formula: two standard
benchmark sets from the causal-inference literature. Here the individual truth exists
because somebody wrote it, so per-person error can be measured directly. This is the only
way to show that an estimator is correct rather than merely self-consistent, which is why
both kinds are in the benchmark and why neither is a substitute for the other.

## Several ways of estimating the same thing

The field has no single agreed method, so the project implements the main families behind
one shared interface and puts them in one table. Five are meta-learners: recipes that
build an effect estimate out of ordinary prediction models, differing in how they handle
the missing half of the data and in how they behave when the treated group is much smaller
than the untreated one. One is Dragonnet, a neural network written in PyTorch, included
deliberately as a test of whether the extra machinery earns its keep on problems this
size. A causal forest, which splits on differences in effect rather than differences in
outcome, is a stretch goal.

The five meta-learners sit on the same LightGBM base learner, so differences between those
columns are differences between the methods rather than differences between their engines.
Dragonnet cannot honour that rule, because a neural architecture is the thing being tested,
and the write-up says so rather than quietly comparing it anyway: the gap between it and a
meta-learner confounds the architecture with the function class underneath it.

**The verdict it was included for.** Competitive, not a breakthrough. It has the best
ranking score on three of the five datasets, sits fourth of seven on another, and is last of
seven on the fifth, where its realised gain is the weakest of the modelled rankings and its
interval covers zero while the five meta-learners' just exclude it. On the one dataset where
individual truth exists and it ranks best, it is also among the worse estimators of the effect
itself, which is the ordinary reminder that ranking well and estimating well are different
jobs. Two caveats hold the wins back, and they pull opposite ways: the comparison is not clean,
for the reason above, but the handicap is smaller than it looks, because it runs at published
defaults where the others get a tuning search and the project separately measured that the
tuning search buys nothing. The write-up that ships with the repository says where every method breaks,
which is usually the more useful half of a comparison.

## The trap the project is built around

The standard score for this kind of model is the Qini coefficient, drawn as a curve: sort
everyone by predicted effect, walk down the list, and plot the cumulative gain against
what random targeting would have given you. It is a good diagnostic and a poor referee,
because a plain risk model, the wrong list from the top of this page, often scores
respectably on it.

So every ranking in the results table is shown next to that risk-ranking baseline and next
to random targeting, and the headline number is not the curve but the realised policy
value: the outcome you would actually have obtained, estimated on held-out data by two
independent methods, from following the policy at a stated budget. Where a ranking looks
good on the curve and buys nothing in practice, the table says so. Demonstrating that gap
is the point of the repository, not a caveat inside it.

Every metric carries a bootstrap confidence interval. In this repository a score reported
without one is treated as a defect.

## From a ranking to a decision

A ranked list is not yet an allocation. Two allocation rules are implemented: take the top
N when every intervention costs the same, and solve for the best affordable combination
when costs differ per person, which is the usual situation once a fraud review costs an
analyst an hour and an automated message costs a fraction of a cent.

## How wrong can the assumptions be

On data that was not randomised, targeting rests on an assumption that everything relevant
was measured. That assumption is never quite true, and it cannot be tested from the data
itself. Rather than assume it away, the project quantifies its fragility with three
devices, and is careful about what each one answers. One asks how strongly a hidden factor
would have to be associated with both the treatment and the outcome to move the measured
effect to zero, which is the point at which the decision flips. One asks how far it would
have to shift the odds of being treated before the result stops being statistically
distinguishable from nothing, which is a weaker question and is reported as such rather
than conflated with the first. The third runs the whole pipeline on a quantity the
treatment cannot possibly have changed, where the right answer is zero and anything else is
the machinery inventing an effect.

Only the third can fail, and on these five datasets none of them do, which the write-up
reports as a limitation rather than as reassurance: two of the datasets were randomised, so
there is nothing hidden to find, and the confounding in the others runs entirely through
variables that were recorded. A device that cannot fail on the data you have is not
evidence that it works. The only evidence offered is a test that plants a hidden confounder
on purpose and requires the check to catch it. None of this removes the assumption, and the
repository says so plainly in its limitations.

## Why one command matters

Eight years of production machine learning inside health and government is real work that
an outsider cannot verify. The portfolio exists to fix that, and the standard is the same
in every project: a stranger clones the repository, runs one command, and gets the same
table. Here that means committed data checksums and split seeds, a tuning grid identical
across every method so that none of them gets a private advantage, and a results table
that is regenerated rather than typed.
