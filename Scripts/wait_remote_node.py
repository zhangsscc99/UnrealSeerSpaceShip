import sys
import time

sys.path.append(
    r"C:\Program Files\Epic Games\UE_5.8\Engine\Plugins\Experimental\PythonScriptPlugin\Content\Python"
)
from remote_execution import RemoteExecution

for i in range(90):
    remote = RemoteExecution()
    remote.start()
    time.sleep(2)
    count = len(remote.remote_nodes)
    remote.stop()
    print(f"attempt={i} nodes={count}")
    if count > 0:
        sys.exit(0)
    time.sleep(5)

sys.exit(1)
