import requests
from discord_webhook import DiscordWebhook, DiscordEmbed
import json
from datetime import datetime as dt
import sys
from dotenv import load_dotenv
import os

load_dotenv()

CONFIG = {
    "enable_pterodactyl": os.getenv("ENABLE_PTERODACTYL") == "true",
    "pterodactyl_domain": os.getenv("PTERODACTYL_DOMAIN"),
    "pterodactyl_api_key": os.getenv("PTERODACTYL_API_KEY"),
    "pterodactyl_server_id": os.getenv("PTERODACTYL_SERVER_ID")
}

if CONFIG["enable_pterodactyl"]:
    from pydactyl import PterodactylClient
    api = PterodactylClient(CONFIG["pterodactyl_domain"], CONFIG['pterodactyl_api_key'])
    try:
        util = api.client.servers.get_server_utilization(CONFIG["pterodactyl_server_id"])
        print(util)
    except Exception as e:
        print(f"Error getting Pterodactyl API to work, disabling Pterodactyl: {e}")
        CONFIG["enable_pterodactyl"] = False

headers = {
    "User-Agent": "PaperMC Version Poller",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache"
}

# Check the ENV for a webhook URL   
if os.getenv("WEBHOOK_URL"):
    webhook_urls = json.loads(os.getenv("WEBHOOK_URL"))
else: 
    webhook_urls = [
        "url.here"
        ]

# Get start args
start_args = sys.argv[1:]
# If it includes --stdin, we'll read from stdin

# Check if there's anything coming in through STDIN
if "--stdin" in start_args:
    # If there is, read it as a json object
    data = json.loads(sys.stdin.read())
    # Grab the urls element from the json object
    webhook_urls = data["urls"]


paper_base = "https://api.papermc.io/v2"


def convert_commit_hash_to_short(hash):
    return hash[:7]


def convert_build_date(date):
    # format: 2022-06-14T10:40:30.563Z
    return dt.strptime(date, "%Y-%m-%dT%H:%M:%S.%f%z")


def get_spigot_drama() -> str | dict:
    try:
        response = requests.get("https://chew.pw/api/spigotdrama", headers=headers)
        data = response.json()
        return data
    except Exception as e:
        print(f"Error getting spigot drama: {e}")
        return "There's no drama :("

class PaperAPI():
    def __init__(self, base_url="https://api.papermc.io/v2", project="paper"):
        self.headers = {
            "User-Agent": "PaperMC Version Poller",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache"
        }
        self.base_url = base_url
        self.project = project

    def get_latest_minecraft_version(self) -> str:
        url = f"{self.base_url}/projects/{self.project}"
        response = requests.get(url, headers=self.headers)
        data = response.json()
        # Get the versions list
        versions = data["versions"]
        # Get the latest version
        latest_version = versions[-1]
        return latest_version
    
    def get_latest_build_for_version(self, version) -> int:
        url = f"{self.base_url}/projects/{self.project}/versions/{version}"
        response = requests.get(url, headers=self.headers)
        data = response.json()
        # Get the builds list
        builds = data["builds"]
        # Get the latest build
        latest_build = builds[-1]
        return latest_build
    
    def get_build_info(self, version, build) -> dict:
        url = f"{self.base_url}/projects/{self.project}/versions/{version}/builds/{build}"
        response = requests.get(url, headers=self.headers)
        data = response.json()
        return data
    
    def up_to_date(self, version, build) -> bool:
        # Read out {project}_poller.json file
        try:
            with open(f"{self.project}_poller.json", "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {"version": "", "build": ""}
        # Check if the version is up to date
        if data["version"] == version and data["build"] == build:
            return True
        else:
            return False
        
    def construct_download_url(self, version, build, data) -> str:
        jar_name = data["downloads"]["application"]["name"]
        return f"{self.base_url}/projects/{self.project}/versions/{version}/builds/{build}/downloads/{jar_name}"
    
    def write_to_json(self, version, build):
        data = {"version": version, "build": build}
        with open(f"{self.project}_poller.json", "w") as f:
            json.dump(data, f)

    def get_changes_for_build(self, data) -> str:
        return_string = ""
        for change in data["changes"]:
            commit_hash = convert_commit_hash_to_short(change["commit"])
            full_hash = change["commit"]
            summary = change["summary"]
            return_string += f"- [{commit_hash}](https://github.com/PaperMC/{self.project}/commit/{full_hash}) {summary}\n"
        return return_string
    
    def run(self, restart_on_build=False):
        current_time = dt.now()
        print(f"[{current_time}] ", end="")
        latest_version = self.get_latest_minecraft_version()
        latest_build = self.get_latest_build_for_version(latest_version)
        updated = self.up_to_date(latest_version, latest_build)
        if not updated:
            print("New build. Sending update.")
            build_info = self.get_build_info(latest_version, latest_build)
            # Create a new webhook
            for hook in webhook_urls:
                webhook = DiscordWebhook(url=hook, rate_limit_retry=True)
                # Create a new embed
                embed = DiscordEmbed(title=f"{self.project.capitalize()} Update", description=f"Build {latest_build} for {latest_version} is now available!", color=0x00ff00)
                # Add the latest build to the embed
                if self.project == "paper":
                    embed.set_author(name="Paper", url="https://papermc.io/", icon_url="https://cdn.theairplan.com/images/paperlogo.png")
                elif self.project == "folia":
                    embed.set_author(name="Folia", url="https://papermc.io/", icon_url="https://cdn.discordapp.com/attachments/1018399544398065725/1092644957849927680/Folia_Logo_200x200.png")
                elif self.project == "velocity":
                    embed.set_author(name="Velocity", url="https://papermc.io/", icon_url="https://cdn.theairplan.com/images/velocity.png")
                else:
                    embed.set_author(name=self.project.capitalize(), url="https://papermc.io/")
                #embed.add_embed_field(name="Build", value=latest_build, inline=True)
                #embed.add_embed_field(name="Version", value=latest_version, inline=True)
                embed.add_embed_field(name="Link", value=self.construct_download_url(latest_version, latest_build, build_info), inline=False)
                #embed.add_embed_field(name="sha256", value=build_info["downloads"]["application"]["sha256"], inline=False)
                embed.add_embed_field(name="Changes", value=self.get_changes_for_build(build_info), inline=False)
                #embed.add_embed_field(name="Build Channel", value=build_info["channel"], inline=False)
                # Timestamp
                embed.set_timestamp(convert_build_date(build_info["time"]).timestamp())
                # Set a footer to link to the site to add this webhook
                drama = get_spigot_drama()
                embed.set_footer(text=drama['response'])
                webhook.add_embed(embed)
                # Send the webhook
                webhook.execute()
                # Write the latest version and build to the json file
            self.write_to_json(latest_version, latest_build)
            # Restart the server if enabled
            if CONFIG["enable_pterodactyl"] and restart_on_build:
                try:
                    print("Restarting server")
                    api.client.servers.send_power_action(CONFIG["pterodactyl_server_id"], "restart")
                except Exception as e:
                    print(f"Error restarting server: {e}")
        else:
            print("Up to date")


def main():
    paper = PaperAPI()
    paper.run(restart_on_build=True)
    folia = PaperAPI(project="folia")
    folia.run()
    velocity = PaperAPI(project="velocity")
    velocity.run()
    waterfall = PaperAPI(project="waterfall")
    waterfall.run()


if __name__ == "__main__":
    main()
