import sys
import numpy as np
import logging
from Model import Model
import pandas as pd

#TODO add conversions and possibility to change names from what is written in the CSV
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

class Controller (Model):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def step(self, ts, **kwargs):
        pass

        # return super().step(ts)

    def finalize(self):
        return super().finalize()
