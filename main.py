#!/usr/bin/env python3
"""
VideoMaker - 主程序入口
基于processing_workflow的分层架构设计
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from PIL import Image
import click

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from models.video_plan import VideoPlan
from steps.workflow_executor import WorkflowExecutor
from utils.logger import get_logger
from utils.config_manager import get_config
from utils.validators import ValidationResult
from utils.directory_manager import initialize_directories, auto_cleanup_if_needed
from apis.claude_api import OpenAIAPI
import config
from steps.step0_video_planning import Step0VideoPlanning

# 设置日志
logger = get_logger(__name__)

@click.group()
def cli():
    """视频生成工具 CLI"""
    pass

@cli.command()
@click.argument('image_path', type=click.Path(exists=True))
@click.option('--duration', '-d', type=float, default=60.0, help='视频时长(秒)')
@click.option('--output-dir', '-o', type=click.Path(), default='output/plans', help='输出目录')
def plan(image_path: str, duration: float, output_dir: str):
    """生成视频规划
    
    Args:
        image_path: 源图片路径
        duration: 视频时长(秒)
        output_dir: 输出目录
    """
    try:
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 创建空的视频规划
        video_plan = VideoPlan.create_empty_plan(
            image_path=image_path,
            output_dir=output_dir,
            duration=duration
        )
        
        # 创建Step0实例
        step0 = Step0VideoPlanning()
        
        # 执行规划
        video_plan.status = "planning"
        try:
            video_plan = step0.execute(video_plan)
            if video_plan.status != "completed":
                raise Exception("视频规划生成失败")
            
            # 验证规划
            is_valid, errors = video_plan.validate()
            if not is_valid:
                raise Exception(f"规划验证失败: {'; '.join(errors)}")
            
            # 保存规划
            output_file = step0.save_to_json_file(video_plan)
            logger.info(f"视频规划已保存到: {output_file}")
            
        except Exception as e:
            video_plan.status = "failed"
            logger.error(f"创建视频规划失败: {str(e)}")
            raise click.ClickException(str(e))
            
    except Exception as e:
        logger.error(f"处理失败: {str(e)}")
        raise click.ClickException(str(e))

def setup_logging() -> None:
    """设置日志系统和初始化环境"""
    logger = get_logger(__name__)
    logger.info("VideoMaker 启动")
    
    # 初始化目录结构
    logger.info("初始化目录结构...")
    if initialize_directories():
        logger.info("✓ 目录结构初始化完成")
    else:
        logger.warning("目录结构初始化失败")
    
    # 自动清理缓存（如果需要）
    if auto_cleanup_if_needed():
        logger.info("✓ 自动缓存清理完成")


def validate_input_file(file_path: str, file_type: str = "json") -> bool:
    """验证输入文件"""
    if not os.path.exists(file_path):
        print(f"错误: 文件不存在 {file_path}")
        return False
    
    # 检查文件扩展名
    ext = os.path.splitext(file_path)[1].lower()
    
    if file_type == "json":
        if ext not in ['.json']:
            print(f"错误: 不支持的文件格式 {ext}，仅支持 .json")
            return False
    elif file_type == "image":
        if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']:
            print(f"错误: 不支持的图片格式 {ext}")
            return False
    
    return True


def get_image_dimensions(image_path: str) -> tuple[int, int]:
    """获取图片尺寸"""
    try:
        with Image.open(image_path) as img:
            return img.size  # (width, height)
    except Exception as e:
        print(f"警告: 无法获取图片尺寸: {e}")
        return (1920, 1080)  # 默认尺寸


def create_output_directory(output_dir: Optional[str] = None) -> str:
    """创建输出目录"""
    if not output_dir:
        # 使用配置中的默认输出目录
        try:
            config_data = get_config()
            output_dir = config_data.get('paths.output_dir', config.OUTPUT_DIR)
        except Exception:
            output_dir = config.OUTPUT_DIR
    
    # 添加时间戳子目录
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    full_output_dir = os.path.join(output_dir, f'video_{timestamp}')
    
    os.makedirs(full_output_dir, exist_ok=True)
    return full_output_dir


def load_video_plan(plan_file: str) -> VideoPlan:
    """加载视频规划"""
    logger = get_logger(__name__)
    logger.info(f"加载视频规划: {plan_file}")
    
    try:
        video_plan = VideoPlan.from_json_file(plan_file)
        logger.info(f"成功加载视频规划: {video_plan.title}")
        return video_plan
    except Exception as e:
        logger.error(f"加载视频规划失败: {e}")
        raise


def validate_video_plan(video_plan: VideoPlan) -> ValidationResult:
    """验证视频规划数据"""
    logger = get_logger(__name__)
    logger.info("验证视频规划数据")
    
    is_valid, errors = video_plan.validate()
    
    if not is_valid:
        logger.error("视频规划验证失败")
        for error in errors:
            logger.error(f"  - {error}")
    else:
        logger.info("✓ 视频规划验证通过")
    
    return ValidationResult(is_valid=is_valid, errors=errors)


def execute_workflow(video_plan: VideoPlan, output_dir: str, steps_to_run: Optional[List[str]] = None) -> bool:
    """执行工作流"""
    logger = get_logger(__name__)
    logger.info("开始执行视频制作工作流")
    
    # 创建工作流执行器
    executor = WorkflowExecutor()
    
    # 执行工作流
    results = executor.execute_workflow(video_plan, output_dir, steps_to_run)
    
    # 统计结果
    success_count = 0
    for result in results:
        if result.is_successful:
            success_count += 1
            logger.info(f"✓ {result.step_name} 完成 ({result.duration:.1f}s)")
            for file_path in result.output_files:
                logger.info(f"    输出: {file_path}")
        else:
            logger.error(f"✗ {result.step_name} 失败: {result.error_message}")
    
    total_steps = len(results)
    logger.info(f"完成 {success_count}/{total_steps} 个步骤")
    
    return success_count == total_steps


def cmd_generate(args) -> int:
    """generate命令处理函数"""
    print(f"🎬 执行视频生成: {args.plan_file}")
    
    try:
        # 验证计划文件
        if not validate_input_file(args.plan_file, "json"):
            return 1
        
        # 加载视频规划
        if args.verbose:
            print(f"加载视频规划: {args.plan_file}")
        
        video_plan = load_video_plan(args.plan_file)
        
        # 验证视频规划
        validation_result = validate_video_plan(video_plan)
        if not validation_result.is_valid:
            print("❌ 视频规划验证失败:")
            for error in validation_result.errors:
                print(f"  - {error}")
            return 1
        
        if args.verbose:
            print("✓ 视频规划验证通过")
        
        # 如果只是验证模式，到此结束
        if args.validate_only:
            print("✓ 验证完成")
            return 0
        
        # 创建输出目录
        output_dir = create_output_directory(args.output)
        print(f"📁 输出目录: {output_dir}")
        
        # 保存验证后的视频规划到输出目录
        plan_output_path = os.path.join(output_dir, 'video_plan.json')
        video_plan.save_to_json_file(plan_output_path)
        
        # 确定要执行的步骤
        steps_to_run = None
        if args.steps:
            steps_to_run = [step.strip() for step in args.steps.split(',')]
        
        # 执行工作流
        print("🚀 开始执行视频制作工作流...")
        success = execute_workflow(video_plan, output_dir, steps_to_run)
        
        if success:
            print("🎉 视频制作完成!")
            return 0
        else:
            print("⚠️  部分步骤执行失败")
            return 1
            
    except FileNotFoundError as e:
        print(f"❌ 文件错误: {e}")
        return 1
    except Exception as e:
        print(f"❌ 执行错误: {e}")
        return 1


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='VideoMaker - 基于视频规划的视频制作工具',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # 创建子命令
    subparsers = parser.add_subparsers(
        title='命令',
        description='可用的命令',
        help='使用 "python main.py <命令> --help" 查看详细帮助',
        dest='command'
    )
    
    # plan 子命令
    plan_parser = subparsers.add_parser(
        'plan',
        help='从图片生成视频计划',
        description='根据输入图片创建视频制作计划，AI自动生成视频描述和旁白文本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python main.py plan assets/input/images/class_01.jpg
  python main.py plan my_image.png --title "我的视频" --duration 60
  python main.py plan image.jpg --title "产品介绍" --duration 45
  
注意: 视频描述和旁白文本将由AI根据图片内容自动生成
        """
    )
    
    plan_parser.add_argument(
        'image',
        help='输入图片路径 (支持: PNG, JPG, JPEG, GIF, WEBP, BMP)'
    )
    
    plan_parser.add_argument(
        '--title', '-t',
        default='VideoMaker生成的视频',
        help='视频标题 (默认: VideoMaker生成的视频)'
    )
    
    plan_parser.add_argument(
        '--duration',
        type=float,
        default=30.0,
        help='视频时长，单位秒 (默认: 30.0)'
    )
    
    plan_parser.add_argument(
        '--output', '-o',
        help='输出目录 (默认: output)'
    )
    
    # generate 子命令
    generate_parser = subparsers.add_parser(
        'generate',
        help='执行视频生成',
        description='根据视频计划文件生成视频',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python main.py generate output/video_plan_20241201_120000.json
  python main.py generate my_plan.json --output /path/to/output
  python main.py generate my_plan.json --steps step1,step2,step3
  python main.py generate my_plan.json --validate-only
        """
    )
    
    generate_parser.add_argument(
        'plan_file',
        help='视频规划JSON文件路径'
    )
    
    generate_parser.add_argument(
        '--output', '-o',
        help='输出目录路径 (默认: output/video_YYYYMMDD_HHMMSS)'
    )
    
    generate_parser.add_argument(
        '--steps',
        help='指定要执行的步骤，用逗号分隔 (如: step1,step2,step3)'
    )
    
    generate_parser.add_argument(
        '--validate-only',
        action='store_true',
        help='仅验证视频规划文件，不执行处理步骤'
    )
    
    generate_parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='详细输出模式'
    )
    
    # 全局参数
    parser.add_argument(
        '--config',
        help='指定配置文件路径 (默认: config.yaml)'
    )
    
    args = parser.parse_args()
    
    # 如果没有指定命令，显示帮助
    if not args.command:
        parser.print_help()
        return 1
    
    # 设置日志
    setup_logging()
    
    # 根据命令调用相应函数
    try:
        if args.command == 'plan':
            return cmd_plan(args)
        elif args.command == 'generate':
            return cmd_generate(args)
        else:
            print(f"未知命令: {args.command}")
            return 1
    except KeyboardInterrupt:
        print("\n⚠️ 操作被用户中断")
        return 1
    except Exception as e:
        print(f"❌ 未预期的错误: {e}")
        return 1


if __name__ == '__main__':
    cli() 