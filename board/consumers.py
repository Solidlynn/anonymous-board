import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Post, Comment


class BoardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = 'board_updates'
        self.room_group_name = f'board_{self.room_name}'

        # 그룹에 참가
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # 그룹에서 나가기
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # 클라이언트에서 메시지 받기
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type')
        
        if message_type == 'new_post':
            await self.handle_new_post(text_data_json)
        elif message_type == 'new_comment':
            await self.handle_new_comment(text_data_json)
        elif message_type == 'update_reaction':
            await self.handle_update_reaction(text_data_json)

    async def handle_new_post(self, data):
        # 새 게시글 그룹에 브로드캐스트
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'broadcast_update',
                'update_type': 'new_post',
                'message': '새로운 게시글이 작성되었습니다.',
                'data': data
            }
        )

    async def handle_new_comment(self, data):
        # 새 댓글 그룹에 브로드캐스트
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'broadcast_update',
                'update_type': 'new_comment',
                'message': '새로운 댓글이 작성되었습니다.',
                'data': data
            }
        )

    async def handle_update_reaction(self, data):
        # 반응 업데이트 그룹에 브로드캐스트
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'broadcast_update',
                'update_type': 'reaction_update',
                'message': '반응이 업데이트되었습니다.',
                'data': data
            }
        )

    # 그룹에서 메시지 받기
    async def broadcast_update(self, event):
        # 클라이언트에 메시지 전송
        await self.send(text_data=json.dumps({
            'type': event['update_type'],
            'message': event['message'],
            'data': event['data']
        }))
