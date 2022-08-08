import environs

class Configuration(environs.Env):
    def __init__(self, **kwargs): # Use same parameter signature as parent (eager=True, expand_vars=False)
        super().__init__(**kwargs)
        self.read_env()

if __name__ == "__main__":
    # For debugging while developing
    config = Configuration()
    print(config('PATH'))



