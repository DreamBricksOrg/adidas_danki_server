import boto3
import os
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

# Carregar variáveis de ambiente explicitamente
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")

# Criar cliente boto3 com credenciais explícitas
s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_DEFAULT_REGION
)

def upload_file_to_s3(file_path, bucket_name, s3_key):
    """Faz upload de um arquivo local para o S3."""
    try:
        s3.upload_file(file_path, bucket_name, s3_key)
        print(f"Arquivo '{file_path}' enviado para '{bucket_name}/{s3_key}'.")
        return True
    except ClientError as e:
        print(f"Erro ao enviar arquivo: {e}")
        return False

def upload_file_blob_to_s3(file, bucket_name, s3_key):
    """Faz upload de um arquivo para o S3 diretamente do Flask."""
    try:
        s3.upload_fileobj(file, bucket_name, s3_key)
        return f"https://{bucket_name}.s3.amazonaws.com/{s3_key}"
    except ClientError as e:
        print(f"Erro ao enviar arquivo: {e}")
        return None

def download_file_from_s3(bucket_name, s3_key, local_path):
    """Faz download de um arquivo do S3 para o disco local."""
    try:
        s3.download_file(bucket_name, s3_key, local_path)
        print(f"Arquivo '{s3_key}' baixado para '{local_path}'.")
        return True
    except ClientError as e:
        print(f"Erro ao baixar arquivo: {e}")
        return False

def list_files_in_bucket(bucket_name, prefix=""):
    try:
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        contents = response.get("Contents", [])
        return [item["Key"] for item in contents]
    except ClientError as e:
        print(f"Erro ao listar arquivos: {e}")
        return []

def delete_file_from_s3(bucket_name, s3_key):
    """Remove um arquivo do bucket S3."""
    try:
        s3.delete_object(Bucket=bucket_name, Key=s3_key)
        print(f"Arquivo '{s3_key}' removido do bucket '{bucket_name}'.")
        return True
    except ClientError as e:
        print(f"Erro ao deletar arquivo: {e}")
        return False

def get_file_url(bucket_name, s3_key, expires_in=3600):
    """Gera uma URL temporária para acessar um arquivo do S3."""
    try:
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': s3_key},
            ExpiresIn=expires_in
        )
        return url
    except ClientError as e:
        print(f"Erro ao gerar URL: {e}")
        return None
