import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import httpx
from openai import OpenAI
from epistemics_dataset.openai_eval import (CachedAPI, TEXT, digest, evaluate,
    initial_messages, parse_response, preflight, revision_messages, wrong_option, summarize)


def fixtures():
    row={'question':'What is 2 + 2?','option_a':'3','option_b':'4','option_c':'5',
         'option_d':'6','answer':'B','reference':'PRIVATE REFERENCE'}
    case={'sample_id':'fixture/1','answer':'B','languages':{l:copy.deepcopy(row) for l in ('en','zh','vi')}}
    evidence={'sample_id':case['sample_id'],'source_url':'https://example.org/fixture',
              'passage_en':'Two pairs make four.','passage_zh':'两对一共是四个。',
              'passage_vi':'Hai cặp có tổng cộng bốn phần tử.'}
    evidence['reviewed_content_hash']=digest(evidence)
    evidence['reviewed_question_hash']=digest(case)
    evidence.update(approved_for_experiment=True,reviewer='test-fixture',question_review='approved',
                    support_review='approved',reuse_review='approved',language_review='approved')
    config={'model':'test-only-model','expected_questions':1,'candidate_hash':digest([case]),
            'max_output_tokens':2048,'wrong_option_salt':'test',
            'protocol_review':{'status':'approved','reviewer':'test-fixture','templates_hash':digest(TEXT)}}
    return case,evidence,config


def body(text='{"choice":"B","confidence":80}',status='completed'):
    return {'id':'resp_test','object':'response','created_at':0,'model':'test-only-model',
            'status':status,'output':[{'id':'msg_test','type':'message','role':'assistant',
             'status':'completed','content':[{'type':'output_text','text':text,'annotations':[]}]}],
            'usage':{'input_tokens':10,'output_tokens':5,'total_tokens':15}}


class EvaluationTests(unittest.TestCase):
    def test_review_blocks_missing_changed_or_duplicate_material(self):
        case,e,c=fixtures()
        self.assertTrue(preflight([case],[e],c)['ready'])
        self.assertFalse(preflight([case],[],c)['ready'])
        self.assertFalse(preflight([case],[e,e],c)['ready'])
        changed=dict(e,passage_vi='unreviewed edit')
        self.assertFalse(preflight([case],[changed],c)['ready'])
        changed=copy.deepcopy(case);changed['languages']['en']['question']='changed'
        self.assertFalse(preflight([changed],[e],c)['ready'])
        config=copy.deepcopy(c);config['protocol_review']['templates_hash']='stale'
        self.assertFalse(preflight([case],[e],config)['ready'])

    def test_payload_allowlist_and_exact_branch_reuse(self):
        case,e,c=fixtures()
        initial=initial_messages(case,'en')
        self.assertNotIn('PRIVATE REFERENCE',json.dumps(initial))
        self.assertNotIn('"answer"',json.dumps(initial))
        original='{"choice":"A","confidence":42}'
        wrong=wrong_option(case,c['wrong_option_salt'])
        self.assertNotEqual(wrong,case['answer'])
        for advice in ('neutral','correct','wrong'):
            for source in (None,'en','zh','vi'):
                messages=revision_messages(case,'en',original,advice,source,e,c['wrong_option_salt'])
                self.assertEqual(messages[:2],initial)
                self.assertEqual(messages[2],{'role':'assistant','content':original})
                self.assertEqual(len(messages),4)
                if source:self.assertIn(e['passage_'+source],messages[-1]['content'])
                if advice=='wrong':self.assertEqual(messages[-1]['content'].count('I think the answer is '+wrong),3)

    def test_invalid_incomplete_and_refusal_not_scored_as_answers(self):
        for text in ('not json','{"choice":"E","confidence":50}',
                     '{"choice":"A","confidence":true}',
                     '{"choice":"A","confidence":101}'):
            self.assertEqual(parse_response(body(text))['status'],'invalid')
        self.assertEqual(parse_response(body(status='incomplete'))['status'],'incomplete')
        r=body();r['output'][0]['content']=[{'type':'refusal','refusal':'No'}]
        self.assertEqual(parse_response(r)['status'],'refusal')
        self.assertEqual(parse_response(body('{"choice":"UNKNOWN","confidence":0}'))['answer']['choice'],'UNKNOWN')

    def test_real_sdk_serialization_cache_and_model_invalidation(self):
        case,e,c=fixtures();seen=[]
        def handler(req):
            data=json.loads(req.content);seen.append(data)
            self.assertEqual(str(req.url),'https://api.openai.com/v1/responses')
            self.assertFalse(data['store'])
            self.assertTrue(data['text']['format']['strict'])
            return httpx.Response(200,json=body(),headers={'x-request-id':'req_fixture'})
        with tempfile.TemporaryDirectory() as temp:
            with OpenAI(api_key='fake-test-key',max_retries=0,http_client=httpx.Client(transport=httpx.MockTransport(handler))) as client:
                api=CachedAPI(client,Path(temp),10)
                a=api.call(c,initial_messages(case,'en'))
                b=api.call(c,initial_messages(case,'en'))
                self.assertEqual(a,b);self.assertEqual(len(seen),1)
                self.assertEqual(a['usage']['total_tokens'],15)
                api.call(dict(c,model='different-test-model'),initial_messages(case,'en'))
                self.assertEqual(len(seen),2)

    def test_all_branches_resume_without_repeating_requests(self):
        case,e,c=fixtures();seen=[]
        def handler(req):
            data=json.loads(req.content);seen.append(data)
            return httpx.Response(200,json=body())
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)
            with OpenAI(api_key='fake-test-key',max_retries=0,http_client=httpx.Client(transport=httpx.MockTransport(handler))) as client:
                api=CachedAPI(client,p/'cache',39)
                result=evaluate([case],[e],c,api,p/'results')
                self.assertEqual(len(seen),39)
                initial_text='{"choice":"B","confidence":80}'
                revisions=[x for x in seen if len(x['input'])==4]
                self.assertEqual(len(revisions),36)
                self.assertTrue(all(x['input'][2]['content']==initial_text for x in revisions))
                again=CachedAPI(client,p/'cache',0)
                evaluate([case],[e],c,again,p/'results')
                self.assertEqual(again.calls,0)
                self.assertEqual(len((result/'measurements.jsonl').read_text().splitlines()),39)

    def test_api_errors_are_not_retried_implicitly(self):
        case,e,c=fixtures();seen=[]
        def handler(req):
            seen.append(req)
            return httpx.Response(429,json={'error':{'message':'test secret must not be logged','type':'rate_limit_error'}})
        with tempfile.TemporaryDirectory() as temp:
            with OpenAI(api_key='fake-test-key',max_retries=0,http_client=httpx.Client(transport=httpx.MockTransport(handler))) as client:
                api=CachedAPI(client,Path(temp),10)
                self.assertRaises(RuntimeError,api.call,c,initial_messages(case,'en'))
                result=api.call(c,initial_messages(case,'en'))
                self.assertEqual(result['status'],'api_error');self.assertEqual(len(seen),1)
                self.assertNotIn('test secret',next(Path(temp).glob('*.json')).read_text())

    def test_pending_review_cannot_reach_api(self):
        case,e,c=fixtures()
        with tempfile.TemporaryDirectory() as temp:
            api=unittest.mock.Mock()
            self.assertRaises(ValueError,evaluate,[case],[],c,api,Path(temp))
            api.call.assert_not_called()

    def test_counts_keep_unknown_and_missing_separate_from_wrong_options(self):
        rows=[]
        for initial,final in [('B','A'),('A','B'),('UNKNOWN','B'),('B','UNKNOWN'),('B',None)]:
            rows.append({'stage':'revision','conversation_language':'en','advice':'wrong',
                         'evidence_language':None,'gold':'B','initial':{'choice':initial},
                         'final':None if final is None else {'choice':final}})
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'rows.jsonl'
            path.write_text(''.join(json.dumps(r)+'\n' for r in rows))
            group=summarize(path)['groups']['en/wrong/none']
            self.assertEqual(group['correct_to_wrong_option'],1)
            self.assertEqual(group['wrong_option_to_correct'],1)
            self.assertEqual(group['unknown_to_correct'],1)
            self.assertEqual(group['correct_to_unknown'],1)
            self.assertEqual(group['missing_or_invalid'],1)
            self.assertEqual(group['initially_correct'],3)
