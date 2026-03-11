import base64
import requests
import os
from PIL import Image
import io
from typing import Optional


class TagGenerator:
    """调用LM Studio API生成图片标签"""

    def __init__(self, api_url: str = "http://localhost:1234/v1", model_name: str = "qwen3.5-9b"):
        self.api_url = api_url
        self.model_name = model_name
        self.chat_endpoint = f"{api_url}/chat/completions"

    def _encode_image_to_base64(self, image_path: str) -> str:
        """将图片编码为base64字符串，先压缩图片"""
        # 打开图片并压缩
        with Image.open(image_path) as img:
            # 转换为RGB模式（如果是RGBA等）
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # 限制图片大小（最大1024像素）
            max_size = 1024
            if max(img.size) > max_size:
                ratio = max_size / max(img.size)
                new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)

            # 压缩图片到合理大小
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=85, optimize=True)
            return base64.b64encode(buffer.getvalue()).decode("utf-8")

    def _get_image_format(self, image_path: str) -> str:
        """获取图片格式"""
        ext = os.path.splitext(image_path)[1].lower()
        format_map = {
            ".jpg": "jpeg",
            ".jpeg": "jpeg",
            ".png": "png",
            ".gif": "gif",
            ".bmp": "bmp",
            ".webp": "webp"
        }
        return format_map.get(ext, "jpeg")

    def generate_tags(self, image_path: str) -> list[str]:
        """
        调用模型生成标签

        Args:
            image_path: 图片文件路径

        Returns:
            标签列表
        """
        try:
            # 编码图片
            base64_image = self._encode_image_to_base64(image_path)
            image_format = self._get_image_format(image_path)

            # 构建消息
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "请仔细分析这张图片的内容，生成5-8个关键词标签。标签应该是描述图片主要内容的名词或形容词，比如：风景、天空、山脉、红色、日落等。直接返回标签，用逗号分隔，不要其他描述文字。"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/{image_format};base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]

            # 调用API
            response = requests.post(
                self.chat_endpoint,
                json={
                    "model": self.model_name,
                    "messages": messages,
                    "stream": False
                },
                timeout=120
            )

            if response.status_code == 200:
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                return self._parse_tags(content)
            else:
                print(f"API调用失败: {response.status_code} - {response.text}")
                return []

        except requests.exceptions.ConnectionError:
            print("无法连接到LM Studio，请确保LM Studio已启动并加载了模型")
            return []
        except Exception as e:
            print(f"生成标签时出错: {e}")
            return []

    def _parse_tags(self, content: str) -> list[str]:
        """
        解析模型返回的内容，提取标签

        Args:
            content: 模型返回的内容

        Returns:
            标签列表
        """
        # 去除可能的markdown代码块
        content = content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json") or content.startswith("text"):
                content = content[4:].strip()
            if content.endswith("```"):
                content = content[:-3].strip()

        # 按逗号分割
        tags = [tag.strip() for tag in content.split(",")]

        # 过滤空标签和过长的标签
        tags = [tag for tag in tags if tag and len(tag) <= 20]

        # 去重并保持顺序
        seen = set()
        unique_tags = []
        for tag in tags:
            if tag not in seen:
                seen.add(tag)
                unique_tags.append(tag)

        # 限制标签数量
        return unique_tags[:8]

    def test_connection(self) -> bool:
        """测试API连接"""
        try:
            response = requests.get(f"{self.api_url}/models", timeout=10)
            return response.status_code == 200
        except:
            return False
