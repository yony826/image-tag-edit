import os
from metadata_storage import MetadataStorage
from image_manager import ImageManager


class SearchEngine:
    """标签搜索引擎，支持AND/OR组合搜索"""

    def __init__(self):
        self.storage = MetadataStorage()
        self.image_manager = ImageManager()

    def search(self, root_folder: str, query_tags: list[str], logic: str = "AND") -> list[dict]:
        """
        搜索图片

        Args:
            root_folder: 根文件夹路径
            query_tags: 查询的标签列表
            logic: "AND" 或 "OR"

        Returns:
            匹配的 图片信息列表
        """
        if not query_tags:
            return []

        # 标准化查询标签（转小写）
        query_tags = [tag.lower().strip() for tag in query_tags if tag.strip()]

        results = []

        # 扫描根文件夹
        results.extend(self._search_folder(root_folder, query_tags, logic))

        # 扫描所有子文件夹
        for folder in self.image_manager.get_all_folders(root_folder):
            results.extend(self._search_folder(folder, query_tags, logic))

        return results

    def _search_folder(self, folder_path: str, query_tags: list[str], logic: str) -> list[dict]:
        """在指定文件夹中搜索"""
        results = []
        folder_name = os.path.basename(folder_path)
        images = self.image_manager.get_images_in_folder(folder_path)

        for img in images:
            full_path = img["full_path"]
            # 直接从图片EXIF读取标签
            info = self.storage.get_all_info(full_path)
            img_tags = [tag.lower() for tag in info.get("tags", [])]

            if not img_tags:
                continue

            # 判断是否匹配
            if logic == "AND":
                # 所有查询标签都必须存在
                matches = all(self._tag_matches_any(img_tags, qt) for qt in query_tags)
            else:  # OR
                # 任意一个查询标签存在即可
                matches = any(self._tag_matches_any(img_tags, qt) for qt in query_tags)

            if matches:
                results.append({
                    "filename": img["filename"],
                    "folder": folder_path,
                    "folder_name": folder_name,
                    "full_path": full_path,
                    "tags": info.get("tags", []),
                    "processed_at": info.get("processed_at", ""),
                    "model": info.get("model", "")
                })

        return results

    def _tag_matches_any(self, img_tags: list[str], query_tag: str) -> bool:
        """
        检查查询标签是否匹配图片标签
        支持模糊匹配
        """
        for tag in img_tags:
            if query_tag in tag or tag in query_tag:
                return True
        return False

    def get_all_tags(self, root_folder: str) -> dict[str, int]:
        """
        获取所有标签及其出现次数

        Args:
            root_folder: 根文件夹路径

        Returns:
            标签计数字典 {标签: 数量}
        """
        tag_counts = {}

        # 扫描根文件夹
        for img in self.image_manager.get_images_in_folder(root_folder):
            info = self.storage.get_all_info(img["full_path"])
            for tag in info.get("tags", []):
                tag_lower = tag.lower()
                tag_counts[tag_lower] = tag_counts.get(tag_lower, 0) + 1

        # 扫描子文件夹
        for folder in self.image_manager.get_all_folders(root_folder):
            for img in self.image_manager.get_images_in_folder(folder):
                info = self.storage.get_all_info(img["full_path"])
                for tag in info.get("tags", []):
                    tag_lower = tag.lower()
                    tag_counts[tag_lower] = tag_counts.get(tag_lower, 0) + 1

        return dict(sorted(tag_counts.items(), key=lambda x: x[1], reverse=True))

    def suggest_tags(self, root_folder: str, prefix: str = "", limit: int = 20) -> list[str]:
        """
        根据前缀建议标签

        Args:
            root_folder: 根文件夹路径
            prefix: 标签前缀
            limit: 返回数量限制

        Returns:
            建议的标签列表
        """
        all_tags = self.get_all_tags(root_folder)
        prefix = prefix.lower().strip()

        if prefix:
            suggestions = [tag for tag in all_tags.keys() if tag.startswith(prefix)]
        else:
            suggestions = list(all_tags.keys())

        return suggestions[:limit]
