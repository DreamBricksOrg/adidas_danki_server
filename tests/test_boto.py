import os
import unittest
from utils import boto
from dotenv import load_dotenv

load_dotenv()

TEST_BUCKET = os.getenv("TEST_S3_BUCKET")
TEST_FILE_LOCAL = "test_file.txt"
TEST_FILE_S3 = "tests/test_file.txt"

class TestBotoUtil(unittest.TestCase):

    def setUp(self):
        # Criar um arquivo temporário local para upload
        with open(TEST_FILE_LOCAL, "w") as f:
            f.write("Arquivo de teste para boto_util.")

    def tearDown(self):
        # Remover o arquivo local
        if os.path.exists(TEST_FILE_LOCAL):
            os.remove(TEST_FILE_LOCAL)

    def test_upload_and_download(self):
        # Upload
        result = boto.upload_file_to_s3(TEST_FILE_LOCAL, TEST_BUCKET, TEST_FILE_S3)
        self.assertTrue(result)

        # Listar arquivos
        files = boto.list_files_in_bucket(TEST_BUCKET, prefix="tests/")
        self.assertIn(TEST_FILE_S3, files)

        # Gerar URL
        url = boto.get_file_url(TEST_BUCKET, TEST_FILE_S3)
        self.assertTrue(url.startswith("http"))

        # Download
        result = boto.download_file_from_s3(TEST_BUCKET, TEST_FILE_S3, "downloaded_test_file.txt")
        self.assertTrue(result)
        self.assertTrue(os.path.exists("downloaded_test_file.txt"))

        # Cleanup
        os.remove("downloaded_test_file.txt")

    def test_delete(self):
        # Upload para garantir que o arquivo exista
        boto.upload_file_to_s3(TEST_FILE_LOCAL, TEST_BUCKET, TEST_FILE_S3)

        # Deletar do S3
        result = boto.delete_file_from_s3(TEST_BUCKET, TEST_FILE_S3)
        self.assertTrue(result)

        # Confirmar remoção
        files = boto.list_files_in_bucket(TEST_BUCKET, prefix="test-folder/")
        self.assertNotIn(TEST_FILE_S3, files)

if __name__ == "__main__":
    unittest.main()
