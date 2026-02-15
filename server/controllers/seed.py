import asyncio
from server.controllers.pokemonController import PokemonController

async def run():
    controller = PokemonController()
    await controller.seed_kanto()

if __name__ == "__main__":
    asyncio.run(run())