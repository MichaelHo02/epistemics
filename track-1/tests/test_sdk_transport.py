"""Exercise the installed Adaption SDK serializer/parser without network access."""
import json
import tempfile
import unittest
import httpx
from adaption import Adaption
from epistemics_dataset.adaption_client import translate
from epistemics_dataset.seeds import make_seeds, render


class SDKTransportCheck(unittest.TestCase):
    def test_real_sdk_request_and_response(self):
        seed = make_seeds()[0]
        def handler(request):
            body = json.loads(request.content)
            self.assertEqual(body["model"], "mock-model")
            self.assertFalse(body["store"])
            payload = json.loads(body["input"])
            self.assertEqual(payload["language"], "vi")
            self.assertNotIn("gold_code", payload)
            text = {k: render(seed, "vi")[k] for k in ("question", "source")}
            return httpx.Response(200, json={
                "id": "mock-response", "object": "response", "created_at": 0,
                "model": "mock-model", "status": "completed", "output_text": json.dumps(text),
                "output": [{"type": "message", "id": "msg_mock", "role": "assistant",
                            "content": [{"type": "output_text", "text": json.dumps(text), "annotations": []}]}],
                "usage": {"input_tokens": 10, "output_tokens": 10, "total_tokens": 20}})
        with httpx.Client(transport=httpx.MockTransport(handler)) as http:
            with Adaption(api_key="mock-not-a-secret", http_client=http, max_retries=0) as client:
                with tempfile.TemporaryDirectory() as cache:
                    row = translate(seed, "vi", "mock-model", cache, client)
                    self.assertEqual(row["source"], render(seed, "vi")["source"])
                    self.assertEqual(row["provenance"]["response_id"], "mock-response")
