import logging
from models._baseModels.Model import Model
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

class Model_iter (Model):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
