import json
import os
from typing import Dict, Any, List, Tuple
from PIL import Image
from apis.openai_api import OpenAIAPI

def identify_target_area(image_path: str = "data/demo.jpg", target_text: str = "真相1解读") -> Dict[str, Any]:
    """
    识别图片中的特定目标区域
    
    Args:
        image_path: 图片文件路径
        target_text: 要寻找的目标文本或区域描述
        
    Returns:
        dict: 包含目标区域识别结果的字典
    """
    openai_api = OpenAIAPI()
    
    # 专门针对目标区域的提示词
    target_prompt = f"""
请仔细观察这张图片，专门寻找包含"{target_text}"的完整区域，该区域内容应该完整。

你的任务是：

1. **精确识别**：在图片中找到包含"{target_text}"文字或相关内容的区域，该区域内容应该完整，不包含非本区域内容。
2. **区域分析**：分析该区域的视觉特征、内容结构和边界范围
3. **适用性评估**：评估该区域是否适合用于短视频制作

请按以下JSON格式返回结果：

```json
{{
  "target_found": true/false,
  "search_target": "{target_text}",
  "position_info": {{
    "x": "x坐标百分比",
    "y": "y坐标百分比",
    "width": "宽度百分比",
    "height": "高度百分比"
  }},
  "confidence": "high/medium/low",
  "notes": "其他重要备注信息"
}}
```

重要说明：
- 坐标以图片左上角为原点(0,0)
- 百分比精确到小数点后1位
- 如果找不到目标区域，请标注target_found为false
- 重点关注文字"{target_text}"的精确位置
- 确保包含完整的相关内容区域
"""

    try:
        print(f"🔍 正在寻找目标区域: {target_text}")
        print(f"📁 图片路径: {image_path}")
        
        # 调用OpenAI API进行目标区域识别
        response = openai_api.send_message_with_image(target_prompt, image_path, stream=False)
        
        print("✅ 目标区域识别完成!")
        print("\n" + "="*50)
        print(f"📍 '{target_text}' 区域识别结果:")
        print("="*50)
        
        # 打印原始响应
        content = response.get('content', '')
        print(content)
        
        # 尝试解析JSON结果
        try:
            # 提取JSON部分
            if '```json' in content:
                json_start = content.find('```json') + 7
                json_end = content.find('```', json_start)
                json_content = content[json_start:json_end].strip()
            else:
                json_content = content
            
            # 解析JSON
            target_result = json.loads(json_content)
            
            print("\n" + "="*50)
            print(f"📋 '{target_text}' 解析结果:")
            print("="*50)
            
            # 格式化输出结果
            found = target_result.get('target_found', False)
            confidence = target_result.get('confidence', 'unknown')
            
            print(f"🎯 目标发现: {'✅ 已找到' if found else '❌ 未找到'}")
            print(f"🔍 识别信心: {confidence}")
            
            if found:
                # 区域分析
                if 'area_analysis' in target_result:
                    analysis = target_result['area_analysis']
                    print(f"\n📄 区域描述: {analysis.get('visual_description', 'N/A')}")
                    print(f"📝 文字内容: {analysis.get('text_content', 'N/A')}")
                    print(f"🎨 设计风格: {analysis.get('design_style', 'N/A')}")
                
                # 位置信息
                if 'position_info' in target_result:
                    pos = target_result['position_info']
                    print(f"\n📐 位置信息:")
                    print(f"   x={pos.get('x')}%, y={pos.get('y')}%")
                    print(f"   w={pos.get('width')}%, h={pos.get('height')}%")
                
                # 视频适用性
                if 'video_suitability' in target_result:
                    suitability = target_result['video_suitability']
                    suitable = suitability.get('suitable_for_video', False)
                    potential = suitability.get('video_potential', 'unknown')
                    duration = suitability.get('recommended_duration', 'N/A')
                    
                    print(f"\n🎬 视频适用性: {'✅ 适合' if suitable else '❌ 不适合'}")
                    print(f"📊 视频潜力: {potential}")
                    print(f"⏱️  建议时长: {duration}秒")
                    print(f"💭 原因: {suitability.get('reason', 'N/A')}")
            
            if target_result.get('notes'):
                print(f"\n📝 备注: {target_result['notes']}")
            
            return target_result
            
        except json.JSONDecodeError as e:
            print(f"\n⚠️  JSON解析失败: {e}")
            print("📄 返回原始文本结果")
            return {"raw_response": content, "error": "JSON解析失败"}
        
    except Exception as e:
        print(f"❌ 目标区域识别失败: {e}")
        return {"error": str(e)}

def crop_target_area(image_path: str, target_result: Dict[str, Any], target_text: str = "真相1解读") -> Dict[str, Any]:
    """
    裁剪目标区域
    
    Args:
        image_path: 原始图片路径
        target_result: 目标区域识别结果
        target_text: 目标文本描述
        
    Returns:
        dict: 裁剪结果信息
    """
    try:
        # 检查是否找到目标区域
        if not target_result.get('target_found', False):
            print(f"❌ 未找到目标区域 '{target_text}'，无法裁剪")
            return {"error": "目标区域未找到", "target": target_text}
    
        
        # 打开原始图片
        original_image = Image.open(image_path)
        image_width, image_height = original_image.size
        
        print(f"📐 原图尺寸: {image_width} x {image_height} 像素")
        
        # 获取位置信息
        position = target_result.get('position_info', {})
        if not position:
            print(f"❌ 缺少位置信息")
            return {"error": "缺少位置信息", "target": target_text}
        
        # 计算像素坐标
        left, top, right, bottom = calculate_pixel_coordinates(position, image_width, image_height)
        
        print(f"\n✂️  裁剪目标区域: {target_text}")
        print(f"   百分比位置: x={position.get('x')}%, y={position.get('y')}%, w={position.get('width')}%, h={position.get('height')}%")
        print(f"   像素坐标: ({left}, {top}) -> ({right}, {bottom})")
        print(f"   裁剪尺寸: {right-left} x {bottom-top} 像素")
        
        # 裁剪图片
        if right > left and bottom > top:
            cropped_image = original_image.crop((left, top, right, bottom))
            
            # 确保输出目录存在
            output_dir = "output/cropped_modules"
            os.makedirs(output_dir, exist_ok=True)
            
            # 生成文件名
            safe_name = "".join(c for c in target_text if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_name = safe_name.replace(' ', '_')
            confidence = target_result.get('confidence', 'medium')
            timestamp = __import__('datetime').datetime.now().strftime("%Y%m%d_%H%M%S")
            
            filename = f"{safe_name}_{confidence}_{timestamp}.png"
            filepath = os.path.join(output_dir, filename)
            
            # 保存裁剪后的图片
            cropped_image.save(filepath, 'PNG')
            
            # 记录结果
            crop_result = {
                'target_text': target_text,
                'target_found': True,
                'confidence': confidence,
                'area_analysis': target_result.get('area_analysis', {}),
                'crop_info': {
                    'original_position': position,
                    'pixel_coordinates': {
                        'left': left,
                        'top': top,
                        'right': right,
                        'bottom': bottom
                    },
                    'cropped_size': {
                        'width': right - left,
                        'height': bottom - top
                    },
                    'file_path': filepath,
                    'file_size': os.path.getsize(filepath) if os.path.exists(filepath) else 0,
                    'timestamp': timestamp
                }
            }
            
            size_kb = crop_result['crop_info']['file_size'] / 1024
            print(f"   ✅ 已保存: {filepath}")
            print(f"   📁 文件大小: {size_kb:.1f}KB")
            print(f"   🎯 识别信心: {confidence}")
            
            return crop_result
            
        else:
            print(f"❌ 无效的裁剪区域")
            return {"error": "无效裁剪区域", "target": target_text}
            
    except Exception as e:
        print(f"❌ 裁剪失败: {e}")
        return {"error": str(e), "target": target_text}

def calculate_pixel_coordinates(position: Dict[str, Any], image_width: int, image_height: int) -> Tuple[int, int, int, int]:
    """
    将百分比位置转换为实际像素坐标
    
    Args:
        position: 包含百分比位置信息的字典 {x, y, width, height}
        image_width: 图片实际宽度（像素）
        image_height: 图片实际高度（像素）
        
    Returns:
        tuple: (left, top, right, bottom) 像素坐标
    """
    # 提取百分比值（移除%符号）
    x_percent = float(str(position.get('x', 0)).replace('%', ''))
    y_percent = float(str(position.get('y', 0)).replace('%', ''))
    width_percent = float(str(position.get('width', 0)).replace('%', ''))
    height_percent = float(str(position.get('height', 0)).replace('%', ''))
    
    # 计算实际像素坐标
    left = int((x_percent / 100) * image_width)
    top = int((y_percent / 100) * image_height)
    right = left + int((width_percent / 100) * image_width)
    bottom = top + int((height_percent / 100) * image_height)
    
    # 确保坐标在图片范围内
    left = max(0, min(left, image_width))
    top = max(0, min(top, image_height))
    right = max(left, min(right, image_width))
    bottom = max(top, min(bottom, image_height))
    
    return (left, top, right, bottom)

def create_target_crop_workflow(target_text: str = "真相1解读"):
    """
    创建针对特定目标区域的识别和裁剪工作流
    
    Args:
        target_text: 要寻找和裁剪的目标文本或区域描述
    """
    print("🎯 启动特定目标区域裁剪工作流")
    print("="*60)
    print(f"🔍 目标区域: {target_text}")
    print("="*60)
    
    # 步骤1: 识别目标区域
    print("📍 步骤1: 目标区域识别")
    print("-" * 40)
    target_result = identify_target_area("data/demo.jpg", target_text)
    
    if 'error' in target_result:
        print(f"❌ 目标区域识别失败，终止工作流")
        return target_result
    
    if not target_result.get('target_found', False):
        print(f"❌ 未找到目标区域 '{target_text}'，终止工作流")
        return target_result
    
    # 步骤2: 裁剪目标区域
    print(f"\n✂️  步骤2: 裁剪目标区域")
    print("-" * 40)
    crop_result = crop_target_area("data/demo.jpg", target_result, target_text)
    
    # 生成最终结果
    final_result = {
        'workflow_type': 'target_area_crop',
        'target_text': target_text,
        'step1_identification': target_result,
        'step2_cropping': crop_result,
        'summary': {
            'target_found': target_result.get('target_found', False),
            'crop_successful': 'error' not in crop_result,
            'confidence': target_result.get('confidence', 'unknown'),
            'video_potential': target_result.get('video_suitability', {}).get('video_potential', 'unknown'),
            'output_directory': 'output/cropped_modules',
            'timestamp': __import__('datetime').datetime.now().isoformat()
        }
    }
    
    print("\n" + "="*60)
    print(f"🎯 目标区域 '{target_text}' 工作流完成！")
    print("="*60)
    
    summary = final_result['summary']
    print(f"   🔍 目标发现: {'✅ 成功' if summary['target_found'] else '❌ 失败'}")
    print(f"   ✂️  裁剪结果: {'✅ 成功' if summary['crop_successful'] else '❌ 失败'}")
    
    if summary['crop_successful']:
        crop_info = crop_result.get('crop_info', {})
        if crop_info:
            print(f"   📁 输出文件: {crop_info.get('file_path', 'N/A')}")
            print(f"   📐 图片尺寸: {crop_info.get('cropped_size', {}).get('width', 'N/A')} x {crop_info.get('cropped_size', {}).get('height', 'N/A')} 像素")
            print(f"   🎬 视频潜力: {summary['video_potential']}")
            print(f"   🎯 识别信心: {summary['confidence']}")
    
    if 'error' in crop_result:
        print(f"   ⚠️  失败原因: {crop_result.get('error', '未知错误')}")
    
    print("\n🎯 工作流特点：")
    print("1. ✅ 专门针对特定目标区域")
    print("2. ✅ 精确识别和定位")
    print("3. ✅ 自动视频适用性评估") 
    print("4. ✅ 高效单一目标处理")
    
    print("\n🔄 下一步建议：")
    if summary['crop_successful']:
        print("1. 检查裁剪后的图片质量和完整性")
        print("2. 根据内容设计视频动画效果")
        print("3. 分析文字内容制作配音脚本")
        print("4. 设计合适的视频时长和节奏")
    else:
        print("1. 检查目标文本是否正确")
        print("2. 尝试其他相似的关键词")
        print("3. 手动验证图片中是否包含目标内容")
    
    # 保存结果到文件
    try:
        safe_filename = "".join(c for c in target_text if c.isalnum() or c in (' ', '-', '_')).strip().replace(' ', '_')
        result_filename = f'output/{safe_filename}_crop_result.json'
        with open(result_filename, 'w', encoding='utf-8') as f:
            json.dump(final_result, f, ensure_ascii=False, indent=2)
        print(f"\n💾 完整结果已保存到: {result_filename}")
    except Exception as e:
        print(f"\n⚠️  保存结果失败: {e}")
    
    return final_result

if __name__ == "__main__":
    # 运行特定目标区域裁剪工作流
    for target_area in ["真相1", "真相2", "真相3"]:
        workflow_result = create_target_crop_workflow(target_area)