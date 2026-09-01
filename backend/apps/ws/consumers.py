"""
WebSocket consumers.
- TaskConsumer: streams log lines for any running Celery task.
- PortfolioConsumer: pushes live P&L updates to the portfolio dashboard.
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer


class TaskConsumer(AsyncWebsocketConsumer):
    """
    Connect to ws://host/ws/tasks/<task_id>/
    The Celery tasks call group_send to this group, and we forward to the browser.
    """

    async def connect(self):
        self.task_id = self.scope["url_route"]["kwargs"]["task_id"]
        self.group_name = f"task_{self.task_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # Handler for group messages sent by Celery tasks
    async def task_log(self, event):
        message = event["message"]
        await self.send(text_data=json.dumps({
            "type": "log",
            "message": message,
            "done": message == "DONE",
            "error": message.startswith("ERROR:"),
        }))


class PortfolioConsumer(AsyncWebsocketConsumer):
    """
    Connect to ws://host/ws/portfolio/
    Receives portfolio_update group messages and forwards to browser.
    """

    GROUP_NAME = "portfolio_live"

    async def connect(self):
        await self.channel_layer.group_add(self.GROUP_NAME, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.GROUP_NAME, self.channel_name)

    async def portfolio_update(self, event):
        await self.send(text_data=json.dumps(event["data"]))
