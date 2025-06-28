import base64
from io import BytesIO

import qrcode
from PIL import Image
from LittlePaimon.utils import logger
from LittlePaimon.utils.path import RESOURCE_BASE_PATH



def generate_qrcode(
        url,
        icon_path = RESOURCE_BASE_PATH / 'genshin.jpg',
        qr_color="black",
        bg_color="white",
        icon_scale=0.25,
        border=4
):
    """
    生成带中心图标的二维码

    参数:
        url: 二维码包含的数据
        icon_path: 图标文件路径
        qr_color: 二维码颜色(默认: black)
        bg_color: 背景颜色(默认: white)
        icon_scale: 图标相对于二维码大小的比例(默认: 0.25)
        border: 二维码边框大小(默认: 4)
    """
    # 生成基础二维码
    qr = qrcode.QRCode(
        version=None,  # 自动选择版本
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # 高容错率
        box_size=10,
        border=border,
    )
    qr.add_data(url)
    qr.make(fit=True)

    # 创建二维码图像
    qr_img = qr.make_image(fill_color=qr_color, back_color=bg_color).convert('RGBA')

    # 打开并处理图标
    icon = Image.open(icon_path)
    icon = icon.convert('RGBA')

    # 计算图标大小(基于二维码大小的比例)
    qr_width, qr_height = qr_img.size
    icon_size = int(qr_width * icon_scale)  # 根据比例调整 icon 大小
    icon = icon.resize((icon_size, icon_size), Image.LANCZOS)  # 高质量缩放 icon

    # 调整图标大小并保持宽高比
    icon.thumbnail((icon_size, icon_size), Image.LANCZOS)

    # 计算图标位置(居中)
    icon_pos = (
        (qr_width - icon.size[0]) // 2,
        (qr_height - icon.size[1]) // 2
    )
    # 透明背景处理（可选）
    if icon.mode in ("RGBA", "LA"):
        alpha = icon.getchannel("A")
        qr_img.paste(icon, icon_pos, mask=alpha)
    else:
        qr_img.paste(icon, icon_pos)
    # 将图标粘贴到二维码中心
    qr_img.paste(icon, icon_pos, icon)

    # 保存结果
    bio = BytesIO()
    qr_img.save(bio, format="PNG")
    logger.success("原神绑定","绑定二维码已生成")
    return f'base64://{base64.b64encode(bio.getvalue()).decode()}'