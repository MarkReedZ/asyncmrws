
import asyncio, time
import asyncmrws, mrpacker

async def run(loop):
  c = asyncmrws.Client()
  await c.connect(io_loop=loop,servers=[("127.0.0.1",7100),("127.0.0.1",7001)])

  num = 10000
  #m = mrpacker.pack( [1, "foo", {"yay":1}] )
  m = mrpacker.pack( "AeeGEVMfFEANKzNPhbNkhMbORHAqn-rR" )
  s = time.time()
  for x in range(1000):
    l = []
    for y in range(10):
      l.append( c.get( x, m ) )
      #l.append( c.set( x, m ) )
    await asyncio.gather( *l )



  e = time.time()
  print( num/(e-s)," Requests/second")

  await asyncio.sleep(0.5, loop=loop)
  await c.close()

if __name__ == '__main__':
  loop = asyncio.get_event_loop()
  loop.run_until_complete(run(loop))
  loop.close()
