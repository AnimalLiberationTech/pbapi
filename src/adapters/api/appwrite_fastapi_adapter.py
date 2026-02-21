from fastapi import FastAPI


class AppwriteFastAPIAdapter:
    def __init__(self, app: FastAPI):
        self.app = app

    async def handle(self, context):
        # Prepare scope for ASGI
        headers = []
        for key, value in context.req.headers.items():
            headers.append(
                (key.lower().encode("latin-1"), str(value).encode("latin-1"))
            )

        scope = {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.0"},
            "http_version": "1.1",
            "method": context.req.method,
            "scheme": "https",
            "path": context.req.path,
            "query_string": (
                context.req.query_string.encode("latin-1")
                if hasattr(context.req, "query_string")
                else b""
            ),
            "headers": headers,
            "appwrite_context": context,
        }

        response_body = b""
        response_status = 200
        response_headers = {}

        async def receive():
            return {
                "type": "http.request",
                "body": (
                    context.req.body_text.encode("utf-8")
                    if isinstance(context.req.body_text, str)
                    else (context.req.body_binary or b"")
                ),
                "more_body": False,
            }

        async def send(message):
            nonlocal response_body, response_status, response_headers
            if message["type"] == "http.response.start":
                response_status = message["status"]
                for key, value in message.get("headers", []):
                    response_headers[key.decode("latin-1")] = value.decode("latin-1")
            elif message["type"] == "http.response.body":
                response_body += message.get("body", b"")

        await self.app(scope, receive, send)

        # Return Appwrite response
        # Note: context.res.send or context.res.json depending on content type
        content_type = response_headers.get("content-type", "")

        # Binary or text?
        if "application/json" in content_type:
            import json

            try:
                data = json.loads(response_body.decode("utf-8"))
                return context.res.json(data, response_status)
            except:
                pass

        return context.res.send(
            response_body.decode("utf-8"), response_status, response_headers
        )


async def run_fastapi_on_appwrite(app: FastAPI, context):
    adapter = AppwriteFastAPIAdapter(app)
    return await adapter.handle(context)
