import re

def fnt_to_fontdef(fnt_path, output_path, font_name, image_file, flip_y=False):
    """
    将 .fnt 文件转换为 OGRE 的 .fontdef 文件（全部字符使用u+十进制编码）
    
    参数：
        fnt_path: 输入的 .fnt 文件路径
        output_path: 输出的 .fontdef 文件路径
        font_name: 字体在 .fontdef 中的名称
        image_file: 关联的纹理图片文件名
        flip_y: 是否翻转Y轴坐标（默认True，适配左上角原点）
    """
    # 初始化存储结构
    common_info = {"scaleW": 256, "scaleH": 256}
    chars = []
    
    # 优化后的正则表达式（支持参数任意顺序）
    common_pattern = re.compile(
        r"common.*?\bscaleW=(\d+).*?\bscaleH=(\d+)",
        re.DOTALL
    )
    char_pattern = re.compile(
        r"char.*?\bid=(-?\d+).*?\bx=(\d+).*?\by=(\d+).*?\bwidth=(\d+).*?\bheight=(\d+)"
        r".*?\bxoffset=(-?\d+).*?\byoffset=(-?\d+).*?\bxadvance=(\d+)",
        re.DOTALL
    )

    # 解析 .fnt 文件
    with open(fnt_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            
            # 提取公共信息
            if line.startswith("common"):
                if match := common_pattern.search(line):
                    common_info["scaleW"] = int(match.group(1))
                    common_info["scaleH"] = int(match.group(2))
            
            # 提取字符信息
            elif line.startswith("char"):
                if match := char_pattern.search(line):
                    # 提取基本属性
                    char_id = int(match.group(1))
                    x = int(match.group(2))
                    y = int(match.group(3))
                    width = int(match.group(4))
                    height = int(match.group(5))
                    
                    # 跳过无效字符（宽度或高度为0）
                    if width <= 0 or height <= 0:
                        continue
                    
                    # 坐标系转换
                    if flip_y:
                        # 翻转Y轴（从左上角原点转换）
                        y = common_info["scaleH"] - y - height
                    
                    # 计算归一化UV坐标
                    u1 = x / common_info["scaleW"]
                    v1 = y / common_info["scaleH"]
                    u2 = (x + width) / common_info["scaleW"]
                    v2 = (y + height) / common_info["scaleH"]
                    xa = round((common_info["scaleW"] / common_info["scaleH"]) * (u2 - u1) / (v2 - v1), 6)
                    
                    # 存储字符数据
                    chars.append({
                        "id": char_id,
                        "u1": round(u1, 6),  # 保留6位小数
                        "v1": round(v1, 6),
                        "u2": round(u2, 6),
                        "v2": round(v2, 6),
                        "aspectRatio": xa,
                        "width": width,
                        "height": height
                    })

    # 生成 .fontdef 内容
    fontdef = [
        f'font {font_name}',
        '{',
        f'    type image',
        f'    source {image_file}',
        f'    size {common_info["scaleH"]}  // 基准字号',
        ''
    ]

    # 添加字符定义
    for char in sorted(chars, key=lambda x: x["id"]):
        char_id = char["id"]
        # 特殊字符处理（如空格需要显式命名）
        if char_id == 32:
            identifier = "space"
        else:
            identifier = f'u{char_id}'
        
        fontdef.append(
            f'    glyph {identifier} '
            f'{char["u1"]:.6f} {char["v1"]:.6f} '
            f'{char["u2"]:.6f} {char["v2"]:.6f}'
            f' {char["aspectRatio"]:.6f}'
        )

    fontdef.append('}')

    # 写入文件
    with open(output_path, 'w', encoding="utf-8") as f:
        f.write('\n'.join(fontdef))

if __name__ == "__main__":
    # 使用示例
    fnt_to_fontdef(
        fnt_path="123.fnt",
        output_path="output.fontdef",
        font_name="MyBitmapFont",
        image_file="123.png",
        flip_y=False  # 根据实际纹理坐标方向调整
    )