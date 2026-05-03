import psutil
for pid in psutil.process_iter():
    if pid.name() == "GuiltyGearXrd.exe":
        xrd_process = pid
        break

envs = xrd_process.environ()
for env in envs:
    if "experimental" in envs.get(env.__str__()).lower():
        print(env.__str__(), end="=")
        print(envs.get(env.__str__()), end="\n\n")

