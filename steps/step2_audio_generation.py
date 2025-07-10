"""
步骤2：音频生成
使用TTS API将旁白脚本转换为语音音频
"""

import os
from typing import Dict, List, Any
from pathlib import Path

from .base_step import BaseStep, StepResult
from models.video_plan import VideoPlan
from models.narration_script import NarrationSegment
from apis.tts_api import TTSAPI
from utils.logger import get_logger
from utils.file_utils import ensure_directory, safe_filename
from utils.config_manager import get_config


class Step2AudioGeneration(BaseStep):
    """音频生成处理步骤"""
    
    def __init__(self):
        super().__init__()
        self.step_name = "音频生成"
        self.step_id = "step2"
        self.logger = get_logger(__name__)
        self.config = get_config()
        
        # 初始化TTS API客户端
        try:
            self.tts_api = TTSAPI()
        except Exception as e:
            self.logger.warning(f"TTS API初始化失败: {e}")
            self.tts_api = None
    
    def execute(self, video_plan: VideoPlan, output_dir: str) -> StepResult:
        """
        执行音频生成步骤
        
        Args:
            video_plan: 视频规划对象
            output_dir: 输出目录
            
        Returns:
            StepResult: 步骤执行结果
        """
        self.logger.info("开始执行音频生成步骤")
        
        try:
            # 验证输入
            if not self.validate_inputs(video_plan):
                return StepResult(
                    step_name=self.step_name,
                    status="failed",
                    error_message="输入验证失败"
                )
            
            # 检查TTS API
            if not self.tts_api:
                return StepResult(
                    step_name=self.step_name,
                    status="failed",
                    error_message="TTS API未初始化"
                )
            
            # 创建输出目录
            audio_dir = os.path.join(output_dir, "audio")  # 使用标准化的目录名
            ensure_directory(audio_dir)
            
            # 获取音频段落
            segments = video_plan.narration_script.segments
            if not segments:
                return StepResult(
                    step_name=self.step_name,
                    status="failed",
                    error_message="没有音频段落"
                )
            
            output_files = []
            total_duration = 0.0
            
            # 生成每个音频段落
            for i, segment in enumerate(segments):
                try:
                    output_path = self._generate_segment_audio(segment, audio_dir, i)
                    if output_path:
                        output_files.append(output_path)
                        # 更新segment的音频文件路径
                        segment.audio_file_path = output_path
                        total_duration += segment.estimated_duration
                        self.logger.info(f"成功生成音频: {segment.segment_id} -> {output_path}")
                        
                except Exception as e:
                    self.logger.error(f"生成音频段落 {segment.segment_id} 失败: {e}")
                    continue
            
            if output_files:
                return StepResult(
                    step_name=self.step_name,
                    status="completed",
                    output_files=output_files,
                    metadata={
                        "total_segments": len(segments),
                        "successful_generations": len(output_files),
                        "total_duration": total_duration
                    }
                )
            else:
                return StepResult(
                    step_name=self.step_name,
                    status="failed",
                    error_message="没有成功生成任何音频"
                )
                
        except Exception as e:
            self.logger.error(f"音频生成步骤执行失败: {e}")
            return StepResult(
                step_name=self.step_name,
                status="failed",
                error_message=str(e)
            )
    
    def _generate_segment_audio(self, segment: NarrationSegment, output_dir: str, index: int) -> str:
        """生成单个音频段落"""
        try:
            # 验证文本内容
            if not segment.text or not segment.text.strip():
                raise ValueError("音频段落文本为空")
            
            # 生成输出文件名
            safe_name = safe_filename(segment.segment_id or f"segment_{index+1}")
            output_filename = f"audio_{safe_name}.mp3"
            output_path = os.path.join(output_dir, output_filename)
            
            # 调用TTS API生成语音
            result = self.tts_api.generate_audio(
                text=segment.text,
                output_path=output_path,
                voice_type=segment.voice  # 使用voice作为voice_type参数
            )
            
            if result.get('success'):
                # 更新音频段落的实际时长
                actual_duration = result.get('duration', 0)
                if actual_duration > 0:
                    segment.actual_duration = actual_duration
                
                return output_path
            else:
                raise ValueError(f"TTS生成失败: {result.get('error', '未知错误')}")
                
        except Exception as e:
            self.logger.error(f"生成音频段落失败: {e}")
            raise
    
    def validate_inputs(self, video_plan: VideoPlan) -> bool:
        """验证输入参数"""
        if not video_plan:
            self.logger.error("缺少video_plan")
            return False
            
        if not video_plan.narration_script:
            self.logger.error("缺少narration_script")
            return False
            
        if not video_plan.narration_script.get('segments'):
            self.logger.error("narration_script中没有语音片段")
            return False
            
        return True
    
    def get_dependencies(self) -> List[str]:
        """获取依赖的步骤列表"""
        return []  # 音频生成可以独立执行
    
    def get_output_info(self, video_plan: VideoPlan) -> Dict[str, Any]:
        """获取输出信息"""
        segments = video_plan.narration_script.segments if video_plan.narration_script else []
        return {
            "expected_outputs": len(segments),
            "output_format": "MP3",
            "output_prefix": "audio_"
        }
    
    def estimate_processing_time(self, video_plan: VideoPlan) -> float:
        """估算处理时间（秒）"""
        if not video_plan.narration_script or not video_plan.narration_script.segments:
            return 0.0
        
        # 估算：每个字符约0.1秒的处理时间
        total_chars = sum(len(segment.text) for segment in video_plan.narration_script.segments)
        return total_chars * 0.1 