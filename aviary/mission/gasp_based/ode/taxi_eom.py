import numpy as np
import openmdao.api as om

from aviary.utils.aviary_values import AviaryValues
from aviary.variable_info.functions import add_aviary_input
from aviary.variable_info.variables import Dynamic, Mission


class TaxiFuelComponent(om.ExplicitComponent):
    """
    Compute the fuel consumed during taxi and update the mass after taxi in a 2DOF mission.
    """

    def initialize(self):
        self.options.declare('num_nodes', default=1, types=int)
        self.options.declare(
            'aviary_options', types=AviaryValues,
            desc='collection of Aircraft/Mission specific options')

    def setup(self):
        nn = self.options['num_nodes']

        self.add_input(
            Dynamic.Mission.FUEL_FLOW_RATE_NEGATIVE_TOTAL,
            val=np.ones(nn),
            units="lbm/s",
            desc="fuel flow rate",
        )
        add_aviary_input(self, Mission.Summary.GROSS_MASS, val=175400.0)

        self.add_output(
            "taxi_fuel_consumed",
            val=np.ones(nn),
            units="lbm",
            desc="taxi_fuel_consumed",
        )
        self.add_output(
            Dynamic.Mission.MASS,
            val=np.ones(nn)*175000.0,
            units="lbm",
            desc="mass after taxi",
        )

    def setup_partials(self):
        nn = self.options['num_nodes']
        arange = np.arange(nn)

        self.declare_partials(
            "taxi_fuel_consumed", [
                Dynamic.Mission.FUEL_FLOW_RATE_NEGATIVE_TOTAL],
            rows=arange, cols=arange)
        self.declare_partials(
            Dynamic.Mission.MASS, Dynamic.Mission.FUEL_FLOW_RATE_NEGATIVE_TOTAL,
            rows=arange, cols=arange)
        self.declare_partials(
            Dynamic.Mission.MASS, Mission.Summary.GROSS_MASS, val=np.ones(nn))

    def compute(self, inputs, outputs):
        fuelflow, takeoff_mass = inputs.values()
        dt_taxi = self.options['aviary_options'].get_val(Mission.Taxi.DURATION, 's')
        outputs["taxi_fuel_consumed"] = -fuelflow * dt_taxi
        outputs[Dynamic.Mission.MASS] = takeoff_mass - outputs["taxi_fuel_consumed"]

    def compute_partials(self, inputs, J):
        nn = self.options['num_nodes']

        dt_taxi = self.options['aviary_options'].get_val(Mission.Taxi.DURATION, 's')

        J["taxi_fuel_consumed", Dynamic.Mission.FUEL_FLOW_RATE_NEGATIVE_TOTAL] = -dt_taxi

        J[Dynamic.Mission.MASS, Dynamic.Mission.FUEL_FLOW_RATE_NEGATIVE_TOTAL] = dt_taxi
