import os
import random
import logging
from io import BytesIO
from pathlib import Path
from typing import List, Tuple, Optional, Any
from PIL import Image, ImageFont, ImageDraw
import asyncio

logger = logging.getLogger("emby-ranks.drawer")


def draw_text_psd_style(draw: ImageDraw.ImageDraw, xy: Tuple[int, int], text: str, 
                        font: ImageFont.FreeTypeFont, tracking: float = 0, 
                        leading: Optional[float] = None, align: str = "left", **kwargs):
    """绘制具有 PSD 样式字距与行距的文本"""
    def stutter_chunk(lst, size, overlap=0, default=None):
        for i in range(0, len(lst), size - overlap):
            r = list(lst[i:i + size])
            while len(r) < size:
                r.append(default)
            yield r

    x, y = xy
    font_size = font.size
    lines = text.splitlines()
    if leading is None:
        leading = font.size * 1.2
        
    for line in lines:
        total_width = font.getlength(line) + (tracking / 1000) * font_size * (len(line) - 1)
        current_x = x
        if align == "right":
            current_x = x - total_width
            
        for a, b in stutter_chunk(line, 2, 1, " "):
            w = font.getlength(a + b) - font.getlength(b)
            draw.text((current_x, y), a, font=font, **kwargs)
            current_x += w + (tracking / 1000) * font_size
        y += leading


class RanksDrawer:
    def __init__(self, assets_dir: str = "./assets", server_name: str = "EMBY SERVER", 
                 weekly: bool = False, backdrop: bool = False):
        self.assets_dir = Path(assets_dir)
        self.server_name = server_name
        self.weekly = weekly
        self.backdrop = backdrop

        # 背景与遮罩路径
        bg_dir = self.assets_dir / "bg"
        if not bg_dir.exists():
            bg_dir = self.assets_dir
        
        bg_files = [f for f in bg_dir.glob("*.jpg")] + [f for f in bg_dir.glob("*.png")]
        if bg_files:
            chosen_bg = random.choice(bg_files)
            self.bg = Image.open(chosen_bg).convert("RGBA")
        else:
            self.bg = Image.new("RGBA", (1920, 1080), (30, 30, 35, 255))

        # 遮罩文件
        mask_prefix = "week_ranks_mask" if self.weekly else "day_ranks_mask"
        mask_name = f"{mask_prefix}_backdrop.png" if self.backdrop else f"{mask_prefix}.png"
        mask_path = self.assets_dir / mask_name

        if mask_path.exists():
            mask = Image.open(mask_path).convert("RGBA")
            self.bg = self.bg.resize(mask.size)
            self.bg.paste(mask, (0, 0), mask)
        else:
            logger.warning(f"遮罩图片未找到: {mask_path}，使用纯背景")

        # 字体初始化
        font_path = self.assets_dir / "font" / "PingFang Bold.ttf"
        if not font_path.exists():
            font_path = self.assets_dir / "PingFang Bold.ttf"

        if font_path.exists():
            self.font = ImageFont.truetype(str(font_path), 18)
            self.font_small = ImageFont.truetype(str(font_path), 14)
            self.font_count = ImageFont.truetype(str(font_path), 12)
            self.font_logo = ImageFont.truetype(str(font_path), 60)
        else:
            self.font = ImageFont.load_default()
            self.font_small = ImageFont.load_default()
            self.font_count = ImageFont.load_default()
            self.font_logo = ImageFont.load_default()

    async def draw(self, emby_client, movies: List[List[Any]], tvshows: List[List[Any]], draw_text: bool = False):
        """渲染电影与剧集封面及名称"""
        text_draw = ImageDraw.Draw(self.bg)
        
        # 1. 绘制电影海报 (前5项)
        for index, item in enumerate(movies[:5]):
            user_id, item_id, item_type, name, count, duration = tuple(item)
            img_data = None
            if self.backdrop:
                img_data = await emby_client.get_item_image(item_id, "Backdrop")
                if not img_data:
                    img_data = await emby_client.get_item_image(item_id, "Primary")
                resize_size = (242, 160) if img_data else (110, 160)
                xy = (103 + 302 * index, 140)
            else:
                img_data = await emby_client.get_item_image(item_id, "Primary")
                resize_size = (144, 210)
                xy = (601, 162 + 230 * index)

            display_name = name[:7] if name else ""
            if img_data:
                try:
                    cover = Image.open(BytesIO(img_data)).convert("RGBA")
                    cover = cover.resize(resize_size)
                    self.bg.paste(cover, xy)
                except Exception as e:
                    logger.error(f"粘贴电影封面异常 [{item_id}] {name}: {e}")
                    img_data = None

            if not img_data:
                # 缺失封面时文字占位
                if self.backdrop:
                    draw_text_psd_style(text_draw, (123 + 302 * index, 140), display_name, self.font, 126)
                else:
                    draw_text_psd_style(text_draw, (601, 162 + 230 * index), display_name, self.font, 126)

            if draw_text:
                draw_text_psd_style(text_draw, (601 + 130, 163 + (230 * index)), str(count), self.font_count, 126)
                draw_text_psd_style(text_draw, (601, 163 + 190 + (230 * index)), display_name, self.font, 126)

        # 2. 绘制剧集海报 (前5项)
        for index, item in enumerate(tvshows[:5]):
            user_id, item_id, item_type, name, count, duration = tuple(item)
            img_data = None
            if self.backdrop:
                img_data = await emby_client.get_item_image(item_id, "Backdrop")
                if not img_data:
                    img_data = await emby_client.get_item_image(item_id, "Primary")
                resize_size = (242, 160) if img_data else (110, 160)
                xy = (408 + 302 * index, 444)
            else:
                img_data = await emby_client.get_item_image(item_id, "Primary")
                resize_size = (144, 210)
                xy = (770, 985 - 232 * index)

            display_name = name[:7] if name else ""
            if img_data:
                try:
                    cover = Image.open(BytesIO(img_data)).convert("RGBA")
                    cover = cover.resize(resize_size)
                    self.bg.paste(cover, xy)
                except Exception as e:
                    logger.error(f"粘贴剧集封面异常 [{item_id}] {name}: {e}")
                    img_data = None

            if not img_data:
                if self.backdrop:
                    draw_text_psd_style(text_draw, (428 + 302 * index, 444), display_name, self.font, 126)
                else:
                    draw_text_psd_style(text_draw, (770, 990 - 232 * index), display_name, self.font, 126)

            if draw_text:
                draw_text_psd_style(text_draw, (770 + 130, 990 - (232 * index)), str(count), self.font_count, 126)
                draw_text_psd_style(text_draw, (770, 990 + 193 - (232 * index)), display_name, self.font, 126)

        # 3. 绘制 Server / Logo 名字
        if self.server_name:
            if self.backdrop:
                draw_text_psd_style(text_draw, (1900, 830), self.server_name, self.font_logo, 126, align="right")
            else:
                draw_text_psd_style(text_draw, (90, 1100), self.server_name, self.font_logo, 126, align="left")

    def save_bytes(self) -> bytes:
        """导出渲染好的图片为 JPEG bytes"""
        img = self.bg
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=90)
        return buf.getvalue()

    def save_file(self, save_path: str) -> str:
        """保存图片到本地文件路径"""
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        img = self.bg
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(save_path, format="JPEG", quality=90)
        return save_path
