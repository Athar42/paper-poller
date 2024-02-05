import requests
from discord_webhook import DiscordWebhook, DiscordEmbed
import json
from datetime import datetime as dt
import sys

headers = {
    "User-Agent": "PaperMC Version Poller",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache"
}

webhook_urls = [
    "url-here.com"
    ]

# Check if there's anything coming in through STDIN
if sys.stdin.isatty():
    # If there is, read it as a json object
    data = json.loads(sys.stdin.read())
    # Grab the urls element from the json object
    webhook_urls = data["urls"]


paper_base = "https://api.papermc.io/v2"


def get_latest_minecraft_version():
    url = f"{paper_base}/projects/paper"
    response = requests.get(url, headers=headers)
    data = response.json()
    # Get the versions list
    versions = data["versions"]
    # Get the latest version
    latest_version = versions[-1]
    return latest_version


def get_latest_paper_build_for_version(version):
    url = f"{paper_base}/projects/paper/versions/{version}"
    response = requests.get(url, headers=headers)
    data = response.json()
    # Get the builds list
    builds = data["builds"]
    # Get the latest build
    latest_build = builds[-1]
    return latest_build

def get_latest_folia_build_for_version(version):
    url = f"{paper_base}/projects/folia/versions/{version}"
    response = requests.get(url, headers=headers)
    data = response.json()
    # Get the builds list
    builds = data["builds"]
    # Get the latest build
    latest_build = builds[-1]
    return latest_build


def get_build_info(version, build):
    url = f"{paper_base}/projects/paper/versions/{version}/builds/{build}"
    response = requests.get(url, headers=headers)
    data = response.json()
    return data

def get_folia_build_info(version, build):
    url = f"{paper_base}/projects/folia/versions/{version}/builds/{build}"
    response = requests.get(url, headers=headers)
    data = response.json()
    return data


def up_to_date(version, build):
    # Read our paper_poller.json file
    try:
        with open("paper_poller.json", "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {"version": "", "build": ""}
    # Check if the version is up to date
    if data["version"] == version and data["build"] == build:
        return True
    else:
        return False

def folia_up_to_date(version, build):
    # Read our folia_poller.json file
    try:
        with open("folia_poller.json", "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {"version": "", "build": ""}
    # Check if the version is up to date
    if data["version"] == version and data["build"] == build:
        return True
    else:
        return False


def construct_download_url(version, build, data):
    jar_name = data["downloads"]["application"]["name"]
    return f"{paper_base}/projects/paper/versions/{version}/builds/{build}/downloads/{jar_name}"


def construct_folia_download_url(version, build, data):
    jar_name = data["downloads"]["application"]["name"]
    return f"{paper_base}/projects/folia/versions/{version}/builds/{build}/downloads/{jar_name}"


def write_to_json(version, build):
    data = {"version": version, "build": build}
    with open("paper_poller.json", "w") as f:
        json.dump(data, f)


def write_folia_to_json(version, build):
    data = {"version": version, "build": build}
    with open("folia_poller.json", "w") as f:
        json.dump(data, f)


def convert_build_date(date):
    # format: 2022-06-14T10:40:30.563Z
    return dt.strptime(date, "%Y-%m-%dT%H:%M:%S.%f%z")


def convert_commit_hash_to_short(hash):
    return hash[:7]


def get_changes_for_build(data):
    return_string = ""
    for change in data["changes"]:
        commit_hash = convert_commit_hash_to_short(change["commit"])
        full_hash = change["commit"]
        summary = change["summary"]
        return_string += f"- [{commit_hash}](https://github.com/PaperMC/paper/commit/{full_hash}) {summary}\n"
    return return_string


def get_folia_changes_for_build(data):
    return_string = ""
    for change in data["changes"]:
        commit_hash = convert_commit_hash_to_short(change["commit"])
        full_hash = change["commit"]
        summary = change["summary"]
        return_string += f"- [{commit_hash}](https://github.com/PaperMC/Folia/commit/{full_hash}) {summary}\n"
    return return_string

def main():
    current_time = dt.now()
    print(f"[{current_time}] ", end="")
    latest_version = get_latest_minecraft_version()
    latest_build = get_latest_paper_build_for_version(latest_version)
    updated = up_to_date(latest_version, latest_build)
    if not updated:
        print("New build. Sending update.")
        build_info = get_build_info(latest_version, latest_build)
        # Create a new webhook
        for hook in webhook_urls:
            webhook = DiscordWebhook(url=hook, rate_limit_retry=True)
            # Create a new embed
            embed = DiscordEmbed(title="Paper Update", description=f"Build {latest_build} for {latest_version} is now available!", color=0x00ff00)
            # Add the latest build to the embed
            embed.set_author(name="Paper", url="https://papermc.io/", icon_url="https://cdn.theairplan.com/images/paperlogo.png")
            #embed.add_embed_field(name="Build", value=latest_build, inline=True)
            #embed.add_embed_field(name="Version", value=latest_version, inline=True)
            embed.add_embed_field(name="Link", value=construct_download_url(latest_version, latest_build, build_info), inline=False)
            #embed.add_embed_field(name="sha256", value=build_info["downloads"]["application"]["sha256"], inline=False)
            embed.add_embed_field(name="Changes", value=get_changes_for_build(build_info), inline=False)
            #embed.add_embed_field(name="Build Channel", value=build_info["channel"], inline=False)
            # Timestamp
            embed.set_timestamp(convert_build_date(build_info["time"]).timestamp())
            webhook.add_embed(embed)
            # Send the webhook
            webhook.execute()
            # Write the latest version and build to the json file
        write_to_json(latest_version, latest_build)
    else:
        print("Up to date")
    
    # Folia
    current_time = dt.now()
    print(f"[{current_time}] ", end="")
    folia_latest_version = get_latest_minecraft_version()
    folia_latest_build = get_latest_folia_build_for_version(folia_latest_version)
    folia_updated = folia_up_to_date(folia_latest_version, folia_latest_build)
    if not folia_updated:
        print("New Folia build. Sending update.")
        folia_build_info = get_folia_build_info(folia_latest_version, folia_latest_build)
        # Create a new webhook
        for hook in webhook_urls:
            folia_webhook = DiscordWebhook(url=hook, rate_limit_retry=True)
            # Create a new embed
            folia_embed = DiscordEmbed(title="Folia Update", description=f"Build {folia_latest_build} for {folia_latest_version} is now available!", color=0x00ff00)
            # Add the latest build to the embed
            folia_embed.set_author(name="Folia", url="https://papermc.io/", icon_url="https://cdn.discordapp.com/attachments/1018399544398065725/1092644957849927680/Folia_Logo_200x200.png")
            #embed.add_embed_field(name="Build", value=latest_build, inline=True)
            #embed.add_embed_field(name="Version", value=latest_version, inline=True)
            folia_embed.add_embed_field(name="Link", value=construct_folia_download_url(folia_latest_version, folia_latest_build, folia_build_info), inline=False)
            #folia_embed.add_embed_field(name="sha256", value=folia_build_info["downloads"]["application"]["sha256"], inline=False)
            folia_embed.add_embed_field(name="Changes", value=get_folia_changes_for_build(folia_build_info), inline=False)
            #folia_embed.add_embed_field(name="Build Channel", value=folia_build_info["channel"], inline=False)
            # Timestamp
            folia_embed.set_timestamp(convert_build_date(folia_build_info["time"]).timestamp())
            folia_webhook.add_embed(folia_embed)
            # Send the webhook
            folia_webhook.execute()
        # Write the latest version and build to the json file
        write_folia_to_json(folia_latest_version, folia_latest_build)
    else:
        print("Folia up to date")


if __name__ == "__main__":
    main()
