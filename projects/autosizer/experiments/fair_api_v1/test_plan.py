"""Small synthetic accounting and units tests; never starts API/simulator."""
import unittest
import yaml
from plan import PROJECT,make_plan,fork_observations,validate_launch_balance,independent_parse,independent_score

def attempts(points,start):
    return [{'indices':p,'attempt_id':start+i,'process_id':'SYNTHETIC_PROCESS_'+str(start+i),
             'spawn_confirmed':True,'status':'valid_infeasible','metrics':{'synthetic':True}}
            for i,p in enumerate(points)]

class Fairness(unittest.TestCase):
    def setUp(self):
        self.plan=make_plan()
        self.common=attempts(self.plan['initial_indices'],0)
        unseen=[p for p in self.plan['initial_domain'] if p not in self.plan['initial_indices']]
        self.guided=attempts(unseen[:24],10)
        self.control=attempts(unseen[:24],34)
    def test_identical_initial_data_without_shared_mutable_state(self):
        fork=fork_observations(self.common)
        self.assertEqual(fork['api_guided'],fork['fixed_gp'])
        fork['api_guided'][0]['metrics']['synthetic']=False
        self.assertTrue(fork['fixed_gp'][0]['metrics']['synthetic'])
    def test_source_units_targets_and_width_mapping(self):
        source=yaml.safe_load((PROJECT/'upstream/inverter.yaml').read_text())
        self.assertEqual(source['user_specs_metric'],'fom > 1.0 AND dc_gain_db > 20 AND average_delay < 50 AND dynamic_power < 50')
        self.assertEqual(float(source['metric_post']['average_delay']['scale']),1e12)
        self.assertEqual(float(source['metric_post']['dynamic_power']['scale']),1e6)
        self.assertEqual(source['width_scales']['W_pmos'],['W_pmos_base',20])
        self.assertEqual(source['width_scales']['W_nmos'],['W_nmos_base',20])
    def test_exact_physical_budget_common_counted_once(self):
        result=validate_launch_balance(self.common,self.guided,self.control)
        self.assertEqual(result['total_physical_search_launches'],58)
        self.assertEqual(self.plan['physical_stage_attempt_cap'],63)
        self.assertEqual(self.plan['observation_budget_per_arm'],34)
    def test_shared_cached_arm_process_rejected(self):
        self.control[0]['process_id']=self.guided[0]['process_id']
        with self.assertRaises(ValueError):validate_launch_balance(self.common,self.guided,self.control)
    def test_early_stop_and_unconfirmed_spawn_are_not_matched(self):
        with self.assertRaises(ValueError):validate_launch_balance(self.common,self.guided[:-1],self.control)
        with self.assertRaises(ValueError):fork_observations(list(reversed(self.common)))
        self.guided[0]['spawn_confirmed']=False
        with self.assertRaises(ValueError):validate_launch_balance(self.common,self.guided,self.control)
    def test_raw_seconds_watts_unit_conversion(self):
        value=independent_parse('dc_gain_db = 24\naverage_delay = 2E-11\ndynamic_power_timeweighted = 4E-5\n')
        self.assertEqual(value,{'dc_gain_db':24.,'average_delay':20.,'dynamic_power':40.})
    def test_boundaries_and_nonpositive_metrics_rejected(self):
        self.assertFalse(independent_score({'dc_gain_db':20.,'average_delay':50.,'dynamic_power':50.})['feasible'])
        self.assertFalse(independent_score({'dc_gain_db':24.,'average_delay':20.,'dynamic_power':65.})['feasible'])
        with self.assertRaises(ValueError):independent_score({'dc_gain_db':24.,'average_delay':0.,'dynamic_power':40.})
        with self.assertRaises(ValueError):independent_parse('dc_gain_db = 24\naverage_delay = 2e-11\n')

if __name__=='__main__':unittest.main()
