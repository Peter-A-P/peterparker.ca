Every team that uses AI models answers the same two questions on a schedule. Which model
should we be using? And when the vendor ships a new version, did anything get worse?

The standard way to answer is a benchmark: a few thousand questions with known answers, put
to every model on the shortlist, counted up into a percentage. It works. It is also slow
and expensive in a way that quietly changes behaviour. Three thousand questions across
twenty models is sixty thousand paid calls, and it has to be repeated every time any vendor
ships anything. Teams that intend to re-check monthly end up re-checking twice a year, and
in between they are guessing.

Underneath that sits a second problem, and it is the more interesting one. Most of those
questions are not doing any work.

| What a question does | What it tells you about which model to buy | What a percentage score does with it |
|---|---|---|
| Every model gets it right | Nothing. It separates nobody | Counts it, at full weight |
| Every model gets it wrong | Nothing. It separates nobody | Counts it, at full weight |
| Its stored answer key is wrong | Worse than nothing: it penalises the models that were right | Counts it, at full weight |
| It leaked into training data | Measures memory, not capability | Counts it, at full weight |
| It cleanly separates stronger models from weaker ones | This is the entire signal you are paying for | Counts it, at full weight |

A total score treats all five rows as equal evidence, because a total score cannot tell
them apart. Nobody knows which of a benchmark's questions belong to which row, because
results are published as one aggregate and the per-question detail is thrown away.

Standardised testing solved this decades ago. The GRE, professional licensing exams and
school assessments stopped handing everybody the same fixed paper long ago: they measure
each question first, then give each candidate the questions that tell them the most. The
statistics behind that is called item response theory, and pointed at a language-model
benchmark the arithmetic does not care that the candidates are models. Each question gets
two measured properties instead of one: how hard it is, and how sharply it separates
ability just above its threshold from ability just below. Each model gets one ability
number on the same scale, with a confidence interval around it.

Once every question has been measured, the test can be short. Ask the question that tells
you the most about this particular model, update the estimate, ask the next one, and stop
when the interval is tight enough to decide. For the question a platform team actually
asks, "is the new version worse than the one we are running", the stopping rule is sharper
still: stop the moment the two models' intervals no longer overlap, because from that point
every further call is spent proving something already proven. If the intervals still
overlap when the budget runs out, the honest report is that these two models are not
distinguishable at that budget, which is a real answer rather than a decimal place nobody
should be trusting.

This project builds that, and then tries to break it. Calibration happens once, mostly on
public data that already records which model got which question right. The claim to be
tested is that about a tenth of the questions, chosen adaptively, reproduce the ranking the
full benchmark produces. That is either true on a chart with confidence intervals on it or
it is not, and the chart is the deliverable either way, drawn next to the two baselines
that would make it worthless: the same number of questions picked at random, and the same
number picked by stratified sampling. The by-product is a named, evidenced list of the
benchmark questions that were never measuring anything.

**Where this stands: planned, and nothing has run.** The build window is the four weeks of
November 2026, and the full plan is written and published in the repository before any of
it starts. There is no result on this page because there is no result yet. The repository
turns public when the table has real numbers in it.

<!-- more -->

## Two numbers per question, not one

The property everybody already uses is difficulty: what share of models get this question
right. On its own it is not enough, because it says nothing about whether the models
getting it right are the good ones.

The second property is discrimination, and it is what decides whether a question is worth
its price. A high-discrimination question behaves like a clean threshold: models below a
certain ability nearly always miss it, models above it nearly always get it. A
low-discrimination question is closer to a coin flip for everybody, so it moves scores
around without carrying information. And a question with negative discrimination, where
stronger models do worse on it than weaker ones, is usually not a hard question at all. It
is a question whose stored answer is wrong.

Multiple-choice questions get a third property, the floor set by guessing: with four
options, a model that knows nothing still scores about 25 percent, and a method that
ignores that misreads the bottom of its own scale. This is the standard two-parameter and
three-parameter formulation, fitted here with the guessing parameter held at zero for
free-response questions, where the data cannot identify it and estimating it anyway makes
the fit worse. That is one of the candidates for the portfolio's rule that every project
publishes something that did not work, with the evidence.

## The expensive part is already public, and already paid for

Fitting those properties needs a large grid: many models by many questions, each cell
recording right or wrong. Running that grid from scratch would cost more than the project
is worth.

It does not have to be run from scratch. Two public sources already publish per-question
results rather than only totals: the Hugging Face Open LLM Leaderboard detail datasets and
HELM's per-instance predictions, together covering hundreds of models across
multiple-choice, mathematics and mixed-format suites. The target grid is at least 100
models by 3,000 to 5,000 questions, with questions identified by a hash of their text so
that the same question arriving from two sources collapses into one row, and a question
kept only where at least 40 models have answered it. Week one of the build is spent
verifying that those datasets are still where they were and still in a usable shape, with a
smaller fallback grid written down in advance in case they are not.

Which means the budget is not spent on calibration at all. It is spent on the part that
actually tests the claim.

## Testing the claim in two layers, one of them adversarial

**The simulation.** Take one model out of the grid entirely. Refit every question's
properties without it, so that nothing about that model can influence the questions it is
about to be asked. Then run the adaptive test against its already-recorded answers, and
record the ability estimate and its interval after every single question. Repeat for every
model in the grid. The rankings produced at 30 questions, at 100, at 300 can then each be
compared against the full-suite ranking with a standard rank-agreement statistic, with a
bootstrap interval taken over models. That curve, agreement against number of questions
used, is the headline.

A curve on its own would prove very little, which is why the two baselines are drawn on the
same axes. Randomly chosen questions probably also reproduce the ranking on average; the
expected difference is in the variance from draw to draw, and in the fact that random
selection has no principled way of saying when it has seen enough. Showing that gap is the
point of the exercise. If the gap is not there, that is the finding, and it gets published
too.

**The live check.** Simulation shares one weakness with every other retrospective study:
the models were in the data. So a panel of eight to ten current models that the calibration
never touched, spanning three major vendors, open-weights models served by a provider, and
small models running locally on a laptop, is run twice. Once the expensive way, every
question, to get a ground-truth ranking. Once adaptively, using only the question
properties calibrated from the public grid. If the two rankings agree, the method transfers
to models that did not exist when the questions were measured, which is the only version of
the claim worth anything to a team choosing a model next quarter.

The small local models are there for a statistical reason as well as a cheap one.
Calibration needs the ability range to be wide, and a panel of frontier models alone leaves
the bottom of the scale unmeasured and the question properties unstable.

## What a percentage was hiding all along

Three deliberately small experiments run on the same panel, each measuring something a
single accuracy figure cannot express.

**Test-retest.** The same model, the same 500 questions, run twice a day apart, with
randomness turned down as far as the vendor allows. Whatever moves between those two runs
is noise, and it sets the floor under every "the new version dropped two points" claim
anyone will ever make about that model. Almost nobody publishes this number.

**Position bias.** Three hundred multiple-choice questions with the options rotated so that
the correct answer occupies each position in turn. The output is the share of results that
flip purely because the right answer moved from A to C, model by model. Where that share is
large, part of the published leaderboard is a formatting artefact.

**Framing.** The same questions under three prompt templates, with the variation in
correctness split between the question, the template, and the interaction of the two. This
also puts a number on what this project's own answer-only output format costs, which is the
honest way to report a design decision that was made for cost reasons.

## The assumption underneath, measured rather than waved away

Item response theory assumes that once you know a model's ability, its answers are
independent of one another, and that a single ability explains the whole test. Benchmarks
break both assumptions. Questions sharing a passage or a setup are correlated with each
other. Reasoning about mathematics is not the same capability as following formatting
instructions.

The choice is between assuming that away and measuring it. This project measures it: a
residual-correlation statistic that finds locally dependent pairs of questions, reported as
a distribution rather than a headline, and a dimensionality check that compares one shared
ability against separate abilities per benchmark. If the benchmarks do not sit on one
dimension, the write-up reports the composite alongside the per-benchmark abilities and
says so in plain terms. The repository's own working rules put it bluntly: report local
dependence and dimensionality, never hide them, they are the interesting section.

There is a practical consequence for the project this one feeds. If some questions are not
independent evidence, then confidence intervals that treat them as independent are too
narrow, and a release gate built on them would be quietly overconfident. The list of
dependent question blocks is part of the handover for exactly that reason.

## Finding the questions that leaked

Contamination has a measurable signature once questions are calibrated. Compare how a
question behaves for models released before it was published against models released after
it was published, holding general ability constant. A question that is anomalously easy for
the later models, beyond what their overall ability predicts, is a candidate. In
psychometric terms this is differential item functioning by release date: the same
machinery that detects an exam question unfairly easier for one group of candidates than
for another group of equal ability.

The same test is run across open-weights and API model families, which asks a different
question: whether parts of a benchmark are measuring something about a family's training
style rather than about capability.

Flagged questions are not published on the strength of a statistic alone. A sample is read
by a person before anything enters the broken-question report, because a bug in the answer
extractor looks exactly like a badly behaved question, and shipping the first as the second
would be the most embarrassing available outcome for a project about measurement error.

## The number a platform team can act on

The end product is not a ranking, it is a function. Given the size of regression a team
cares about, the confidence they want in the answer, and roughly where their model sits on
the ability scale, it returns how many questions they need to run. Detecting a three-point
drop is a different budget from detecting a one-point drop, and until now that has been
guesswork.

That function, with the calibrated question bank and the adaptive estimator beside it, is
handed over as a versioned package to the AI Release Gate, the next project in this
portfolio, which uses it to size its own regression tests. This is the piece of that system
that answers "how many evaluation questions does this test actually need", and it is why
this project is built before that one rather than after it.

## What it deliberately does not do

It scores questions that are right or wrong, and nothing else. No writing quality, no human
preference, and no second model acting as a judge, because the psychometrics rests on a
correct-or-not response and a judge would add a second, drifting instrument to the
measurement. It calibrates existing benchmark questions rather than writing new ones. It
ships as a package, a results table and a write-up, not as a hosted service. And the
frontier-tier models are run only on the short adaptive subset, because paying full price
for the most expensive models on all three thousand questions would be an odd way to
demonstrate a project about not doing that.

The ratio itself is reported as measured. If the honest answer turns out to be a seventh of
the calls rather than a tenth, the chart says a seventh, and it is the project's name that
is wrong rather than its number.

## Why one command matters

Eight years of production machine learning inside health and government is real work that
an outsider cannot verify. The portfolio exists to fix that, and the standard is the same in
every project: a stranger clones the repository, runs one command, and gets the same table.
Here that means a content-hashed question bank frozen at a version, question properties
stored next to the fit that produced them, every vendor response cached so that a rerun
costs nothing, and an interval on every figure reported. In this repository a bare number is
treated as a defect.
