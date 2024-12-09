import json

from starlette.datastructures import Headers
from starlette.responses import Response
from starlette.requests import ClientDisconnect
from starlette.types import ASGIApp, Receive, Scope, Send

class JsonRPCMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        if scope["path"] == "/":
            headers = Headers(scope=scope)
            ct = headers.get("Content-Type", "")
            if scope["method"] == "POST" and ct == "application/json":
                await self.call_rpc(scope, receive, send)
                return

        await self.app(scope, receive, send)

    async def call_rpc(self, scope: Scope, receive: Receive, send: Send) -> None:
        message = await self.get_full_message(receive)
        async def mod_receive():
            nonlocal message
            return message

        s = message["body"].decode('utf-8')
        pyld = json.loads(s)
        if pyld.get("jsonrpc") != "2.0":
            await self.app(scope, mod_receive, send)
            return

        method = pyld.get("method")
        params = pyld.get("params")
        id = pyld.get("id")
        if method == None or params == None:
            response = Response(status_code=400)
            await response(scope, receive, send)
            return

        scope["path"] = "/" + method
        ps = json.dumps(params)
        message["body"] = ps.encode('utf-8')


        startMsg = None
        async def mod_send(message):
            if message["type"] == "http.response.start":
                nonlocal startMsg
                startMsg = message # fix content-length later

            elif message["type"] == "http.response.body":
                body = self.create_reply(message["body"], id)
                message["body"] = body
                startMsg["headers"] = self.set_content_length(len(body), startMsg["headers"])

            await send(message)

        await self.app(scope, mod_receive, mod_send)

    def create_reply(self, body, id):
        #{"jsonrpc": "2.0", "result": 19, "id": 3}
        s = body.decode('utf-8')
        result = json.loads(s)
        reply = {
            "jsonrpc": "2.0",
            "result": result,
            "id": id,
        }
        return json.dumps(reply).encode('utf-8')

    def set_content_length(self, length, headers):
        def f(t):
            k = t[0].decode('utf-8')
            if k == "content-length":
                return (t[0], f"{length}".encode('utf-8'))
            return t

        l = list(map(f, headers))
        return l

    async def get_full_message(self, receive: Receive):
        message = None
        chunks: list[bytes] = []
        done = False

        async def g():
            nonlocal message, chunks, done
            while not done:
                m = await receive()
                if m["type"] == "http.request":
                    if message == None:
                        message = m
                    body = m.get("body", b"")
                    chunks.append(body)
                    if not m.get("more_body", False):
                        message[body] = chunks
                        done = True
                        yield message
                elif message["type"] == "http.disconnect":
                    raise ClientDisconnect()
            yield None

        async for _ in g():
            pass

        return message

def use_json_rpc_middleware(app):
    app.add_middleware(JsonRPCMiddleware)
