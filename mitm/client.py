import subprocess

def is_riot_running() -> bool:
    return "RiotClientServices.exe" in subprocess.run("tasklist /fi \"imagename eq RiotClientServices.exe\"", shell=True, capture_output=True, text=True).stdout

def launch_riot_client(config_host: str, config_port: int):
    subprocess.run(f"\"C:\\Riot Games\\Riot Client\\RiotClientServices.exe\" --client-config-url=\"http://{config_host}:{config_port}\" --launch-product=valorant --launch-patchline=live", shell=True)