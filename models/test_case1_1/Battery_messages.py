import numpy as np
from Model import Model #rember the top level running python script is al;ways main
import logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

class BESS:
    def __init__(self, **kwargs):
        """

        :param kwargs:
        """
        # load parameters
        kwargs = {k.lower(): v for k, v in kwargs.items()}

        if 'rated_capacity' in kwargs:
            self.rated_capacity = kwargs['rated_capacity']
        else:
            self.rated_capacity = 300

        if 'maximum_charge_power' in kwargs:
            self.maximum_charge_power = kwargs['maximum_charge_power']
        else:
            self.maximum_charge_power = 65

        if 'maximum_discharge_power' in kwargs:
            self.maximum_discharge_power = kwargs['maximum_discharge_power']
        else:
            self.maximum_discharge_power = 65

        if 'SOC_upper_limit' in kwargs:
            self.SOC_upper_limit = kwargs['SOC_upper_limit']
        else:
            self.SOC_upper_limit = 0.95

        if 'SOC_lower_limit' in kwargs:
            self.SOC_lower_limit = kwargs['SOC_lower_limit']
        else:
            self.SOC_lower_limit = 0.25

        if 'charge_efficiency' in kwargs:
            self.charge_efficiency = kwargs['charge_efficiency']
        else:
            self.charge_efficiency = 1

        if 'discharge_efficiency' in kwargs:
            self.discharge_efficiency = kwargs['discharge_efficiency']
        else:
            self.discharge_efficiency = 1

        if 'self_discharge_rate' in kwargs:
            self.self_discharge_rate = kwargs['self_discharge_rate']
        else:
            self.self_discharge_rate = 0

        self.SOC = np.nan

    def setSOC(self, SOC):
        """
        set SOC, especially when initializing the BESS
        :param SOC:
        :return:
        """
        if SOC >= self.SOC_lower_limit and SOC <= self.SOC_upper_limit:
            self.SOC = SOC
        elif SOC < self.SOC_lower_limit:
            self.SOC = self.SOC_lower_limit
        else:
            self.SOC = self.SOC_upper_limit

    def getlegalpower(self, power):
        """
        get the legal value of charging/discharging power
        :param power: the expected charging/discharging power; (+) means charging, (-) means discharging
        :return: the legal value of power, which is below the maximum of power
        """
        if power > 0:  # charging
            power_legal = min(power, self.maximum_charge_power)
        elif power < 0:  # discharging
            power_legal = max(power, -self.maximum_discharge_power)
        else:
            power_legal = 0
        return power_legal

    def calculatepower(self, power, **kwargs):
        """
        calculate the charging/discharging process of BESS by a timestep; after charging/discharging, SOC is updated
        :param power: the expected charging/discharging power; (+) means charging, (-) means discharging
        :param kwargs: dt - timestep (s)
        :return: the actual energy received or supplied by BESS within a timestep
        """
        dt = kwargs['dt']  # in seconds
        power_legal = self.getlegalpower(power)
        if power_legal >= 0:
            efficiency = self.charge_efficiency
        else:
            efficiency = 1 / self.discharge_efficiency

        SOC = (self.SOC * self.rated_capacity + power_legal * dt / 3600 * efficiency) / self.rated_capacity
        Energy_last = self.getE()
        self.setSOC(SOC)
        Energy_now = self.getE()
        Energy_out = (Energy_now - Energy_last) / efficiency

        return Energy_out

    def getE(self):
        """
        :return: the current remaining energy in BESS
        """
        return self.SOC * self.rated_capacity

    def getSOC(self):
        """
        :return: the current SOC of the BESS
        """
        return self.SOC

class Battery(Model):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model = None
        self.initialization()
    def initialization(self):
        self.model = BESS()
        for par in self.params:
            setattr(self.model, par, self.params[par])
        self.model.setSOC(self.model.SOC)

    def step(self, ts):

        logger.debug(f'messages {self.messages_in}')
        input_power = sum([float(i) for i in self.messages_in['power']])

        self.messages_out['energy_out'] = self.model.calculatepower(input_power, dt=3600)
        self.params['SOC'] = self.model.SOC

        return super().step(ts)

    def finalize(self):
        return super().finalize()
        pass