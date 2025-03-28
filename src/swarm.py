import asyncio
from time import time
from typing import List
from .kahootbot import KahootBot
import secrets

class Swarm:
    def __init__(self):
        """Initialize the swarm object."""
        self.ttl = None
        self.start_time = time()
        self.tasks: List[asyncio.Task] = []
        self.gameid: int
        self.nickname: str
        self.crash: bool
        self.queue = asyncio.Queue()  # Errors will be put in here
        self.instancetotask: dict[KahootBot, asyncio.Task] = {}
        self.stop = False

    def isAlive(self) -> bool:
        """Check if the swarm is still alive based on TTL."""
        return (time() - self.start_time) < self.ttl

    def getTimeRemaining(self) -> int:
        """Calculate the time remaining before TTL expires."""
        return self.ttl - (time() - self.start_time)

    def startNewBot(self):
        """Start a new bot instance and create its task."""
        print("starting a new bot!")
        if self.amount == 1: 
            instance = KahootBot(self.gameid, self.nickname, self.crash, self.queue)
        else: 
            instance = KahootBot(self.gameid, f"{self.nickname}{secrets.token_hex(4)}", self.crash, self.queue)
        
        task = instance.start()
        self.instancetotask[instance] = task
        self.tasks.append(task)

    # Async functions below

    async def cleanUp(self):
        """Cancel all running tasks."""

        for task in self.tasks:
            
            task.cancel()
            await task  # Ensure graceful cancellation

        
        self.watchdog.cancel()    
        await self.watchdog 
        
       
        self.tasks.clear()
        self.instancetotask.clear()

    

    async def watchDog(self):
        """Listen for errors and handle them when they occur."""
        try:
            while True:
                instance, error = await self.queue.get()
                await error.handle(self.instancetotask[instance], self)
                self.queue.task_done()

        except asyncio.CancelledError:
            return

    async def start(self, gameid: int, nickname: str, crash: bool, amount: int, ttl: int):
        """Start the swarm in an async event loop with TTL check."""
        self.gameid = gameid
        self.nickname = nickname
        self.crash = crash
        self.ttl = int(ttl)
        self.amount = amount
        print(f"starting {amount} kahoot bot(s) ...")

        # Start error handler task
        self.watchdog = asyncio.create_task(self.watchDog())

        # Start new bot instances
        for _ in range(int(amount)):
            self.startNewBot()

        # Main loop to check if the swarm is still alive
        while self.isAlive() and not self.stop:
            print("time remaining: " + str(self.getTimeRemaining()))
            await asyncio.sleep(5)

        await self.cleanUp()

    # Task starter for the /swarm endpoint wrapped in a new task as we dont want the endpoint to live for the entire duration of the swarm.
    def createSwarm(self, gameid: int, nickname: str, crash: bool, amount: int, ttl: int):
        """Create a new swarm task and run it asynchronously."""
        asyncio.create_task(self.start(gameid, nickname, crash, amount, ttl))
