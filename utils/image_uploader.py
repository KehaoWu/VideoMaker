import base64
import os
from urllib.parse import quote

class ImageUploader:
    def __init__(self):
        pass
    
    def image_to_data_url(self, image_path):
        """
        将本地图片转换为data URL格式
        :param image_path: 图片路径
        :return: data URL字符串
        """
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        # 获取文件扩展名
        _, ext = os.path.splitext(image_path)
        ext = ext.lower().lstrip('.')
        
        # 确定MIME类型
        mime_type = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp'
        }.get(ext, 'image/jpeg')
        
        # 转换为base64
        base64_data = base64.b64encode(image_data).decode('utf-8')
        
        return f"data:{mime_type};base64,{base64_data}"
    
    def save_as_data_url_file(self, image_path, output_path=None):
        """
        将图片保存为包含data URL的文本文件
        :param image_path: 原图片路径
        :param output_path: 输出文件路径
        :return: 输出文件路径
        """
        if not output_path:
            base_name = os.path.splitext(os.path.basename(image_path))[0]
            output_path = f"assets/data_urls/{base_name}_data_url.txt"
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        data_url = self.image_to_data_url(image_path)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(data_url)
        
        return output_path
    
    def get_image_url_for_api(self, image_path):
        """
        获取适用于API调用的图片URL
        由于文生视频API需要可访问的URL，这里返回data URL
        在实际部署中，建议上传到云存储服务
        :param image_path: 图片路径
        :return: 图片URL
        """
        # 对于演示目的，返回data URL
        # 在生产环境中，应该上传到云存储并返回公网URL
        return self.image_to_data_url(image_path)
    
    def upload_to_temp_service(self, image_path):
        """
        上传到临时图片服务（示例实现）
        实际使用时需要替换为真实的图片上传服务
        :param image_path: 图片路径
        :return: 公网可访问的URL
        """
        # 这里是示例实现，实际需要对接真实的图片上传服务
        # 比如阿里云OSS、腾讯云COS、七牛云等
        
        print(f"注意: 当前使用data URL格式，建议在生产环境中上传到云存储服务")
        return self.image_to_data_url(image_path) 