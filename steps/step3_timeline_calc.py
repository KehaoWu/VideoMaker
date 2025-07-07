"""
步骤3：时间轴重计算
根据实际音频时长重新计算视频时间轴
"""

import os
from typing import Dict, List, Any

from .base_step import BaseStep, StepResult
from models.video_plan import VideoPlan
from utils.logger import get_logger
from utils.config_manager import get_config


class Step3TimelineCalc(BaseStep):
    """时间轴重计算处理步骤"""
    
    def __init__(self):
        super().__init__()
        self.step_name = "时间轴重计算"
        self.step_id = "step3"
        self.logger = get_logger(__name__)
        self.config = get_config()
    
    def execute(self, video_plan: VideoPlan, output_dir: str) -> StepResult:
        """
        执行时间轴重计算步骤
        
        Args:
            video_plan: 视频规划对象
            output_dir: 输出目录
            
        Returns:
            StepResult: 步骤执行结果
        """
        self.logger.info("开始执行时间轴重计算步骤")
        
        try:
            # 验证输入
            if not self.validate_inputs(video_plan):
                return StepResult(
                    step_name=self.step_name,
                    status="failed",
                    error_message="输入验证失败"
                )
            
            # 计算音频总时长
            total_audio_duration = self._calculate_total_audio_duration(video_plan)
            
            # 更新元信息中的目标时长
            original_duration = video_plan.meta_info.target_duration
            video_plan.meta_info.target_duration = total_audio_duration
            
            # 重新计算视频段落时间轴
            self._recalculate_video_timeline(video_plan, total_audio_duration)
            
            # 重新计算视频合成时间轴
            if hasattr(video_plan, 'video_composition') and video_plan.video_composition:
                self._recalculate_composition_timeline(video_plan, total_audio_duration)
            
            self.logger.info(f"时间轴重计算完成: {original_duration:.2f}s -> {total_audio_duration:.2f}s")
            
            return StepResult(
                step_name=self.step_name,
                status="completed",
                metadata={
                    "original_duration": original_duration,
                    "new_duration": total_audio_duration,
                    "audio_segments": len(video_plan.narration_script.segments),
                    "duration_change": total_audio_duration - original_duration
                }
            )
            
        except Exception as e:
            self.logger.error(f"时间轴重计算步骤执行失败: {e}")
            return StepResult(
                step_name=self.step_name,
                status="failed",
                error_message=str(e)
            )
    
    def _calculate_total_audio_duration(self, video_plan: VideoPlan) -> float:
        """计算音频总时长"""
        total_duration = 0.0
        
        if video_plan.narration_script and video_plan.narration_script.segments:
            for segment in video_plan.narration_script.segments:
                total_duration += segment.duration
        
        return total_duration
    
    def _recalculate_video_timeline(self, video_plan: VideoPlan, total_duration: float):
        """重新计算视频段落时间轴"""
        if not hasattr(video_plan, 'text_to_video_plan') or not video_plan.text_to_video_plan:
            return
        
        segments = video_plan.text_to_video_plan.segments
        if not segments:
            return
        
        # 计算每个视频段落的时长分配
        if len(segments) == 1:
            # 只有一个段落，使用全部时长
            segments[0].duration = total_duration
            segments[0].start_time = 0.0
        else:
            # 多个段落，按比例分配
            original_total = sum(seg.duration for seg in segments if seg.duration > 0)
            
            if original_total > 0:
                # 按原始比例重新分配
                current_time = 0.0
                for segment in segments:
                    ratio = segment.duration / original_total
                    segment.duration = total_duration * ratio
                    segment.start_time = current_time
                    current_time += segment.duration
            else:
                # 平均分配
                segment_duration = total_duration / len(segments)
                current_time = 0.0
                for segment in segments:
                    segment.duration = segment_duration
                    segment.start_time = current_time
                    current_time += segment_duration
        
        self.logger.info(f"重新计算了 {len(segments)} 个视频段落的时间轴")
    
    def _recalculate_composition_timeline(self, video_plan: VideoPlan, total_duration: float):
        """重新计算视频合成时间轴"""
        composition = video_plan.video_composition
        
        # 更新时间轴总时长
        composition.timeline.total_duration = total_duration
        
        # 调整音频图层时长
        for layer in composition.layers:
            if layer.layer_type == 'audio':
                # 音频图层使用实际音频时长
                if layer.duration == 0 or layer.duration > total_duration:
                    layer.duration = total_duration
            elif layer.layer_type in ['video', 'image']:
                # 视频/图片图层根据需要调整
                if layer.duration == 0 or layer.end_time > total_duration:
                    layer.duration = min(layer.duration, total_duration - layer.start_time)
        
        # 调整转场效果时间
        for transition in composition.transitions:
            if transition.start_time + transition.duration > total_duration:
                # 调整转场时间或删除超出的转场
                if transition.start_time < total_duration:
                    transition.duration = total_duration - transition.start_time
                else:
                    # 标记为需要删除的转场
                    transition.duration = 0
        
        # 删除无效的转场
        composition.transitions = [t for t in composition.transitions if t.duration > 0]
        
        # 调整视觉效果时间
        for effect in composition.effects:
            if effect.start_time + effect.duration > total_duration:
                if effect.start_time < total_duration:
                    effect.duration = total_duration - effect.start_time
                else:
                    effect.duration = 0
        
        # 删除无效的视觉效果
        composition.effects = [e for e in composition.effects if e.duration > 0]
        
        self.logger.info("重新计算了视频合成时间轴")
    
    def validate_inputs(self, video_plan: VideoPlan) -> bool:
        """验证输入参数"""
        try:
            # 检查narration_script
            if not video_plan.narration_script:
                self.logger.error("缺少narration_script")
                return False
            
            # 检查音频段落
            segments = video_plan.narration_script.segments
            if not segments:
                self.logger.error("没有音频段落")
                return False
            
            # 验证音频段落有有效时长
            valid_segments = [s for s in segments if s.duration > 0]
            if not valid_segments:
                self.logger.error("没有有效时长的音频段落")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"输入验证失败: {e}")
            return False
    
    def get_dependencies(self) -> List[str]:
        """获取依赖的步骤列表"""
        return ["step2"]  # 依赖音频生成步骤
    
    def get_output_info(self, video_plan: VideoPlan) -> Dict[str, Any]:
        """获取输出信息"""
        return {
            "modifies_timeline": True,
            "updates_meta_info": True,
            "recalculates_segments": True
        } 