from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
from werkzeug.datastructures.file_storage import FileStorage


TENCENT_COS_DOMAIN = "https://oss.roleip.com"


class COSDB:
    def __init__(self, secret_id: str, secret_key: str, region: str, bucket_name: str):
        config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key, Token=None)
        self.client = CosS3Client(config)
        self.bucket_name = bucket_name
        self.region = region

    def upload_file(self, file_stream, cos_file_name: str, content_type=None):
        self.client.upload_file_from_buffer(
            Bucket=self.bucket_name,
            Key=cos_file_name,
            Body=file_stream,
            EnableMD5=False,  # 关闭MD5校验，加快上传速度
            ContentType=content_type
        )

        # 修改文件权限为公共读
        self.client.put_object_acl(
            Bucket=self.bucket_name,
            Key=cos_file_name,
            ACL='public-read'
        )

        # 返回文件的访问链接
        return f"{TENCENT_COS_DOMAIN}/{cos_file_name}"

    def delete_file(self, cos_file_name: str):
        response = self.client.delete_object(
            Bucket=self.bucket_name,
            Key=cos_file_name
        )

        return response

    def get_file_size(self, cos_file_name: str):
        response = self.client.head_object(
            Bucket=self.bucket_name,
            Key=cos_file_name
        )

        if response:
            return response['Content-Length']
        else:
            return 0
