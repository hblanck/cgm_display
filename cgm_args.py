import argparse

class cgm_args:
    def __init__(self) -> None:
        # Process command line arguments
        ArgParser = argparse.ArgumentParser(description="Handle Command Line Arguments")
        ArgParser.add_argument("--logging", '-l', default="INFO", help="Logging level: INFO (Default) or DEBUG")
        ArgParser.add_argument("--nightscoutserver", '-ns', help="Set the base URL for your Nightscout server e.g. https://mynighscout.domain.com")
        ArgParser.add_argument("--polling_interval", default=60, help="Polling interval for getting updates from Sugarmate")
        ArgParser.add_argument("--time_ago_interval", default=30, help="Polling interval for updating the \"Time Ago\" detail")
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