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

for the current retryable sandboxed logic which is being implemented
### things i would change
- Return immediately after a successful execution (don't continue looping).

- Retry only transient exceptions (TimeoutError, maybe ConnectionError), not permanent ones like ValueError or ZeroDivisionError.

ValueError is a specific type of error that occurs when a function gets an argument with the correct data type but an invalid value

A TypeError is a built-in error triggered when you use a piece of data incorrectly based on its data type.The Cause: You are forcing a data type to do something it cannot do.JavaScript Example: Trying to treat a standard variable like a function, such as writing let x = 10; x();.

The difference between max_attempts (with an s) and max_attempt (without an s) in that code comes down to two different concepts in Python: class configuration storage versus function parameter overrides.Here is exactly why they are named differently and how they work together:1. self.max_attempts (Inside __init__)This is an Instance Variable. It defines the permanent, global baseline default configuration for your Executor object. It uses the plural "attempts" because it represents the total pool of possible tries allowed by default across the whole system lifespan.2. max_attempt (Inside the execute function signature)This is a Local Parameter Override. It is singular because it allows a single, specific call to the function to say: "Hey, for this one specific request, I want to change the target ceiling rule to this exact number."

trace means what ,it should be given at the response time


- https://api.openweathermap.org/data/2.5/weather?q=London&appid=abc123&units=metric

The import requests statement imports the Requests package on PyPI, which is Python's most popular third-party library for making HTTP requests.

### What normalization did:

Flattened nested objects into one level
Renamed confusing keys (name → city, main.temp → temperature)
Extracted only the 9 fields you care about
Dropped 50+ useless fields (visibility, coordinates, timestamps, etc.)

# If "city" is missing, returns None gracefully:
city = request.arguments.get("city")  # None — no crash ✅

# Even better with default:
city = request.arguments.get("city", "London")  # Defaults to "London"

main.py creates: ExecutionRequest(tool="weather", arguments={"city": "London"})
This becomes a Pydantic object: request.arguments = {"city": "London"}
Tool extracts: request.arguments.get("city") → "London"
Tool uses "London" to call API

# Just send raw data? HOW?
response = requests.get(self.base_url, data=request)
# API: "What is this? I don't understand Python objects!"
# Result: 400 Bad Request

The params dict tells requests.get():
"Build the URL with these query parameters"
"I don't care how URLs work, you handle it"

OpenWeather's docs page: https://openweathermap.org/current


### how the weather details are being fetched
- first of all ,i am declaring what are my request as an arguments

- they are passed as a response to the executor functionality as a argument ,to the .execute

- there it identifies what could be the possible tool from the registry

- the registry checks if the tool exists or not ,how it checks ,there i have declared the tool under the registry hence yes

- now once its done i will be call the specific tool to handover my request for the possible response

- now inside that particular tool ,first thing would be to fetch whats the value of the possible key(argument)

- once its fetched then we are sending the request to the external source for our request

- but the external source alone cant understand the possible request ,for that : you need to declare them in a way that it could understand without breaking ,hence we specify the info about the arguments value with a special key ,so as to get the response

- once we get the response ,we look for possible errors or success

- after wards we simply go for cleaning up the mess ,keeping the necessary inputs to showcase to the client and

- its done ,bro :)


"Can Aegis execute completely different capabilities without changing its execution engine?"

A reliability layer between the LLM and external capabilities.