import requests
import json
from datetime import datetime as dt
import sys
from dotenv import load_dotenv
import os
from filelock import Timeout, FileLock
import re
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
import time

load_dotenv()

headers = {
    "User-Agent": "PaperMC Version Poller",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}

# Check the ENV for a webhook URL
if os.getenv("WEBHOOK_URL"):
    print(f"Using webhook URL from ENV: {os.getenv('WEBHOOK_URL')}")
    webhook_urls = json.loads(os.getenv("WEBHOOK_URL"))
elif os.path.exists("webhooks.json"):
    print(f"Using webhook URL from webhooks.json")
    with open("webhooks.json", "r") as f:
        webhook_urls = json.load(f)["urls"]
else:
    print("No webhook URL found, using default")
    webhook_urls = ["url.here"]

# Get start args
start_args = sys.argv[1:]
# If it includes --stdin, we'll read from stdin

# Check if there's anything coming in through STDIN
if "--stdin" in start_args:
    # If there is, read it as a json object
    data = json.loads(sys.stdin.read())
    # Grab the urls element from the json object
    webhook_urls = data["urls"]


gql_base = "https://fill.papermc.io/graphql"

transport = RequestsHTTPTransport(url=gql_base)
client = Client(transport=transport, fetch_schema_from_transport=True)

latest_query = gql(
    """
query getLatestBuild($project: String!) {
    project(id: $project) {
        id
        versions(last: 1) {
            id
            builds(last: 1) {
                id
                download(name: "server:default") {
                    name
                    size
                    url
                    checksums {
                        sha256
                    }
                }
                commits {
                    sha
                    message
                }
                time
                channel
            }
        }
    }
}
"""
)


def convert_commit_hash_to_short(hash):
    return hash[:7]


def convert_build_date(date):
    # format: 2022-06-14T10:40:30.563Z
    return dt.strptime(date, "%Y-%m-%dT%H:%M:%S.%f%z")


def get_spigot_drama() -> str | dict:
    try:
        response = requests.get("https://drama.mart.fyi/api", headers=headers)
        data = response.json()
        return data
    except Exception as e:
        print(f"Error getting spigot drama: {e}")
        return "There's no drama :("


class PaperAPI:
    def __init__(self, base_url="https://api.papermc.io/v2", project="paper"):
        self.headers = {
            "User-Agent": "PaperMC Version Poller",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }
        self.base_url = base_url
        self.project = project
        self.image_url = ""
        if self.project == "paper":
            self.image_url = "https://assets.papermc.io/brand/papermc_logo.512.png"
        elif self.project == "folia":
            self.image_url = "https://assets.papermc.io/brand/folia_logo.256x139.png"
        elif self.project == "velocity":
            self.image_url = "https://assets.papermc.io/brand/velocity_logo.256x128.png"

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
        
    def get_stored_data(self):
        try:
            with open(f"{self.project}_poller.json", "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {"version": "", "build": "", "channel": ""}
        return data

    def write_to_json(self, version, build, channel_name):
        data = {"version": version, "build": build, "channel": channel_name}
        with open(f"{self.project}_poller.json", "w") as f:
            json.dump(data, f)

    def get_changes_for_build(self, data) -> str:
        return_string = ""
        for change in data["commits"]:
            commit_hash = convert_commit_hash_to_short(change["sha"])
            full_hash = change["sha"]
            summary = change["message"]
            summary = summary.strip()
            # summary = "Update DataConverter constants for 1.21.7\n\nhttps://github.com/PaperMC/DataConverter/commit/04b08a102a3d2473420edceed05420b5ccb3b771\n"
            # Replace the first \n\n with \n\t, then all others with \n
            summary = summary.split("\n")[0]
            # Find all unique PR/issue numbers referenced in the summary
            pr_numbers = set(re.findall(r"#(\d+)", summary))

            # Replace each occurrence exactly once so we don't wrap already-linked numbers
            for pr_number in pr_numbers:
                summary = summary.replace(
                    f"#{pr_number}",
                    f"[#{pr_number}](https://github.com/PaperMC/{self.project}/issues/{pr_number})",
                )
            return_string += f"- [{commit_hash}](https://github.com/PaperMC/{self.project}/commit/{full_hash}) {summary}\n"
        return return_string
    
    def get_latest_build(self):
        query = latest_query
        variables = {"project": self.project}
        result = client.execute(query, variable_values=variables)
        return result

    def send_v2_webhook(self, hook_url, latest_build, latest_version, build_time, image_url, changes, download_url, drama, channel_name, channel_changed):
        payload = {
            "components": [
                {
                    "type": 17,
                    "accent_color": 0x00FF00,
                    "components": [
                        {
                            "type": 9,
                            "components": [
                                {
                                    "type": 10,
                                    "content": f"# {self.project.capitalize()} Update",
                                },
                                {
                                    "type": 10,
                                    "content": f"{channel_name} Build {latest_build} for {latest_version} is now available!\nReleased <t:{build_time}:R> (<t:{build_time}:f>)",
                                },
                            ],
                            "accessory": {
                                "type": 11,
                                "media": {
                                    "url": image_url
                                }
                            }
                        },
                        {
                            "type": 14,
                            "divider": True
                        },
                        {
                            "type": 10,
                            "content": changes
                        },
                        {
                            "type": 14,
                            "divider": True
                        },
                        {
                            "type": 10,
                            "content": f"-# {drama['response']}"
                        }
                    ]
                },
                {
                    "type": 1,
                    "components": [
                        {
                            "type": 2,
                            "label": "Download",
                            "style": 5,
                            "url": download_url
                        }
                    ]
                }
            ],
            "flags": 1 << 15,
            "allowed_mentions": {"parse": []}
        }
        # If the channel changed, add another container to the components
        if channel_changed:
            changed_container = {
                "type": 10,
                "content": f"# {self.project.capitalize()} is now {channel_name}!"
            }
            payload["components"].append(changed_container)
        # Then do a post to the webhook with ?with_components=true
        requests.post(
            hook_url,
            json=payload,
            params={"with_components": "true"}
        )

    def run(self):
        current_time = dt.now()
        print(f"[{current_time}] ", end="")
        try:
            gql_latest_build = self.get_latest_build()
            latest_version = gql_latest_build["project"]["versions"][0]["id"]
            latest_build = gql_latest_build["project"]["versions"][0]["builds"][0]["id"]
            latest_build_info = gql_latest_build["project"]["versions"][0]["builds"][0]
            channel_name = gql_latest_build["project"]["versions"][0]["builds"][0]["channel"]
            updated = self.up_to_date(latest_version, latest_build)
            stored_data = self.get_stored_data()
            channel_changed = stored_data.get("channel", None) is not None and stored_data.get("channel", "") != channel_name
            if not updated:
                print(f"New build. Sending update for {self.project}.")
                # Write the latest version and build to the json file
                self.write_to_json(latest_version, latest_build, channel_name)
                changes = self.get_changes_for_build(latest_build_info)
                download_url = latest_build_info["download"]["url"]
                build_time = int(convert_build_date(latest_build_info["time"]).timestamp())
                # Create a new webhook
                for hook in webhook_urls:
                    drama = get_spigot_drama()
                    # Otherwise we have to hand roll it since there's no library support for components v2
                    self.send_v2_webhook(
                        hook_url=hook,
                        latest_build=latest_build,
                        latest_version=latest_version,
                        build_time=build_time,
                        image_url=self.image_url,
                        changes=changes,
                        download_url=download_url,
                        drama=drama,
                        channel_name=channel_name.capitalize(),
                        channel_changed=channel_changed
                    )
            else:
                print(f"Up to date for {self.project}")
        except KeyError as e:
            print(f"Error getting latest build: {e}")
            return
        finally:
            # Wait 2 seconds to not hit discord API rate limits
            time.sleep(2)


def main():
    try:
        lock_file = "paper_poller.lock"
        lock = FileLock(lock_file, timeout=10)
        with lock:
            paper = PaperAPI()
            paper.run()
            folia = PaperAPI(project="folia")
            folia.run()
            velocity = PaperAPI(project="velocity")
            velocity.run()
            waterfall = PaperAPI(project="waterfall")
            waterfall.run()
    except Timeout:
        print("Lock file is locked, exiting")


if __name__ == "__main__":
    main()
