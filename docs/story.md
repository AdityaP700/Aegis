"Let me tell you about Aegis — it's a reliability wrapper I built for tool-calling agents.

The problem I was solving is simple but real. When you connect an LLM to external tools — like weather APIs or GitHub — the LLM makes mistakes. It routes to the wrong tool. It hallucinates arguments. It returns broken JSON. Most demos just ignore this and say 'look, it calls tools!' But in production, those failures mean a broken user experience.

So I designed Aegis with one philosophy: the LLM will fail, so the system must not.

Here's how it works.

A user asks something like 'What's the weather in Delhi?' That natural language query hits the Brain — which is an LLM-powered router. But instead of just throwing a prompt at the model, I built a Prompt Builder that generates structured prompts from rules and tool metadata. That means prompts are testable and version-controlled, not magic strings.

The LLM returns a plan — what tool to use, what arguments, and how confident it is. But I don't trust it yet.

First, the Intent Parser cleans up whatever garbage the LLM might have returned — markdown wrapping, trailing commas, malformed JSON. If parsing fails completely, the system doesn't crash. It falls back to web search with the original query. That's graceful degradation — an imperfect answer beats no answer.

Then comes the Validator — and this is where the real engineering is. It runs five checks. Does the tool exist? Are required arguments present? Are the types correct? And critically — does this tool even make sense for what the user asked? I use domain-specific signal words to catch semantic mismatches. If the user mentions 'stars' and 'repository' but the LLM chose the weather tool, the validator catches that and feeds the error back to the LLM for a retry.

Only after validation passes does the plan reach the Executor. The Executor doesn't know anything about specific tools — it just routes to the registry and invokes the right one with built-in retry and timeout logic.

The result is a system where the LLM can be wrong, but the user never sees a crash. Every failure degrades gracefully, every execution is traced, and the architecture is completely provider-agnostic — swap Groq for Claude without touching the pipeline.

That's Aegis. It's not just 'LLM calls tools.' It's 'LLM calls tools reliably


text
evals/loader.py          ← Where load_cases is DEFINED
evals/__init__.py        ← Imports it for convenience
test script              ← Uses from evals import load_cases
It's like a store front:

Warehouse (loader.py) — where items are made

Storefront (__init__.py) — where customers pick up items

Customer (your script) — buys from storefront, not warehouse directly

## load cases
load_cases is a factory function — it creates many EvalCase objects. If it were inside the class, you'd need an instance to call it, which doesn't make sense when you're trying to create the first instance.

## Property
Think of a Property as a "Secretary" that you hire for your object.Instead of you digging through filing cabinets yourself, you just ask the secretary for the information. The secretary does the work behind the scenes and hands it to you instantly.

## why LLM provider??
The LLM is the semantic interpreter. Everything else in Aegis is the safety net around it.

## Problem :
Aegis does catch the capability mismatch. It rejects the plan. But it forgets to write down that it rejected it.
Person tries to enter → Bouncer says "No, you're underage" → Person leaves

## latencies :
there are a few metrics through which we determine how's the overall and generic experience

one of the ways is to calculate the
p50 median ,where we determine the typical experience of the user "lets say most users wait X ms ,

another way is to be more specific and representative and that could be calculated using the p95 :

- where we usually tells about the worst case experience ,lets suppose "5% of users wait longer than X ms"

P99 : it tells about outlier detection i.e.  1% of users have terrible experience

Aegis adds layers — validation, retry, fallback, post-check. Each layer adds latency. You need to prove the overhead is worth it.

Scenario	Latency
Happy path (no issues)	~1000ms
Validation failure + retry	~2000ms
Capability mismatch + fallback	~3000ms
Multiple retries	~5000ms
P50 tells you: "The typical query takes X ms."
P95 tells you: "Even with retries and fallbacks, 95% of queries finish within Y ms."

Attributes are stable metadata: "which tool," "what confidence"

Events are points-in-time: "retry happened," "fallback triggered"

You don't make "retry" a separate span because retry isn't a separate operation — it's something that happens during tool execution. So it's an event on the tool.execute span.

## Why OpenTelemetry instead of custom JSON?
Because:

It's the industry standard — every observability tool understands it

It handles trace IDs, parent-child relationships, timing automatically

It's portable — you can send the same traces to Jaeger, Grafana, Datadog, or console without changing your code

It has stable APIs — you don't maintain it yourself
