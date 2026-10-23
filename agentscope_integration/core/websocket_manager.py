# -*- coding: utf-8 -*-
"""
WebSocket管理器 - 管理WebSocket连接和实时通信
"""

import asyncio
import json
import logging
from typing import Dict, List, Set, Any, Optional
from datetime import datetime
import uuid

from fastapi import WebSocket, WebSocketDisconnect


class WebSocketConnection:
    """WebSocket连接封装"""
    
    def __init__(self, websocket: WebSocket, client_id: str):
        self.websocket = websocket
        self.client_id = client_id
        self.connected_at = datetime.now()
        self.subscriptions: Set[str] = set()
        self.metadata: Dict[str, Any] = {}
    
    async def send_message(self, message: Dict[str, Any]):
        """发送消息"""
        try:
            await self.websocket.send_text(json.dumps(message))
        except Exception as e:
            logging.getLogger(__name__).error(f"Failed to send message to {self.client_id}: {e}")
            raise
    
    def subscribe(self, event_type: str):
        """订阅事件类型"""
        self.subscriptions.add(event_type)
    
    def unsubscribe(self, event_type: str):
        """取消订阅事件类型"""
        self.subscriptions.discard(event_type)
    
    def is_subscribed(self, event_type: str) -> bool:
        """检查是否订阅了指定事件类型"""
        return event_type in self.subscriptions


class WebSocketManager:
    """WebSocket管理器 - 处理实时通信和事件广播"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 连接管理
        self.connections: Dict[str, WebSocketConnection] = {}
        self.connection_groups: Dict[str, Set[str]] = {}  # 连接分组
        
        # 消息队列和缓存
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.event_cache: List[Dict[str, Any]] = []  # 缓存最近的事件
        self.max_cache_size = 100
        
        # 统计信息
        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "messages_received": 0,
            "events_broadcasted": 0
        }
        
        # 启动消息处理器
        asyncio.create_task(self._message_processor())
        
        self.logger.info("WebSocketManager initialized")
    
    async def connect(self, websocket: WebSocket, client_id: Optional[str] = None) -> str:
        """接受WebSocket连接"""
        await websocket.accept()
        
        if not client_id:
            client_id = str(uuid.uuid4())
        
        connection = WebSocketConnection(websocket, client_id)
        self.connections[client_id] = connection
        
        # 更新统计
        self.stats["total_connections"] += 1
        self.stats["active_connections"] = len(self.connections)
        
        self.logger.info(f"WebSocket client {client_id} connected")
        
        # 发送连接确认消息
        await connection.send_message({
            "type": "connection_established",
            "client_id": client_id,
            "timestamp": datetime.now().isoformat()
        })
        
        # 发送缓存的事件
        await self._send_cached_events(connection)
        
        # 广播新连接事件
        await self.broadcast_event("client_connected", {
            "client_id": client_id,
            "timestamp": datetime.now().isoformat()
        }, exclude_clients={client_id})
        
        return client_id
    
    def disconnect(self, websocket: WebSocket):
        """断开WebSocket连接"""
        client_id = None
        
        # 查找对应的连接
        for cid, connection in self.connections.items():
            if connection.websocket == websocket:
                client_id = cid
                break
        
        if client_id:
            # 从所有分组中移除
            for group_clients in self.connection_groups.values():
                group_clients.discard(client_id)
            
            # 移除连接
            del self.connections[client_id]
            
            # 更新统计
            self.stats["active_connections"] = len(self.connections)
            
            self.logger.info(f"WebSocket client {client_id} disconnected")
            
            # 广播断连事件
            asyncio.create_task(self.broadcast_event("client_disconnected", {
                "client_id": client_id,
                "timestamp": datetime.now().isoformat()
            }))
    
    async def handle_message(self, websocket: WebSocket, message: str):
        """处理接收到的消息"""
        try:
            data = json.loads(message)
            self.stats["messages_received"] += 1
            
            # 查找连接
            connection = None
            for conn in self.connections.values():
                if conn.websocket == websocket:
                    connection = conn
                    break
            
            if not connection:
                self.logger.warning("Received message from unknown connection")
                return
            
            await self._process_client_message(connection, data)
            
        except json.JSONDecodeError:
            self.logger.error(f"Invalid JSON message: {message}")
        except Exception as e:
            self.logger.error(f"Error handling message: {e}")
    
    async def _process_client_message(self, connection: WebSocketConnection, data: Dict[str, Any]):
        """处理客户端消息"""
        message_type = data.get("type")
        
        if message_type == "subscribe":
            # 订阅事件
            event_types = data.get("event_types", [])
            for event_type in event_types:
                connection.subscribe(event_type)
            
            await connection.send_message({
                "type": "subscription_confirmed",
                "event_types": event_types,
                "timestamp": datetime.now().isoformat()
            })
            
        elif message_type == "unsubscribe":
            # 取消订阅
            event_types = data.get("event_types", [])
            for event_type in event_types:
                connection.unsubscribe(event_type)
            
            await connection.send_message({
                "type": "unsubscription_confirmed",
                "event_types": event_types,
                "timestamp": datetime.now().isoformat()
            })
            
        elif message_type == "join_group":
            # 加入分组
            group_name = data.get("group_name")
            if group_name:
                if group_name not in self.connection_groups:
                    self.connection_groups[group_name] = set()
                self.connection_groups[group_name].add(connection.client_id)
                
                await connection.send_message({
                    "type": "group_joined",
                    "group_name": group_name,
                    "timestamp": datetime.now().isoformat()
                })
        
        elif message_type == "leave_group":
            # 离开分组
            group_name = data.get("group_name")
            if group_name and group_name in self.connection_groups:
                self.connection_groups[group_name].discard(connection.client_id)
                
                await connection.send_message({
                    "type": "group_left",
                    "group_name": group_name,
                    "timestamp": datetime.now().isoformat()
                })
        
        elif message_type == "ping":
            # 心跳检测
            await connection.send_message({
                "type": "pong",
                "timestamp": datetime.now().isoformat()
            })
        
        elif message_type == "get_status":
            # 获取状态信息
            await connection.send_message({
                "type": "status_response",
                "data": await self.get_status(),
                "timestamp": datetime.now().isoformat()
            })
        
        else:
            self.logger.warning(f"Unknown message type: {message_type}")
    
    async def send_to_client(self, client_id: str, message: Dict[str, Any]):
        """发送消息给指定客户端"""
        if client_id in self.connections:
            try:
                await self.connections[client_id].send_message(message)
                self.stats["messages_sent"] += 1
            except Exception as e:
                self.logger.error(f"Failed to send message to client {client_id}: {e}")
                # 移除失效连接
                await self._remove_dead_connection(client_id)
    
    async def send_to_group(self, group_name: str, message: Dict[str, Any]):
        """发送消息给指定分组"""
        if group_name in self.connection_groups:
            tasks = []
            for client_id in self.connection_groups[group_name].copy():
                tasks.append(self.send_to_client(client_id, message))
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
    
    async def broadcast_message(self, message: Dict[str, Any], exclude_clients: Optional[Set[str]] = None):
        """广播消息给所有连接的客户端"""
        exclude_clients = exclude_clients or set()
        
        tasks = []
        for client_id in list(self.connections.keys()):
            if client_id not in exclude_clients:
                tasks.append(self.send_to_client(client_id, message))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def broadcast_event(self, event_type: str, data: Dict[str, Any], exclude_clients: Optional[Set[str]] = None):
        """广播事件给订阅的客户端"""
        exclude_clients = exclude_clients or set()
        
        event_message = {
            "type": "event",
            "event_type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        # 缓存事件
        self._cache_event(event_message)
        
        # 发送给订阅的客户端
        tasks = []
        for client_id, connection in self.connections.items():
            if (client_id not in exclude_clients and 
                connection.is_subscribed(event_type)):
                tasks.append(self.send_to_client(client_id, event_message))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        self.stats["events_broadcasted"] += 1
    
    def _cache_event(self, event: Dict[str, Any]):
        """缓存事件"""
        self.event_cache.append(event)
        
        # 限制缓存大小
        if len(self.event_cache) > self.max_cache_size:
            self.event_cache = self.event_cache[-self.max_cache_size:]
    
    async def _send_cached_events(self, connection: WebSocketConnection):
        """发送缓存的事件给新连接"""
        for event in self.event_cache[-10:]:  # 发送最近10个事件
            try:
                await connection.send_message(event)
            except Exception as e:
                self.logger.error(f"Failed to send cached event: {e}")
                break
    
    async def _remove_dead_connection(self, client_id: str):
        """移除失效连接"""
        if client_id in self.connections:
            # 从所有分组中移除
            for group_clients in self.connection_groups.values():
                group_clients.discard(client_id)
            
            # 移除连接
            del self.connections[client_id]
            
            # 更新统计
            self.stats["active_connections"] = len(self.connections)
            
            self.logger.info(f"Removed dead connection: {client_id}")
    
    async def _message_processor(self):
        """消息处理器（后台任务）"""
        while True:
            try:
                # 这里可以处理队列中的消息
                # 目前主要用于清理失效连接
                await asyncio.sleep(30)  # 每30秒检查一次
                await self._cleanup_dead_connections()
                
            except Exception as e:
                self.logger.error(f"Error in message processor: {e}")
                await asyncio.sleep(5)
    
    async def _cleanup_dead_connections(self):
        """清理失效连接"""
        dead_connections = []
        
        for client_id, connection in self.connections.items():
            try:
                # 发送心跳检测
                await connection.send_message({
                    "type": "ping",
                    "timestamp": datetime.now().isoformat()
                })
            except Exception:
                dead_connections.append(client_id)
        
        # 移除失效连接
        for client_id in dead_connections:
            await self._remove_dead_connection(client_id)
        
        if dead_connections:
            self.logger.info(f"Cleaned up {len(dead_connections)} dead connections")
    
    async def get_status(self) -> Dict[str, Any]:
        """获取WebSocket管理器状态"""
        return {
            "active_connections": len(self.connections),
            "connection_groups": {
                group: len(clients) for group, clients in self.connection_groups.items()
            },
            "cached_events": len(self.event_cache),
            "stats": self.stats.copy(),
            "connections": [
                {
                    "client_id": conn.client_id,
                    "connected_at": conn.connected_at.isoformat(),
                    "subscriptions": list(conn.subscriptions),
                    "metadata": conn.metadata
                }
                for conn in self.connections.values()
            ]
        }
    
    async def get_connection_info(self, client_id: str) -> Optional[Dict[str, Any]]:
        """获取连接信息"""
        if client_id in self.connections:
            connection = self.connections[client_id]
            return {
                "client_id": client_id,
                "connected_at": connection.connected_at.isoformat(),
                "subscriptions": list(connection.subscriptions),
                "metadata": connection.metadata,
                "groups": [
                    group for group, clients in self.connection_groups.items()
                    if client_id in clients
                ]
            }
        return None
    
    async def close_all(self):
        """关闭所有连接"""
        self.logger.info("Closing all WebSocket connections...")
        
        # 发送关闭通知
        close_message = {
            "type": "server_shutdown",
            "message": "Server is shutting down",
            "timestamp": datetime.now().isoformat()
        }
        
        tasks = []
        for connection in self.connections.values():
            tasks.append(connection.send_message(close_message))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # 关闭所有连接
        for connection in self.connections.values():
            try:
                await connection.websocket.close()
            except Exception:
                pass
        
        # 清理
        self.connections.clear()
        self.connection_groups.clear()
        self.stats["active_connections"] = 0
        
        self.logger.info("All WebSocket connections closed")
