from utils.spawner import Spawner

spawner = Spawner()
spawner.create_or_modify_spawn(name="test", new_port=22222, new_minecraftVersion="1.19", server_properties=["DIFFICULTY=HARD", "MAX_PLAYERS=10", "MAX_WORLD_SIZE=10"])
spawner.purge_spawn("test")