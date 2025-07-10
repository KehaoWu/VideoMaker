"""
工作流执行器
统一管理和执行视频制作的5个步骤
"""

import os
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

from .base_step import BaseStep, StepResult
from models.video_plan import VideoPlan
from models.constants import STEP_NAMES, STEP_DEPENDENCIES
from utils.logger import get_logger
from utils.file_utils import ensure_directory
from utils.config_manager import get_config


class WorkflowExecutor:
    """工作流执行器"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.config = get_config()
        self.steps: Dict[str, BaseStep] = {}
        self.execution_history: List[StepResult] = []
        
        # 注册所有步骤
        self._register_steps()
    
    def _register_steps(self):
        """注册所有处理步骤"""
        try:
            # 动态导入步骤类
            from .step1_image_cutting import Step1ImageCutting
            from .step2_audio_generation import Step2AudioGeneration
            from .step3_timeline_calc import Step3TimelineCalc  
            from .step4_text_to_video import Step4TextToVideo
            from .step5_video_composition import Step5VideoComposition
            
            # 注册所有步骤
            self.steps['step1'] = Step1ImageCutting()
            self.steps['step2'] = Step2AudioGeneration()
            self.steps['step3'] = Step3TimelineCalc()
            self.steps['step4'] = Step4TextToVideo()
            self.steps['step5'] = Step5VideoComposition()
            
            self.logger.info(f"已注册 {len(self.steps)} 个处理步骤")
            
        except ImportError as e:
            self.logger.error(f"步骤注册失败: {e}")
    
    def execute_workflow(self, video_plan: VideoPlan, output_dir: str,
                        enabled_steps: Optional[List[str]] = None,
                        skip_dependencies: bool = False) -> Dict[str, Any]:
        """
        执行完整的工作流
        
        Args:
            video_plan: 视频规划对象
            output_dir: 输出目录
            enabled_steps: 启用的步骤列表，None表示执行所有步骤
            skip_dependencies: 是否跳过依赖检查
            
        Returns:
            工作流执行结果
        """
        self.logger.info("开始执行视频制作工作流")
        
        # 确保输出目录存在并创建子目录结构
        ensure_directory(output_dir)
        subdirs = [
            'cuts',          # 切图输出
            'audio',         # 音频文件
            'background',    # 背景视频
            'composition',   # 合成中间文件
            'final'          # 最终输出
        ]
        
        for subdir in subdirs:
            ensure_directory(os.path.join(output_dir, subdir))
        
        # 记录开始时间
        start_time = datetime.now()
        
        # 确定要执行的步骤
        if enabled_steps is None:
            enabled_steps = list(self.steps.keys())
        
        # 验证步骤
        valid_steps = self._validate_steps(enabled_steps, skip_dependencies)
        if not valid_steps:
            return {
                'success': False,
                'error': '没有有效的步骤可执行',
                'execution_time': 0
            }
        
        # 按依赖顺序执行步骤
        execution_order = self._get_execution_order(valid_steps)
        
        results = {}
        failed_steps = []
        
        # 执行每个步骤
        for step_id in execution_order:
            if failed_steps:
                # 如果有前序步骤失败，记录后续步骤为跳过状态
                self.logger.warning(f"由于前序步骤失败，跳过步骤: {step_id}")
                results[step_id] = StepResult(
                    step_name=f"{step_id} - {self.steps[step_id].step_name}",
                    status="skipped",
                    error_message="前序步骤失败，步骤被跳过"
                )
                continue
                
            self.logger.info(f"执行步骤: {step_id} - {self.steps[step_id].step_name}")
            
            try:
                # 执行步骤
                result = self.steps[step_id].execute(video_plan, output_dir)
                results[step_id] = result
                
                # 检查执行结果
                if not result.is_successful:
                    self.logger.error(f"步骤 {step_id} 执行失败: {result.error_message}")
                    failed_steps.append(step_id)
                    
            except Exception as e:
                self.logger.error(f"步骤 {step_id} 执行异常: {e}")
                failed_steps.append(step_id)
                results[step_id] = StepResult(
                    step_name=f"{step_id} - {self.steps[step_id].step_name}",
                    status="failed",
                    error_message=str(e)
                )
        
        # 记录结束时间
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        # 生成工作流结果
        workflow_result = {
            'success': len(failed_steps) == 0,
            'total_steps': len(execution_order),
            'completed_steps': len(execution_order) - len(failed_steps),
            'failed_steps': failed_steps,
            'execution_time': execution_time,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'step_results': {step_id: result.to_dict() for step_id, result in results.items()},
            'output_directory': output_dir
        }
        
        # 保存执行报告
        self._save_execution_report(workflow_result, output_dir)
        
        if workflow_result['success']:
            self.logger.info(f"工作流执行成功，用时 {execution_time:.2f} 秒")
        else:
            self.logger.error(f"工作流执行失败，{len(failed_steps)} 个步骤失败")
            # 输出失败的步骤
            for step_id in failed_steps:
                result = results[step_id]
                self.logger.error(f"  - {step_id}: {result.error_message}")
        
        return workflow_result
    
    def execute_single_step(self, step_id: str, video_plan: VideoPlan, output_dir: str) -> StepResult:
        """
        执行单个步骤
        
        Args:
            step_id: 步骤ID
            video_plan: 视频规划对象
            output_dir: 输出目录
            
        Returns:
            步骤执行结果
        """
        if step_id not in self.steps:
            raise ValueError(f"未知的步骤ID: {step_id}")
        
        self.logger.info(f"执行单个步骤: {step_id}")
        
        step_instance = self.steps[step_id]
        result = step_instance.execute(video_plan, output_dir)
        
        self.execution_history.append(result)
        return result
    
    def _validate_steps(self, step_ids: List[str], skip_dependencies: bool) -> List[str]:
        """验证步骤的有效性"""
        valid_steps = []
        
        for step_id in step_ids:
            if step_id not in self.steps:
                self.logger.warning(f"步骤 {step_id} 未注册，跳过")
                continue
            
            if not skip_dependencies:
                # 检查依赖
                dependencies = STEP_DEPENDENCIES.get(step_id, [])
                missing_deps = [dep for dep in dependencies if dep not in step_ids]
                if missing_deps:
                    self.logger.warning(f"步骤 {step_id} 缺少依赖 {missing_deps}，跳过")
                    continue
            
            valid_steps.append(step_id)
        
        return valid_steps
    
    def _get_execution_order(self, step_ids: List[str]) -> List[str]:
        """根据依赖关系确定执行顺序"""
        ordered_steps = []
        remaining_steps = step_ids.copy()
        
        while remaining_steps:
            # 查找没有未满足依赖的步骤
            ready_steps = []
            for step_id in remaining_steps:
                dependencies = STEP_DEPENDENCIES.get(step_id, [])
                if all(dep in ordered_steps for dep in dependencies):
                    ready_steps.append(step_id)
            
            if not ready_steps:
                # 如果没有就绪步骤，说明存在循环依赖
                self.logger.error(f"存在循环依赖，剩余步骤: {remaining_steps}")
                break
            
            # 按步骤ID排序，确保一致性
            ready_steps.sort()
            
            # 添加就绪步骤到执行序列
            for step_id in ready_steps:
                ordered_steps.append(step_id)
                remaining_steps.remove(step_id)
        
        return ordered_steps
    
    def _save_execution_report(self, workflow_result: Dict[str, Any], output_dir: str):
        """保存执行报告"""
        try:
            import json
            
            report_path = os.path.join(output_dir, "execution_report.json")
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(workflow_result, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"执行报告已保存: {report_path}")
            
        except Exception as e:
            self.logger.error(f"保存执行报告失败: {e}")
    
    def get_step_status(self, step_id: str) -> Optional[str]:
        """获取步骤状态"""
        for result in reversed(self.execution_history):
            if hasattr(result, 'step_id') and result.step_id == step_id:
                return result.status
        return None
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """获取执行摘要"""
        if not self.execution_history:
            return {'total': 0, 'completed': 0, 'failed': 0, 'pending': 0}
        
        status_counts = {}
        for result in self.execution_history:
            status = result.status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            'total': len(self.execution_history),
            'completed': status_counts.get('completed', 0),
            'failed': status_counts.get('failed', 0),
            'pending': status_counts.get('pending', 0),
            'running': status_counts.get('running', 0)
        }
    
    def clear_history(self):
        """清空执行历史"""
        self.execution_history.clear()
        self.logger.info("执行历史已清空")
    
    def validate_video_plan(self, video_plan: VideoPlan) -> Dict[str, Any]:
        """验证视频规划对所有步骤的适用性"""
        validation_results = {}
        
        for step_id, step_instance in self.steps.items():
            try:
                is_valid = step_instance.validate_inputs(video_plan)
                validation_results[step_id] = {
                    'valid': is_valid,
                    'step_name': STEP_NAMES.get(step_id, step_id)
                }
            except Exception as e:
                validation_results[step_id] = {
                    'valid': False,
                    'error': str(e),
                    'step_name': STEP_NAMES.get(step_id, step_id)
                }
        
        # 计算总体验证结果
        all_valid = all(result['valid'] for result in validation_results.values())
        
        return {
            'overall_valid': all_valid,
            'step_validations': validation_results
        } 