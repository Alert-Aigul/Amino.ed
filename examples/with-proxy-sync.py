import aminoed.sync as aminoed

client = aminoed.Client()

ip = client.with_proxy(
    "http://proxy", # one argument - your proxy 
    client.get_request, # one argument - two atrgument function
    "http://api.ipify.org/" # this and other arguments - client.get_request arguments
)

print(ip.text)
