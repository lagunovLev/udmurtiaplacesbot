import threading

import flask
from asgiref.wsgi import WsgiToAsgi
from telegram.ext import CallbackQueryHandler, Application

from app import app
import main
import os
import env_variables
from tg import *
import asyncio
import uvicorn


async def run():
    application = configure_application()

    @app.route("/" + env_variables.secret_key, methods=['POST'])
    async def webhook():
        await application.update_queue.put(Update.de_json(data=flask.request.json, bot=application.bot))
        return '!', 200

    await application.bot.set_webhook(url=f"{env_variables.url}/{env_variables.secret_key}", allowed_updates=Update.ALL_TYPES)

    webserver = uvicorn.Server(
        config=uvicorn.Config(
            app=WsgiToAsgi(app),
            port=8080,
            use_colors=False,
            host="0.0.0.0",
        )
    )

    async with application:
        await application.start()
        await webserver.serve()
        await application.stop()


if __name__ == '__main__':
    if os.getenv('DEPLOYING'):
        asyncio.run(run())
    else:
        th = threading.Thread(target=lambda: app.run(host="0.0.0.0", port=8080))
        th.start()
        application = configure_application()
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        th.join()
