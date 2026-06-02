import argparse
from ui.app import App


def main():
    parser = argparse.ArgumentParser(description="Launch the Shadowrun 7E Pygame UI.")
    parser.add_argument("--campaign", type=str, default="campaigns/default/campaign.json", help="Path to the campaign JSON file")
    args = parser.parse_args()

    app = App(width=1000, height=700, campaign_file=args.campaign)
    app.run()


if __name__ == "__main__":
    main()
