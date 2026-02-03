"""账单解析器模块"""

from .base import BaseParser
from .alipay import AlipayParser
from .wechat import WechatParser
from .ccb import CCBParser

__all__ = ["BaseParser", "AlipayParser", "WechatParser", "CCBParser"]
