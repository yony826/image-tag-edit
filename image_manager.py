import os
from pathlib import Path
from typing import Optional
from PIL import Image


class ImageManager:
    """图片管理器，处理图片导入、浏览、删除等操作"""

    SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"}

    def __init__(self):
        pass

    def is_image_file(self, file_path: str) -> bool:
        """检查文件是否为图片"""
        ext = os.path.splitext(file_path)[1].lower()
        return ext in self.SUPPORTED_FORMATS

    def get_images_in_folder(self, folder_path: str) -> list[dict]:
        """
        获取文件夹中的所有图片

        Args:
            folder_path: 文件夹路径

        Returns:
            图片信息列表
        """
        images = []
        if not os.path.exists(folder_path):
            return images

        for filename in os.listdir(folder_path):
            full_path = os.path.join(folder_path, filename)
            if os.path.isfile(full_path) and self.is_image_file(full_path):
                try:
                    with Image.open(full_path) as img:
                        width, height = img.size
                        images.append({
                            "filename": filename,
                            "full_path": full_path,
                            "width": width,
                            "height": height,
                            "size": os.path.getsize(full_path)
                        })
                except Exception as e:
                    print(f"无法读取图片 {filename}: {e}")

        return images

    def get_images_recursive(self, root_folder: str) -> list[dict]:
        """
        递归获取所有子文件夹中的图片

        Args:
            root_folder: 根文件夹路径

        Returns:
            所有图片信息列表
        """
        images = []
        root_path = Path(root_folder)

        for folder in root_path.rglob("*"):
            if folder.is_dir():
                folder_images = self.get_images_in_folder(str(folder))
                for img in folder_images:
                    img["relative_folder"] = str(folder.relative_to(root_path))
                images.extend(folder_images)

        return images

    def get_all_folders(self, root_folder: str) -> list[str]:
        """
        获取所有包含图片的文件夹

        Args:
            root_folder: 根文件夹路径

        Returns:
            文件夹路径列表
        """
        folders = []
        root_path = Path(root_folder)

        for folder in root_path.rglob("*"):
            if folder.is_dir():
                images = self.get_images_in_folder(str(folder))
                if images:
                    folders.append(str(folder))

        return folders

    def delete_image(self, image_path: str) -> bool:
        """
        删除图片文件

        Args:
            image_path: 图片路径

        Returns:
            是否成功删除
        """
        try:
            if os.path.exists(image_path):
                os.remove(image_path)
                return True
            return False
        except Exception as e:
            print(f"删除图片失败: {e}")
            return False

    def get_thumbnail(self, image_path: str, size: tuple = (200, 200)) -> Optional[Image.Image]:
        """
        生成缩略图

        Args:
            image_path: 图片路径
            size: 缩略图大小

        Returns:
            PIL Image对象
        """
        try:
            with Image.open(image_path) as img:
                # 保持宽高比
                img.thumbnail(size, Image.Resampling.LANCZOS)
                return img.copy()
        except Exception as e:
            print(f"生成缩略图失败: {e}")
            return None

    def validate_image(self, image_path: str) -> bool:
        """
        验证图片是否有效

        Args:
            image_path: 图片路径

        Returns:
            是否为有效图片
        """
        try:
            with Image.open(image_path) as img:
                img.verify()
            return True
        except:
            return False
