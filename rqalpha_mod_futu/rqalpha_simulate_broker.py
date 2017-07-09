#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2017 Futu, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from rqalpha.const import MATCHING_TYPE
from rqalpha.mod.rqalpha_mod_sys_simulation.simulation_broker import SimulationBroker

import six


class RQSimulateBroker(SimulationBroker):
    def __init__(self, env, mod_simu_config):
        mod_simu_config.matching_type = self.parse_matching_type(mod_simu_config.matching_type)
        super(RQSimulateBroker, self).__init__(env, mod_simu_config)

    def submit_order(self, order):
        # print("futu RQSimulateBroker submit_order.{}".format(order))
        super(RQSimulateBroker, self).submit_order(order)

    @staticmethod
    def parse_matching_type(me_str):
        assert isinstance(me_str, six.string_types)
        if me_str == "current_bar":
            return MATCHING_TYPE.CURRENT_BAR_CLOSE
        elif me_str == "next_bar":
            return MATCHING_TYPE.NEXT_BAR_OPEN
        elif me_str == "last":
            return MATCHING_TYPE.NEXT_TICK_LAST
        elif me_str == "best_own":
            return MATCHING_TYPE.NEXT_TICK_BEST_OWN
        elif me_str == "best_counterparty":
            return MATCHING_TYPE.NEXT_TICK_BEST_COUNTERPARTY
        else:
            raise NotImplementedError
