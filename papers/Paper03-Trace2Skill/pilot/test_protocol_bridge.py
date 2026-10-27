import unittest
from chat_adapter import BASE_URL,MODEL,Stopped
from protocol_bridge import responses_to_chat,chat_to_responses
from test_chat_adapter import response
class TestBridge(unittest.TestCase):
    def test_developer_mapping_and_model_substitution(self):
        r=responses_to_chat({'model':'historical-opus-alias','input':[{'role':'developer','content':'visible tool contract'},{'role':'user','content':[{'type':'input_text','text':'task'}]}]})
        self.assertEqual(r['url'],BASE_URL+'/chat/completions');self.assertEqual(r['json']['model'],MODEL);self.assertEqual(r['json']['messages'][0]['role'],'system')
    def test_tool_calls_and_outputs_preserve_call_id(self):
        r=responses_to_chat({'input':[{'role':'user','content':'compile'},{'type':'function_call','call_id':'c1','name':'iverilog','arguments':'{"args":"dut.v"}'},{'type':'function_call_output','call_id':'c1','output':'ok'}],'tools':[{'type':'function','name':'iverilog','parameters':{'type':'object'}}]})
        self.assertEqual(r['json']['messages'][-1]['tool_call_id'],'c1');self.assertEqual(r['json']['tools'][0]['function']['name'],'iverilog')
    def test_reverse_usage_and_tool_fields(self):
        calls=[{'id':'c1','type':'function','function':{'name':'iverilog','arguments':'{"args":"dut.v"}'}}]
        r=chat_to_responses(response(finish='tool_calls',calls=calls,content=None),['iverilog'])
        self.assertEqual(r['usage']['input_tokens'],10);self.assertEqual(r['output'][0]['call_id'],'c1');self.assertNotIn('reasoning',str(r))
    def test_unsupported_multimodal_or_reasoning_stops(self):
        for x in [{'role':'user','content':[{'type':'input_image','image_url':'x'}]},{'type':'reasoning','summary':[]}]:
            with self.assertRaises(Stopped):responses_to_chat({'input':[x]})
    def test_unknown_fields_stops(self):
        with self.assertRaises(Stopped):responses_to_chat({'input':'task','previous_response_id':'hidden-state'})
    def test_orphan_result_stops(self):
        with self.assertRaises(Stopped):responses_to_chat({'input':[{'type':'function_call_output','call_id':'orphan','output':'ok'}]})
    def test_pending_result_stops(self):
        with self.assertRaises(Stopped):responses_to_chat({'input':[{'type':'function_call','call_id':'c','name':'ls','arguments':'{}'}]})
    def test_length_response_is_marked_incomplete(self):
        self.assertEqual(chat_to_responses(response(finish='length'),[])['status'],'incomplete')
if __name__=='__main__':unittest.main(verbosity=2)
