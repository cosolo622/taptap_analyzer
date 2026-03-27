# -*- coding: utf-8 -*-
"""
小红书图片OCR识别脚本
功能：
1. 读取已爬取的笔记数据
2. 下载笔记中的图片
3. OCR识别图片中的文字
4. 将识别结果合并到数据中
"""

import json
import os
import re
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import sys

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))


def setup_ocr():
    """
    初始化OCR引擎（尝试多种方案）
    
    Returns:
        callable: OCR函数，接收图片路径返回文字
    """
    # 方案1：使用EasyOCR（支持中文，效果好）
    try:
        import easyocr
        print("[OCR] 使用 EasyOCR 引擎（支持中文）")
        reader = easyocr.Reader(['ch_sim', 'en'], gpu=False, verbose=False)
        
        def ocr_with_easyocr(image_path):
            try:
                results = reader.readtext(image_path)
                texts = []
                for bbox, text, confidence in results:
                    if confidence > 0.3 and text.strip():
                        texts.append(text.strip())
                return " ".join(texts)
            except Exception as e:
                return f"[OCR错误: {e}]"
        
        return ocr_with_easyocr
    except ImportError:
        pass
    
    # 方案2：使用Pytesseract + Tesseract
    try:
        import pytesseract
        from PIL import Image
        print("[OCR] 使用 Pytesseract 引擎")
        
        # Windows上可能需要指定tesseract路径
        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        
        def ocr_with_tesseract(image_path):
            try:
                img = Image.open(image_path)
                text = pytesseract.image_to_string(img, lang='chi_sim+eng')
                return text.strip()
            except Exception as e:
                return f"[OCR错误: {e}]"
        
        return ocr_with_tesseract
    except ImportError:
        pass
    
    print("[OCR] 未找到可用的OCR引擎，建议安装: pip install easyocr")
    return None


def download_image(url, save_path, timeout=10):
    """
    下载单张图片
    
    Args:
        url: 图片URL
        save_path: 保存路径
        timeout: 超时时间
    
    Returns:
        bool: 是否下载成功
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        if response.status_code == 200:
            # 保存到临时文件，避免中文路径问题
            temp_path = str(save_path)
            with open(temp_path, 'wb') as f:
                f.write(response.content)
            return True
    except Exception as e:
        print(f"  下载失败: {url[:50]}... - {e}")
    return False


def process_single_note(note, ocr_func, output_dir, max_images=3):
    """
    处理单条笔记，下载图片并OCR识别
    
    Args:
        note: 笔记数据字典
        ocr_func: OCR函数
        output_dir: 输出目录
        max_images: 最大处理图片数
    
    Returns:
        dict: 处理后的笔记数据
    """
    note_id = note.get('note_id', 'unknown')
    image_list = note.get('image_list', '')
    
    # 解析图片URL列表
    if not image_list:
        return note
    
    image_urls = [url.strip() for url in image_list.split(',') if url.strip()]
    if not image_urls:
        return note
    
    # 只处理前几张图片
    image_urls = image_urls[:max_images]
    
    # 使用英文路径避免中文问题
    temp_dir = Path("d:/temp_xhs_ocr")
    temp_dir.mkdir(exist_ok=True)
    
    # 下载并OCR识别
    image_texts = []
    for i, url in enumerate(image_urls):
        # 生成临时文件名（英文）
        temp_image_path = temp_dir / f"temp_{note_id}_{i}.jpg"
        
        # 下载图片
        print(f"  下载图片 {i+1}/{len(image_urls)}: {url[:50]}...")
        if download_image(url, temp_image_path):
            # OCR识别
            if ocr_func:
                print(f"  OCR识别中...")
                text = ocr_func(str(temp_image_path))
                if text and not text.startswith('[OCR错误'):
                    image_texts.append(text)
        else:
            print(f"  下载失败，跳过")
    
    # 将图片文字合并到笔记
    if image_texts:
        note['image_text'] = " | ".join(image_texts)
        note['image_text_count'] = len(image_texts)
    else:
        note['image_text'] = ""
        note['image_text_count'] = 0
    
    return note


def process_existing_data(input_file, output_file, max_workers=3, max_images=3):
    """
    处理已爬取的数据，添加图片OCR文字
    
    Args:
        input_file: 输入文件路径
        output_file: 输出文件路径
        max_workers: 并行处理数
        max_images: 每条笔记最大处理图片数
    """
    print(f"\n{'='*60}")
    print(f"开始处理数据文件: {input_file}")
    print(f"{'='*60}\n")
    
    # 检查输入文件
    if not os.path.exists(input_file):
        print(f"[错误] 输入文件不存在: {input_file}")
        return
    
    # 读取数据
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    notes = []
    for line in lines:
        line = line.strip()
        if line:
            try:
                notes.append(json.loads(line))
            except json.JSONDecodeError:
                print(f"[警告] 跳过无效JSON行")
    
    print(f"共读取 {len(notes)} 条笔记")
    
    # 初始化OCR
    ocr_func = setup_ocr()
    if not ocr_func:
        print("[错误] 无法初始化OCR引擎")
        return
    
    # 创建输出目录
    output_dir = Path(output_file).parent / "images"
    output_dir.mkdir(exist_ok=True)
    
    # 过滤出有图片的笔记
    notes_with_images = [n for n in notes if n.get('image_list')]
    print(f"其中 {len(notes_with_images)} 条笔记包含图片")
    
    # 处理每条笔记
    processed_notes = []
    for i, note in enumerate(notes):
        print(f"\n处理笔记 {i+1}/{len(notes)}: {note.get('title', '')[:30]}...")
        processed = process_single_note(note, ocr_func, output_dir, max_images)
        processed_notes.append(processed)
        
        # 避免请求过快
        time.sleep(0.5)
    
    # 保存结果
    print(f"\n{'='*60}")
    print(f"保存处理结果到: {output_file}")
    print(f"{'='*60}\n")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for note in processed_notes:
            f.write(json.dumps(note, ensure_ascii=False) + '\n')
    
    # 统计结果
    notes_with_ocr = [n for n in processed_notes if n.get('image_text')]
    print(f"\n处理完成！")
    print(f"  总笔记数: {len(processed_notes)}")
    print(f"  成功OCR: {len(notes_with_ocr)}")
    print(f"  图片目录: {output_dir}")
    
    return processed_notes


def show_sample_results(output_file, n=5):
    """
    显示处理结果样例
    
    Args:
        output_file: 结果文件路径
        n: 显示条数
    """
    print(f"\n{'='*60}")
    print(f"结果样例（前{n}条有图片文字的笔记）")
    print(f"{'='*60}\n")
    
    if not os.path.exists(output_file):
        print(f"[错误] 文件不存在: {output_file}")
        return
    
    count = 0
    with open(output_file, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                note = json.loads(line.strip())
                if note.get('image_text'):
                    count += 1
                    if count <= n:
                        print(f"【{count}】{note.get('title', '无标题')}")
                        print(f"    正文: {note.get('desc', '')[:100]}...")
                        print(f"    图片文字: {note['image_text'][:150]}...")
                        print()
            except:
                pass
    
    print(f"共找到 {count} 条包含图片文字的笔记")


def main():
    """
    主函数
    """
    print("\n" + "="*60)
    print("小红书图片OCR识别工具")
    print("="*60 + "\n")
    
    # 路径配置
    data_dir = Path(__file__).parent.parent / "data" / "xhs" / "jsonl"
    input_file = data_dir / "search_contents_2026-03-23.jsonl"
    output_file = data_dir / "search_contents_with_ocr_2026-03-23.jsonl"
    
    # 如果今天的文件不存在，查找最新的文件
    if not input_file.exists():
        existing_files = list(data_dir.glob("search_contents_*.jsonl"))
        if existing_files:
            input_file = existing_files[-1]
            output_file = data_dir / f"search_contents_with_ocr_{input_file.stem.split('_')[-1]}.jsonl"
            print(f"[信息] 使用最新文件: {input_file.name}")
        else:
            print(f"[错误] 未找到数据文件: {input_file}")
            return
    
    print(f"输入文件: {input_file}")
    print(f"输出文件: {output_file}")
    
    # 处理数据
    process_existing_data(str(input_file), str(output_file), max_workers=2, max_images=2)
    
    # 显示结果样例
    show_sample_results(str(output_file))


if __name__ == "__main__":
    main()
