
import asyncio, struct
from .parser import Parser
from .errors import *

BUFFER_SIZE = 1024 * 1024

class Server(object):
    def __init__(self, host, port, loop):
        self.host = host
        self.port = port
        self.reconnects = 0
        self.last_attempt = None
        self.r = None
        self.w = None
        self.flush_queue = asyncio.Queue( maxsize=1, loop=loop )
        self.read_queue  = asyncio.Queue( maxsize=2, loop=loop )
        self.pending = []
        self.pending_sz = 0
        self.connected = False
        self.reconnect_task = None
        #self.did_connect = False
        #self.discovered = False

class Client(object):

  def __repr__(self):
    return "<mrws client v{}>".format(__version__)

  def __init__(self):
    self.loop = None
    self.parser = Parser(self)
    self.servers = []

  async def connect(self,
              servers=[("127.0.0.1",7000)],
              io_loop=None,
              ssl=None
             ):
    self.loop = io_loop or asyncio.get_event_loop()
    self.reconnect_task = None
    self.ssl = ssl

    self.read_tasks  = []
    self.flush_tasks = []

    self.max_pending = 1024 * 1024 * 10

    for s in servers:
      srv = Server( s[0], s[1], self.loop )
      srv.r, srv.w = await asyncio.open_connection( s[0], s[1], loop=self.loop, ssl=ssl)
      srv.connected = True
      self.servers.append(srv)

    self.num_servers = len(self.servers)

    for n in range(len(servers)):
      self.read_tasks.append(  self.loop.create_task(self.read_loop(n)) )
      self.flush_tasks.append( self.loop.create_task(self.flusher(n)  ) )


  async def close(self):

    for t in self.read_tasks:
      t.cancel()
    for t in self.flush_tasks:
      t.cancel()

    try:
      
      for s in range(len(self.servers)):
        if self.servers[s].pending_sz > 0:
          self.servers[s].w.writelines(self.servers[s].pending)
          self.servers[s].pending = []
          self.servers[s].pending_sz = 0
          await self.servers[s].w.drain()
        self.servers[s].w.close()

    except:
      pass


  async def send_flush(self, slot):
    bstr = b'\x00\x0A'
    s = slot % len(self.servers)
    self.servers[s].pending.append(bstr)
    self.servers[s].pending_sz += 2
    if self.servers[s].flush_queue.empty():
      await self.flush_pending(s)

  #TODO ?
    #if self.is_closed: raise ErrConnectionClosed
    #if data_len > self.max_data_size: raise ErrMaxPayload

  async def push(self, slot, data, data_len):
    s = slot % self.num_servers
    if not self.servers[s].connected:
      if self.servers[s].pending_sz > self.max_pending:
        return -1
    bstr = b'\x00\x01' + struct.pack("=I",data_len) + data
    self.servers[s].pending.append(bstr)
    self.servers[s].pending_sz += data_len + 6
    if self.servers[s].flush_queue.empty():
      await self.flush_pending(s)

  async def push_noflush(self, slot, data, data_len):
    s = slot % self.num_servers
    if not self.servers[s].connected:
      if self.servers[s].pending_sz > self.max_pending:
        return -1
    bstr = b'\x00\x01' + struct.pack("=I",data_len) + data
    self.servers[s].pending.append(bstr)
    self.servers[s].pending_sz += data_len + 6
    if self.servers[s].pending_sz > BUFFER_SIZE:
      await self.flush_pending(s)
    return 0


  async def get(self, s, b):
    s = s % self.num_servers
    blen = len(b)
    bstr = b'\x00\x0B' + struct.pack(">H",blen) + b

    self.servers[s].pending.append(bstr)
    self.servers[s].pending_sz += blen+4
    if self.servers[s].flush_queue.empty():
      await self.flush_pending(s)

    return await self.servers[s].read_queue.get()

  async def set(self, s, b):
    s = s % self.num_servers
    blen = len(b)
    bstr = b'\x00\x0C' + struct.pack(">H",blen) + b

    self.servers[s].pending.append(bstr)
    self.servers[s].pending_sz += blen+4
    if self.servers[s].flush_queue.empty():
      await self.flush_pending(s)

    return 0

  async def flush(self):
    for s in range(len(self.servers)):
      await self.flush_pending(s)

  async def flush_pending(self, s):
    try:
      if not self.servers[s].connected: return
      await self.servers[s].flush_queue.put(None)
    except asyncio.CancelledError:
      pass

  async def flusher(self, s):
    while True:
      try:
        await self.servers[s].flush_queue.get()

        if self.servers[s].pending_sz > 0:
          self.servers[s].w.writelines(self.servers[s].pending)
          self.servers[s].pending = []
          self.servers[s].pending_sz = 0
          await self.servers[s].w.drain()
      except OSError as e:
        if self.reconnect_task == None:
          self.reconnect_task = self.reconnect(s)
        await self.reconnect_task
      except asyncio.CancelledError:
        break

  async def reconnect(self, s):

    srv = self.servers[s]
    srv.connected = False
    while True:
      try:
        print("Attempting to reconnect to server",s)
        srv.r, srv.w = await asyncio.open_connection( srv.host, srv.port, loop=self.loop, ssl=self.ssl)
        print("Reconnected")
        srv.connected = True
        self.reconnect_task = None
        break
      except:
        await asyncio.sleep(5)

  async def process_read(self, s, msgs):
    await self.servers[s].read_queue.put(msgs) 

  async def read_loop(self, s):
    while True:
      try:
        if self.servers[s].r.at_eof():  
          self.servers[s].connected = False
          if self.reconnect_task == None:
            self.reconnect_task = self.reconnect(s)
          await self.reconnect_task

        b = await self.servers[s].r.read(BUFFER_SIZE) 
        await self.parser.parse(s, b)
      except OSError as e:
        if self.reconnect_task == None:
          self.reconnect_task = self.reconnect(s)
        await self.reconnect_task
      except asyncio.CancelledError:
        break

