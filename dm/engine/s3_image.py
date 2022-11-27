import boto3
import requests
import time
from dm.log import logger

s3_resource = boto3.resource('s3',
                     aws_access_key_id='AKIAZT66GHX7XM2MFLXV',
                     aws_secret_access_key='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')

bucket_name = 'instagram-profile-bucket'



def upload_profile(profile_url,profile_key_name):
    try_num = 0
    max_try_num = 10
    while True:
        if try_num >= max_try_num:
            logger.error("s3 - upload_profile 연결 에러")
            raise ConnectionError

        profile_file_name = f"profile/{profile_key_name}"
        profile_req_for_image = requests.get(profile_url, stream=True)
        profile_file_object_from_req = profile_req_for_image.raw
        profile_req_data = profile_file_object_from_req.read()

        try:
            s3_resource.Bucket(bucket_name).put_object(Key=profile_file_name,
                                                      Body=profile_req_data, ACL='public-read',
                                                      ContentType="image/jpg")
        except Exception as e:
            logger.warning(f"s3 - upload_profile 연결:{e}")
            try_num += 1
            time.sleep(5)
            continue

        return f'https://instagram-profile-bucket.s3.ap-northeast-2.amazonaws.com/{profile_file_name}'

