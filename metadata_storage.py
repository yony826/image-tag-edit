import os
import json
import piexif
from PIL import Image
from typing import Optional


class MetadataStorage:
    """图片EXIF元数据存储，使用piexif库保存标签"""

    def __init__(self):
        pass

    def save_tags(self, image_path: str, tags: list[str], model: str = "qwen3.5-9b"):
        """保存标签到图片的EXIF中"""
        try:
            # 准备标签数据
            from datetime import datetime
            tag_data = {
                "tags": tags,
                "processed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "model": model
            }
            tag_json = json.dumps(tag_data, ensure_ascii=False)

            # 读取原图
            img = Image.open(image_path)

            # 转换模式
            if img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGB')

            # 使用piexif保存EXIF
            exif_dict = {'0th': {}, 'Exif': {}, 'GPS': {}, '1st': {}, 'thumbnail': None}
            # UserComment 需要 bytes
            exif_dict['Exif'][piexif.ExifIFD.UserComment] = tag_json.encode('utf-8')

            exif_bytes = piexif.dump(exif_dict)
            img.save(image_path, exif=exif_bytes, quality=95)
            img.close()

        except Exception as e:
            print(f"保存EXIF失败: {e}")
            raise e

    def get_tags(self, image_path: str) -> Optional[list[str]]:
        """获取图片的标签"""
        info = self.get_all_info(image_path)
        return info.get("tags", []) if info else None

    def get_all_info(self, image_path: str) -> dict:
        """获取图片的所有元信息"""
        if not os.path.exists(image_path):
            return {}

        try:
            img = Image.open(image_path)
            exif_dict = piexif.load(img.info.get('exif', b''))
            img.close()

            # 从UserComment读取
            comment = exif_dict['Exif'].get(piexif.ExifIFD.UserComment)
            if comment:
                if isinstance(comment, bytes):
                    comment = comment.decode('utf-8')
                if comment:
                    try:
                        return json.loads(comment)
                    except:
                        pass

            return {}

        except Exception as e:
            print(f"读取元信息失败: {e}")
            return {}

    def delete_tags(self, image_path: str):
        """删除图片的标签"""
        try:
            img = Image.open(image_path)
            if img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGB')

            try:
                exif_dict = piexif.load(img.info.get('exif', b''))
            except:
                exif_dict = {'0th': {}, 'Exif': {}, 'GPS': {}, '1st': {}, 'thumbnail': None}

            # 删除UserComment
            if piexif.ExifIFD.UserComment in exif_dict['Exif']:
                del exif_dict['Exif'][piexif.ExifIFD.UserComment]

            exif_bytes = piexif.dump(exif_dict)
            img.save(image_path, exif=exif_bytes, quality=95)
            img.close()
        except Exception as e:
            print(f"删除标签失败: {e}")

    def scan_folder(self, folder_path: str) -> list[dict]:
        """扫描文件夹中所有带标签的图片"""
        results = []
        if not os.path.exists(folder_path):
            return results

        from image_manager import ImageManager
        mgr = ImageManager()

        for filename in os.listdir(folder_path):
            full_path = os.path.join(folder_path, filename)
            if os.path.isfile(full_path) and mgr.is_image_file(full_path):
                info = self.get_all_info(full_path)
                if info and info.get("tags"):
                    results.append({
                        "filename": filename,
                        "full_path": full_path,
                        "tags": info.get("tags", []),
                        "processed_at": info.get("processed_at", ""),
                        "model": info.get("model", "")
                    })

        return results

    def scan_folders_recursive(self, root_folder: str) -> list[dict]:
        """递归扫描所有子文件夹"""
        results = []

        for folder_name in os.listdir(root_folder):
            folder_path = os.path.join(root_folder, folder_name)
            if os.path.isdir(folder_path):
                results.extend(self.scan_folder(folder_path))

        # 也检查根文件夹
        results.extend(self.scan_folder(root_folder))

        return results
