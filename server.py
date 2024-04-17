from decimal import ExtendedContext
import json
from urllib import request
from aiohttp import web
from logger import logger

import asyncio
import config
import bot

routes = web.RouteTableDef()

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "chrome-extension://bdieafbllidjamameipekbmodcangibp",
    "Access-Control-Allow-Methods": "GET",
    "Access-Control-Allow-Headers": "api_key",
}


@routes.options("/{path:.*}")
async def handle_options(request):
    headers = {
        "Access-Control-Allow-Origin": "chrome-extension://bdieafbllidjamameipekbmodcangibp",  # Или более конкретный домен
        "Access-Control-Allow-Methods": "POST, GET, OPTIONS",  # Указать методы, которые вы поддерживаете
        "Access-Control-Allow-Headers": "Content-Type, api_key",  # Указать заголовки, которые вы поддерживаете
        "Access-Control-Max-Age": "86400",  # 86400 секунд (24 часа)
    }
    return web.Response(headers=headers, status=204)  # 204 No Content


@routes.post("/v1/vea/attempt/forbidden_word")
async def attempt_forbidden_word(request):
    data = await request.json()

    required_fields = ["username", "api_key", "banword", "login_time"]
    missing_fields = [field for field in required_fields if field not in data]

    if missing_fields:
        return web.Response(
            text=f"Missing fields {', '.join(missing_fields)}",
            status=400,
            headers=CORS_HEADERS,
        )

    if data["api_key"] != config.API_KEY:
        return web.Response(text="Invalid API key", status=403, headers=CORS_HEADERS)

    await bot.send_banword_attempt(data)

    return web.Response(text="Accepted", status=200, headers=CORS_HEADERS)


@routes.get("/v1/vea/attempt/uninstall")
async def attempt_uninstall(request):
    username = request.query.get("username")
    api_key = request.query.get("key")
    login_time = request.query.get("login_time")

    required_fields = ["username", "key", "login_time"]
    missing_fields = [
        field for field in required_fields if request.query.get(field) is None
    ]

    if missing_fields:
        return web.Response(
            text=f"Missing fields {', '.join(missing_fields)}",
            status=400,
            headers=CORS_HEADERS,
        )
    # Проверка значения api_key
    if api_key != config.API_KEY:
        return web.Response(text="Invalid API key", status=403, headers=CORS_HEADERS)

    await bot.send_uninstall_attempt({"login_time": login_time, "username": username})

    raise web.HTTPFound("https://onlyfans.com")


@routes.get("/v1/vea/banwords")
async def get_banwords(request):
    api_key = request.query.get("api_key")
    if api_key != config.API_KEY:
        return web.Response(text="Invalid API key", status=403, headers=CORS_HEADERS)

    try:
        with open("banwords.txt", "r") as file:
            banwords = file.read().split(", ")
            banwords_json = json.dumps(banwords)
        return web.Response(
            text=banwords_json,
            content_type="application/json",
            status=200,
            headers=CORS_HEADERS,
        )
    except FileNotFoundError:
        return web.Response(text="Not found banwords", status=404, headers=CORS_HEADERS)


async def start():
    logger.info("starting server")
    try:
        global app
        app = web.Application()
        app.router.add_routes(routes)

        runner = web.AppRunner(app)
        await runner.setup()

        site = web.TCPSite(runner, port=15000, host="0.0.0.0")
        await site.start()

        logger.info("successful start")

        await asyncio.Event().wait()
    except Exception as e:
        logger.error("error on server start: " + str(e))
