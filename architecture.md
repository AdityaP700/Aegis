Why does the Executor exist?
Why do tools inherit from BaseTool?
Why does the Registry exist?
Why are exceptions centralized?
Why are timing metrics collected in the Executor?


for the weather tool , i'm gonna implement an error reliability layer which deals with the distributed systems

### there are two types of failuire
- permanent failure
#### they never change
- transient failure
### they usually change : it could be timeout ,503 ,429 rate limited ,temporary network issue

- "Can this failure realistically disappear by waiting?"

If yes
↓
Retry.

If no
↓
Fail immediately.

but here comes another question
How many times should I retry?

There is no universal answer.

It depends on the service.

For example

Weather API
3 attempt
is common.

Payment
Maybe
5 attempts
because losing a payment is expensive.

LLM API
Maybe
2 attempts
because every retry costs money and increases latency.

exponential backoff
 - its a technique ,where after a failure by anything ,we provide time to the server to recover and go for the next process

Attempt 1
↓
Wait 100 ms
↓
Attempt 2
↓
Wait 200 ms

Notice something?

The Tool has **no idea** it was called three times.

That's a beautiful abstraction.

---

# Now let's answer your waiting time question.

You said

> "The variable should be the different waiting times."

Exactly.

But where should that variable live?

Not inside Weather.

Imagine tomorrow.