class PlainOnlineTournamentConfig:
    en_confirmation_end_time = None
    en_tournament_timezone = None
    ru_confirmation_end_time = None
    ru_tournament_timezone = None
    en_discord_confirmation_channel = None
    ru_discord_confirmation_channel = None
    public_lobby = None
    is_validated = False

    def __init__(
        self,
        en_confirmation_end_time=None,
        en_tournament_timezone=None,
        ru_confirmation_end_time=None,
        ru_tournament_timezone=None,
        en_discord_confirmation_channel=None,
        ru_discord_confirmation_channel=None,
        public_lobby=None,
    ):
        self.en_confirmation_end_time = en_confirmation_end_time
        self.en_tournament_timezone = en_tournament_timezone
        self.ru_confirmation_end_time = ru_confirmation_end_time
        self.ru_tournament_timezone = ru_tournament_timezone
        self.en_discord_confirmation_channel = en_discord_confirmation_channel
        self.ru_discord_confirmation_channel = ru_discord_confirmation_channel
        self.public_lobby = public_lobby

    def is_valid(self):
        if self.en_confirmation_end_time is None:
            return False
        if self.en_tournament_timezone is None:
            return False
        if self.ru_confirmation_end_time is None:
            return False
        if self.en_tournament_timezone is None:
            return False
        if self.en_discord_confirmation_channel is None:
            return False
        if self.en_discord_confirmation_channel is None:
            return False
        if self.public_lobby is None:
            return False
        return True
