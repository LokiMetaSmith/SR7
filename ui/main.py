import argparse
from ui.app import App


def main():
    parser = argparse.ArgumentParser(description="Launch the Shadowrun 7E Pygame UI.")
    parser.add_argument("--campaign", type=str, default="campaigns/default/campaign.json", help="Path to the campaign JSON file")
    parser.add_argument("--host", action="store_true", help="Run the UI as the GM/Host to broadcast state.")
    parser.add_argument("--client", action="store_true", help="Run the UI as a player/client to view state.")
    parser.add_argument("--ip", type=str, default="127.0.0.1", help="Host IP to connect to (if client).")
    args = parser.parse_args()

    # If explicitly set as client, we are not the host. Otherwise default to host behavior.
    is_host = not args.client

    app = App(width=1000, height=700, campaign_file=args.campaign, is_host=is_host, host_ip=args.ip)
    app.run()


if __name__ == "__main__":
    main()
