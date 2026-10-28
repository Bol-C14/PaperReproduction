"""Boundary tests; no network and no simulator execution."""
import json
import unittest
from unittest.mock import patch
import bridge

class Boundaries(unittest.TestCase):
    def setUp(self):
        self.fixture=bridge.TestController()
        self.domain=self.fixture.call(stage='initial_search_space',messages=bridge.request('initial_search_space',[]))
    def test_domain_capacity_and_seen(self):
        points=bridge.domain_points(self.domain)
        self.assertEqual(len(points),49)
        with self.assertRaises(ValueError):bridge.domain_points(self.domain,points,required=1)
    def test_fixed_variable(self):
        self.domain['optimization_configuration']['variables_to_optimize'].pop('W_nmos_base')
        self.domain['optimization_configuration']['variables_fixed']={'W_nmos_base':{'fixed_value':1.68}}
        self.assertEqual(len(bridge.domain_points(self.domain,required=7)),7)
        with self.assertRaises(ValueError):bridge.domain_points(self.domain)
    def test_invented_and_overlap_rejected(self):
        self.domain['optimization_configuration']['variables_to_optimize']['W_pmos_base']['search_space']=[999]
        with self.assertRaises(ValueError):bridge.domain_points(self.domain)
        self.setUp()
        self.domain['optimization_configuration']['variables_fixed']={'W_nmos_base':{'fixed_value':1.68}}
        with self.assertRaises(ValueError):bridge.domain_points(self.domain)
    def test_exact_boundary_infeasible(self):
        value=bridge.score(bridge.CFG,{'dc_gain_db':20.,'average_delay':50.,'dynamic_power':50.})
        self.assertFalse(value['feasible'])
    def test_missing_invalid_not_gp_label(self):
        value=bridge.score(bridge.CFG,{'dc_gain_db':None,'average_delay':12.,'dynamic_power':2.})
        self.assertFalse(value['measurement_valid'])
        self.assertIsNone(value['normalized_fom'])
    def test_fixture_reflection_requires_measurements(self):
        with self.assertRaises(ValueError):
            self.fixture.call(stage='outer_regeneration',messages=bridge.request('outer_regeneration',[]))
    def test_no_network_on_fixture_or_request(self):
        with patch('urllib.request.urlopen',side_effect=AssertionError('No network permitted')):
            for stage in ('circuit_understanding','initial_search_space','inner_iteration'):
                response=self.fixture.call(stage=stage,messages=bridge.request(stage,[]))
                bridge.validate(stage,response)
    def test_api_gate_fails_before_network(self):
        with self.assertRaises(RuntimeError):bridge.APIBridgeController()
        with self.assertRaises(ValueError):bridge.APIBridgeController(authorized=True)
    def test_runtime_fields_not_sent(self):
        text=json.dumps(bridge.request('circuit_understanding',[]))
        self.assertNotIn('/home/',text)
        self.assertNotIn('/Users/',text)
        self.assertNotIn('pdk_lib_path',text)

if __name__=='__main__':unittest.main()
