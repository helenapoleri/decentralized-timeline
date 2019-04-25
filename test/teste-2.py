import asyncio

async def echo_server(reader, writer):
    while True:
        data = await reader.read(100)  # Max number of bytes to read
        if not data:
            break
        writer.write(data)
        await writer.drain()  # Flow control, see later
    writer.close()
async def main(host, port):
    server = await asyncio.start_server(echo_server, host, port)
    await server.serve_forever()
    

asyncio.run(main('127.0.0.1', 5000))

import asyncio
class EchoProtocol(asyncio.Protocol):
    def connection_made(self, transport):
        self.transport = transport
    def data_received(self, data):
        self.transport.write(data)

async def main(host, port):
    loop = asyncio.get_running_loop()
    server = await loop.create_server(EchoProtocol, host, port)
    await server.serve_forever()
asyncio.run(main('127.0.0.1', 5000))