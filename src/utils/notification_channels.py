"""
多渠道通知实现
支持: Server酱, 飞书, 邮件
"""
import os
import requests
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class ServerChanNotifier:
    """Server酱通知"""
    
    def __init__(self, sendkey: Optional[str] = None):
        self.sendkey = sendkey or os.getenv("SERVERCHAN_SENDKEY", "")
    
    def is_available(self) -> bool:
        return bool(self.sendkey)
    
    def send(self, title: str, content: str) -> bool:
        """发送Server酱通知"""
        if not self.is_available():
            logger.warning("Server酱未配置SendKey")
            return False
        
        try:
            url = f"https://sctapi.ftqq.com/{self.sendkey}.send"
            data = {
                "title": title,
                "desp": content
            }
            response = requests.post(url, data=data, timeout=10)
            success = response.status_code == 200
            if success:
                logger.info(f"Server酱发送成功: {title}")
            else:
                logger.error(f"Server酱发送失败: HTTP {response.status_code}")
            return success
        except Exception as e:
            logger.error(f"Server酱发送异常: {e}")
            return False


class FeishuNotifier:
    """飞书通知"""
    
    def __init__(self, webhook: Optional[str] = None, secret: Optional[str] = None):
        self.webhook = webhook or os.getenv("FEISHU_WEBHOOK", "")
        self.secret = secret or os.getenv("FEISHU_SECRET", "")
    
    def is_available(self) -> bool:
        return bool(self.webhook)
    
    def send(self, title: str, content: str) -> bool:
        """发送飞书通知"""
        if not self.is_available():
            logger.warning("飞书未配置Webhook")
            return False
        
        try:
            # 飞书富文本消息格式
            payload = {
                "msg_type": "text",
                "content": {
                    "text": f"{title}\n\n{content}"
                }
            }
            
            headers = {"Content-Type": "application/json"}
            response = requests.post(
                self.webhook, 
                json=payload, 
                headers=headers,
                timeout=10
            )
            
            success = response.status_code == 200
            if success:
                result = response.json()
                if result.get("code") == 0:
                    logger.info(f"飞书发送成功: {title}")
                    return True
                else:
                    logger.error(f"飞书发送失败: {result.get('msg', 'Unknown error')}")
                    return False
            else:
                logger.error(f"飞书发送失败: HTTP {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"飞书发送异常: {e}")
            return False


class MultiChannelNotifier:
    """多渠道通知管理器"""
    
    def __init__(self):
        self.serverchan = ServerChanNotifier()
        self.feishu = FeishuNotifier()
    
    def send_all(self, title: str, content: str) -> Dict[str, bool]:
        """发送到所有可用渠道"""
        results = {}
        
        if self.serverchan.is_available():
            results["serverchan"] = self.serverchan.send(title, content)
        else:
            results["serverchan"] = None  # 未配置
        
        if self.feishu.is_available():
            results["feishu"] = self.feishu.send(title, content)
        else:
            results["feishu"] = None  # 未配置
        
        return results
    
    def get_status(self) -> Dict[str, str]:
        """获取各渠道配置状态"""
        return {
            "serverchan": "✅ 已配置" if self.serverchan.is_available() else "❌ 未配置",
            "feishu": "✅ 已配置" if self.feishu.is_available() else "❌ 未配置"
        }
