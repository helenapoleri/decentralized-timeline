import asyncio

# this is a coroutine definition
async def fake_network_request(request):
    print('making network call for request:  ' + request)
    # simulate network delay
    await asyncio.sleep(1)

    return 'got network response for request: ' + request

# this is a coroutine definition
async def web_server_handler():
    # schedule both the network calls in a non-blocking way.

    # ensure_future creates a task from the coroutine object, and schedules it on the event loop
    #task1 = asyncio.ensure_future(fake_network_request('one'))
    await fake_network_request('one')
    print('ola')
    # another way to do the scheduling
    task2 = asyncio.get_event_loop().create_task(fake_network_request('two'))

    # simulate a no-op blocking task. This gives a chance to the network requests scheduled above to be executed.
    await asyncio.sleep(0.5)

    print('doing useful work while network calls are in progress...')

    # wait for the network calls to complete. Time to step off the event loop using await! 
    await asyncio.wait([task1, task2])

    print(task1.result())
    print(task2.result())

loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.ensure_future(web_server_handler()))