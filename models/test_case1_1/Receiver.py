from Model import Model
import logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)
class Receiver(Model):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model = None

    def step(self, ts, **kwargs):
        for msg in self.messages_in:
            logger.debug(f"\t\t\tmessage_received: {msg}")

        return super().step(ts)


    def finalize(self):
        return super().finalize()
        pass