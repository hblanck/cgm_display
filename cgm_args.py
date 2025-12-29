import argparse

class cgm_args:
    def __init__(self) -> None:
        # Process command line arguments
        ArgParser = argparse.ArgumentParser(description="Handle Command Line Arguments")

        subparsers = ArgParser.add_subparsers(title="commands", dest="command")

        # Add Subparser for 'nightscout' command
        add_parsers = subparsers.add_parser("nightscout", help="Nightscout mode - Get Display data from a Nightscout server")
        add_parsers.add_argument("--nightscoutserver", "-ns", help="Set the base URL for your Nightscout server d.g. https://mynightscout.domain.com")
        add_parsers.add_argument("--logging", "-l", default="INFO", help="Logging level: INFO (Default) or DEBUG")
        add_parsers.add_argument("--polling_interval", default=60, help="Polling interval for getting updates from Sugarmate")
        add_parsers.add_argument("--time_ago_interval", default=30, help="Polling interval for updating the \"Time Ago\" detail") 

        # Add Subparser for 'dexcom' command
        add_parsers = subparsers.add_parser("dexcom", help="Dexcom mode - Get Display data from a Dexcom server")
        add_parsers.add_argument("--logging", "-l", default="INFO", help="Logging level: INFO (Default) or DEBUG")
        add_parsers.add_argument("--polling_interval", default=60, help="Polling interval for getting updates from Sugarmate")
        add_parsers.add_argument("--time_ago_interval", default=30, help="Polling interval for updating the \"Time Ago\" detail")
        add_parsers.add_argument("--username", "-u", help="Dexcom Share User Name")
        add_parsers.add_argument("--password", "-p", help="Dexcom Share Password")
        self.args = ArgParser.parse_args()

    @property
    def logging(self):
        return self.args.logging

    @property
    def night_scout_server(self):
        return self.args.nightscoutserver
    
    @property
    def polling_interval(self):
        return self.args.polling_interval
    
    @property
    def time_ago_interval(self):
        return self.args.time_ago_interval

    @property
    def username(self):
        return self.args.username

    @property
    def password(self):
        return self.args.password