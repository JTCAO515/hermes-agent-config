#!/usr/bin/env python3
"""
检查 AI 生成的 App 图标质量，使用 Doubao VLM 描述并给出评分。

用法:
    python3 scripts/check-icon-quality.py <image-path>

输出:
    VLM 对图标的内容描述 + 是否适合作为 App 图标 + 改进建议
"""

import sys, os, json, base64, requests

def check_icon(image_path):
    if not os.path.exists(image_path):
        print(f"文件不存在: {image_path}")
        sys.exit(1)

    api_key = os.environ.get("VOLCENGINE_API_KEY", "")
    if not api_key:
        print("缺少 VOLCENGINE_API_KEY 环境变量")
        sys.exit(1)

    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()

    # 如果图片太大，先提示
    size_mb = len(b64) / 1_000_000
    if size_mb > 1:
        print(f"警告: base64 编码 {size_mb:.1f}MB，VLM 可能超时。建议先缩小图片。")
        # 尝试用 Pillow 缩小
        try:
            from PIL import Image
            import io
            img = Image.open(image_path)
            img.thumbnail((512, 512), Image.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode()
            print(f"已自动缩小到 512x512，新大小 {len(b64)/1_000_000:.1f}MB")
        except ImportError:
            print("Pillow 不可用，继续使用原图（可能超时）")

    resp = requests.post(
        "https://ark.cn-beijing.volces.com/api/v3/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": "doubao-seed-2-0-lite-260215",
            "messages": [{
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "你是App图标质量评审专家。分析这张图片："
                                "1. 主体是否突出、居中？"
                                "2. 颜色对比是否足够（在深色背景上能看清吗）？"
                                "3. 是否适合作为App启动图标（建议: 适合/不适合/需要修改）？"
                                "4. 给出0-10分评分。"
                                "简洁回答，中文。"
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{b64}"}
                    }
                ]
            }],
            "max_tokens": 300
        }
    )

    result = resp.json()
    content = result["choices"][0]["message"]["content"]
    print("=" * 50)
    print("图标质量评估")
    print("=" * 50)
    print(content)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 check-icon-quality.py <image-path>")
        sys.exit(1)
    check_icon(sys.argv[1])
