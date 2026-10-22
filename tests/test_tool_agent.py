import json
import unittest
from aries_math.tool_agent import run_tool_loop


def completion(message):
    return {"choices": [{"message": message, "finish_reason": "stop"}]}


class ToolLoopTests(unittest.IsolatedAsyncioTestCase):
    async def test_calculation_result_returns_to_model(self):
        calls = []
        async def provider(payload):
            calls.append(payload)
            if len(calls) == 1:
                return completion({"role": "assistant", "content": None, "tool_calls": [{
                    "id": "call-1", "type": "function",
                    "function": {"name": "aries_calculate", "arguments": json.dumps({
                        "operation": "dot_product",
                        "parameters": {"left": [2, 3], "right": [4, 5]}
                    })}
                }]})
            return completion({"role": "assistant", "content": "The dot product is 23."})
        def execute(op, params):
            self.assertEqual(op, "dot_product")
            return sum(a*b for a, b in zip(params["left"], params["right"]))
        result = await run_tool_loop({"model": "test", "messages": [{"role": "user", "content": "calculate"}]},
                                     provider, execute)
        self.assertEqual(result["choices"][0]["message"]["content"], "The dot product is 23.")
        self.assertEqual(json.loads(calls[1]["messages"][-1]["content"])["result"], 23)

    async def test_no_tool_call_returns_response(self):
        expected = completion({"role": "assistant", "content": "Hello."})
        async def provider(_payload): return expected
        self.assertEqual(await run_tool_loop({"model": "m", "messages": []}, provider, lambda *_: None), expected)

    async def test_unapproved_tool_is_not_executed(self):
        executed = []
        async def provider(payload):
            if len(payload["messages"]) == 1:
                return completion({"role": "assistant", "tool_calls": [{
                    "id": "bad", "type": "function",
                    "function": {"name": "run_shell", "arguments": "{}"}
                }]})
            return completion({"role": "assistant", "content": "Rejected."})
        await run_tool_loop({"model": "m", "messages": [{"role": "user", "content": "x"}]},
                            provider, lambda *args: executed.append(args))
        self.assertEqual(executed, [])

    async def test_invalid_json_is_reported_as_tool_error(self):
        seen = []
        async def provider(payload):
            if len(payload["messages"]) == 1:
                return completion({"role": "assistant", "tool_calls": [{
                    "id": "bad-json", "type": "function",
                    "function": {"name": "aries_calculate", "arguments": "not-json"}
                }]})
            seen.append(json.loads(payload["messages"][-1]["content"]))
            return completion({"role": "assistant", "content": "Invalid input."})
        await run_tool_loop({"model": "m", "messages": [{"role": "user", "content": "x"}]},
                            provider, lambda *_: 1)
        self.assertFalse(seen[0]["ok"])

    async def test_rounds_are_bounded(self):
        count = 0
        async def provider(_payload):
            nonlocal count
            count += 1
            return completion({"role": "assistant", "tool_calls": [{
                "id": str(count), "type": "function",
                "function": {"name": "aries_calculate", "arguments": json.dumps({
                    "operation": "gcd", "parameters": {"values": [6, 9]}
                })}
            }]})
        result = await run_tool_loop({"model": "m", "messages": [{"role": "user", "content": "loop"}]},
                                     provider, lambda *_: 3, max_rounds=2)
        self.assertTrue(result["aries_runtime"]["tool_loop_limited"])
        self.assertLessEqual(count, 3)

    async def test_client_cannot_override_tool_definitions(self):
        captured = []
        async def provider(payload):
            captured.append(payload)
            return completion({"role": "assistant", "content": "ok"})
        await run_tool_loop({"model": "m", "tools": [{"evil": True}], "messages": []},
                            provider, lambda *_: None)
        self.assertEqual(captured[0]["tools"][0]["function"]["name"], "aries_calculate")


if __name__ == "__main__":
    unittest.main()
