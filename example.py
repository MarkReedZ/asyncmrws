
import asyncio, time, ssl
import asyncmrws
import mrpacker

async def run(loop):
  c = asyncmrws.Client()
  await c.connect(io_loop=loop,servers=[("127.0.0.1",7100)])

  #sc = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
  #sc.load_verify_locations('cert/server.crt')
  #await c.connect(io_loop=loop,servers=[("127.0.0.1",7100)],ssl=sc)

  m = mrpacker.pack([1,2,3,"test"])
  l = len(m)
  await c.push( 0, m, l )
  await c.close()

loop = asyncio.get_event_loop()
loop.run_until_complete(run(loop))
loop.close()

