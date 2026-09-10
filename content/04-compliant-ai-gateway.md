A hospital, a bank, an insurer or a government department wants to use the same AI models
everybody else is using. The technology is not what stops it. What stops it is a meeting.

In that meeting, three people ask three questions. Privacy asks where the personal
information goes and who at the vendor can read it. Audit asks to be shown exactly what
was sent, on what date, by whom. Finance asks what happens if one team leaves a loop
running over a long weekend. None of these are research questions. They are plumbing
questions, and the honest answer in most organisations is that nobody knows, because the
plumbing was never built.

| What gets asked before the answer is yes | The usual answer | What that answer is missing |
|---|---|---|
| Where does personal information go? | A vendor contract, and a rule telling staff not to paste anything sensitive | Nothing enforces the rule. It lives in a training slide, and it is broken by the first person in a hurry |
| What exactly was sent, and when? | Application logs, if somebody remembered to add them | Logs are edited, rotated and switched off. An auditor needs a record that cannot be quietly changed, including by the operator |
| Which country did the request travel to? | A region chosen once at sign-up | Nothing checks it per request, and nothing refuses when a request carries data that is not allowed to leave |
| What did it cost, and which team spent it? | The vendor's monthly invoice | It arrives weeks late, as one number, attributed to nobody |
| How much slower does all of that make things? | Negligible | A figure nobody has measured |

This project builds the layer that answers all five, and treats the last row as the
deliverable rather than the disclaimer. Every one of those controls costs time. A claim
that the cost is small is worth nothing without a number, so the number is measured under
load, per control, and published whether or not it flatters the design.

It is built in two stages, in an order chosen on purpose.

First, a library. Every model call made anywhere in this portfolio goes through one piece
of code: one way to call any vendor, one place that decides which model you actually get,
one record of what a call cost, and a hard refusal when a budget is spent. Think of it as
the single door in the building. Everything that leaves goes through it, and everything
that leaves is written down.

Second, the gateway around that library: a server an organisation puts between its teams
and the model vendors. It speaks the same protocol the vendors speak, so an existing tool
moves onto it by changing one setting. On the way out it finds personal information and
replaces it with placeholders, and on the way back it puts the real values into the answer,
so the vendor never receives the data but the person asking still gets a useful reply.
Requests carrying sensitive classes of data can only reach approved providers and regions,
and a request that does not say what it is carrying is treated as the most sensitive kind
rather than the least. Every call lands in an audit log built so that changing it after the
fact is detectable. Every team has a budget the gateway enforces before the call, not after
the invoice.

One thing separates this from a demonstration of the same idea. It is not being tried out
on a toy workload. The library is the piece the rest of this portfolio already depends on,
so it is load-bearing before it is presentable: if it is wrong, other projects break, and
the record it keeps is the record their own results are checked against.

**Where this stands in September 2026: in progress.** The library is built, tested and
released internally, with its programming interface deliberately frozen early so that
another project in the portfolio could be written against it before it was finished. It is
already carrying real calls to four vendors. The full gateway, with redaction, residency
enforcement, the audit chain, the cache, team budgets and the published latency budget, is
built in May 2027. Nothing here is measured in public yet, and the results tables in the
repository are empty until it is. The repository becomes public when it has numbers in it.

<!-- more -->

## Why the library comes first, and why that is the harder choice

A proxy demonstrates better. It has a URL, it can be shown working in a minute, and it
looks like a product. A library looks like nothing at all.

The library came first because the portfolio has ten other projects and eight of them call
AI models. If each one called the vendors directly, three things follow. When a vendor
retires or reprices a model, and that happens most months, there are eight codebases to
edit. Nobody can say what the whole portfolio spent or on which project, because the
evidence is eight separate invoices. And the project that measures whether vendors quietly
change their supposedly frozen models could never rule out its own client code as the
cause of what it found.

The cost of that decision was paid immediately. The programming interface had to be frozen
two days into the build, before most of the implementation existed, because another
project's runner was written against it the following week. From that point changes are
additive only: new optional fields yes, renames or removals no. Freezing an interface
before you have finished learning what it needs is uncomfortable and it is the correct
trade when other work is already pinned to it.

## The order of operations is the design

One call runs through seven steps, and the order is the whole point.

Work out which model was actually asked for. Build the exact bytes to send. Check the
spending limits and refuse here if the limit would be passed, so that a refused call never
touches the network. Write the accounting record. Send. Read the reply and work out what
it cost. Complete the record, and return.

The record is written fourth, before anything leaves the machine, carrying a deliberately
overstated cost estimate. Kill the process halfway through the call and the record is still
there, marked as in flight, still holding that estimate against the budget. The ordinary
way round is to log after the reply arrives, which means the only calls that go
unrecorded are the ones that crashed, timed out or were killed. Those are precisely the
calls somebody will later need to account for.

## Money is never estimated after the fact

Cost comes from the token counts the vendor returns, multiplied by rates in a dated price
file copied from that vendor's own price page. Repricing is a new file with a new date,
never an edit to an old one, so a call made in September is still priced by September's
rates a year later. If a model is not in the price file, the record says uncosted. It never
says a guess. The same applies to a partial rate: a call that used prompt caching where the
file has no caching rate is uncosted rather than approximately costed.

That rule earns its keep in ways that are hard to predict in advance. On the first live
calls, one vendor answered a request for a model with a slightly different, dated name for
the same model. A system that guessed would have quietly mispriced or silently dropped
those calls. This one prices by the name the vendor returned, falls back to the name that
was requested, keeps both in the record so an auditor can see which one was used, and
guesses no further than that.

The pre-call estimate runs the other way on purpose. It assumes a pessimistic number of
tokens in and the full requested limit out, because a call refused slightly too early costs
nothing and an overspend costs money.

## Limits that refuse before the call, and are still the second line of defence

Three limits: what a project may spend this month, what a single run may spend, and a
ceiling across the whole portfolio. Each is checked against the running total in the
accounting record plus the pessimistic estimate for the call about to be made, and a
refusal happens before any request is sent.

They are documented as the second line of defence, not the first. The first is the hard cap
set in each vendor's own console, outside this code entirely. A budget control whose only
enforcement is the code that might have the bug is not a budget control.

## Two modes, and one of them cannot be touched

Everyday calls retry when a vendor returns a transient error, back off politely, and fill
in sensible defaults for anything not specified. That is what you want almost always.

It is exactly what you do not want when the call is a measurement. Another project in this
portfolio spends twelve months asking whether vendors change their pinned models behind a
fixed name. If the client library retried, or served an answer from a cache, or filled in a
value the caller did not set, the finding would be about the library and not the vendor.

So there is a second mode that does none of it: no retries, no cache, no rewriting of any
kind, no friendly aliases, and the model must be named exactly. Even supplying a default
token limit counts as rewriting and is refused rather than helpfully filled in. A vendor
error is returned as a result rather than raised as a failure, because in a measurement an
error is data. Every request and reply is kept, with the credentials stripped out, so the
run can be audited long afterwards.

None of that is enforced by a comment asking people to be careful. A test takes the bytes
the code handed to the HTTP client and compares them against the bytes the request builder
produced, and fails on any difference. Another test configures a cache and then proves that
a measurement call still made exactly one request to the vendor.

For the same reason there are no vendor software kits anywhere in the request path, only
plain HTTP with pinned protocol version headers. Vendor kits change their defaults between
releases: timeouts, retry behaviour, which fields get sent when you did not set them. Any
of those is a silent edit to a measurement, arriving through a routine dependency update
that nobody reviews as a change to the data.

## Telemetry that cannot leak a prompt

Every call emits one monitoring record carrying counts, costs, timings and identifiers,
and never the text of a prompt or an answer.

That is a common promise. Here the list of permitted fields is written into the code, and
the function that attaches a field refuses anything not on the list. Adding the prompt to
the monitoring record is not a lapse of judgement in code review, it is a program that
stops working. A test plants a fictional patient's name in a prompt and checks it appears
nowhere in the output.

## What the gateway adds in 2027

**It speaks the vendors' own protocol**, so an existing tool moves onto it by changing a
base address and a key. Adoption cost is close to zero, which is the only version of this
that a real team would install.

**The sensitivity of the data is declared, never inferred.** Each request states what class
of data it carries. A request that says nothing is treated as personal, which is the
restrictive reading, so the failure mode of a forgetful caller is refusal rather than
disclosure. A policy file maps each class to the providers and regions it may reach and to
the protections it must pass through. The gateway never inspects content to decide the
class, because a system that guessed would be making a compliance judgement that no human
signed.

**Redaction is reversible.** Detected names, identifiers and places become consistent typed
placeholders, so the same person is the same placeholder throughout one request. The
mapping back lives in a short-lived, encrypted, per-request store that the audit log never
sees. The reply is rehydrated on the way back. Models sometimes mangle placeholders, and
that rate is measured and published, because it is the honest limit of the approach and the
first thing an informed buyer will ask about.

**The recognisers are Canadian**, which public tooling largely is not: social insurance
numbers checked against their checksum, provincial health numbers, postal codes, and a
gazetteer of Newfoundland and Labrador place and organisation names. Precision and recall
are reported for each entity type separately, with intervals, because a single average
figure hides the categories that fail.

**The audit log is hash-chained and anchored in public.** Each record includes the hash of
the record before it, so the log is a chain rather than a list, and altering any earlier
entry breaks every entry after it. Once a day the current end of the chain is committed to
a public repository. That is the part worth pausing on: it makes tampering by the
organisation running the gateway detectable by anyone, not just tampering by an outsider.
An audit trail that the operator can rewrite is not an audit trail, and almost every audit
trail is one.

**The cache is published with its risk beside its saving.** Repeated questions can be
answered from a store of previous answers, which saves real money. It can also answer a
subtly different question with the confidence of an exact match, which is worse than having
no cache. So the saving is reported next to the rate at which that happens, measured by
hand-labelling a sample of the cache's own hits. It is switched off entirely for personal
and sensitive data.

**Injection screening is advisory by default.** Content that looks like an attempt to
hijack the model is flagged in the audit record rather than blocked, because blocking has a
false-positive cost that belongs to the policy owner rather than to the vendor of the tool.

**The dashboard is public.** A read-only view of every project in this portfolio, showing
calls, latency, errors and cost broken down by project, model, provider and day. Next to it
sits the panel that matters more: a comparison of how many calls the central record holds
against how many each individual machine's own record holds. Dashboards are usually shown
to be full. This one is shown to be complete, which is a different and much stronger claim,
and the gap between the two numbers is published rather than hidden.

**The latency budget is published before the feature list grows.** The overhead is measured
against a stand-in vendor with a fixed response time, with the protections switched on one
at a time, at three levels of load, several runs each, with intervals across runs. The
budget is set from the first measurement in the first week, so the budget constrains the
architecture instead of the architecture excusing the budget. Whatever the final figures
are, those are the figures that get published.

## Does redaction make the answers worse

This is the question a buyer asks second, right after the privacy question, and it is
almost never answered. Removing names and numbers from a prompt might well degrade the
reply, and any honest version of this product has to say by how much.

It gets answered with another project from this portfolio: the release gate, pointed at
this gateway. The same questions are put through redacted and unredacted, paired item by
item, tested for whether the redacted side is worse by more than a stated tolerance rather
than for whether it happens to score higher. The measuring instrument is the same one every
other project in the portfolio uses, which is the point of building it first.

## What this deliberately does not do

Stated here as plainly as it is stated in the repository, because the omissions are part of
the design and a reader who finds them later has been misled.

It does not decide what is sensitive. The caller declares it and the gateway enforces the
policy for that declaration.

It does not run in more than one region. Residency here means controlling where a request
is allowed to go, not where the gateway itself runs. A multi-region deployment is
integration work with no measurement attached.

It handles text. Images and audio cannot be redacted here, so they are refused for anything
other than public data rather than waved through.

Redaction is not perfect. Nothing that finds personal information in free text is perfect,
and the results table says how imperfect, per entity type, with intervals.

## Why one command matters

Eight years of production machine learning inside health and government is real work that
an outsider cannot verify. The portfolio exists to fix that, and the standard is the same in
every project: a stranger clones the repository, runs one command, and gets the same table.
Here that means the latency overhead regenerated by a benchmark rather than typed, the
accounting record checked against a real vendor invoice, the redaction scores carrying
intervals per entity type, and the audit chain verifiable by a stranger against anchors
published in public. In this repository a bare number without an interval is treated as a
defect.
