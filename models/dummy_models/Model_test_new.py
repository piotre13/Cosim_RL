
from _baseModels.Model import Model #rember the top level running python script is al;ways main
import logging
import pprint
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

pp = pprint.PrettyPrinter(indent=4)


class Test(Model):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for key, value in kwargs.items():
            setattr(self, key, value)

    def step(self, ts, **kwargs):

        for out in self.outputs:
            self.outputs[out] = ts
        self._fill_memory()
        # logger.debug(f"memory at ts {ts} = {pp.pformat(self.memory)}")



    def finalize(self):
        pass